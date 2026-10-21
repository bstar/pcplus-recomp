#!/usr/bin/env python3
"""Correlate owned DOS socket syscalls, serial input and observed BBS output."""
import argparse
import ast
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from modem import Telnet


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def syscalls(file, port):
    pending={}; rows=[]
    for line in file.read_text().splitlines():
        m=re.match(r'^(\d+)\s+(\d+\.\d+)\s+(.*)$',line)
        if not m: continue
        pid,stamp,body=m.groups(); ns=int(Decimal(stamp)*10**9)
        resumed=re.match(r'<\.\.\. (\w+) resumed>(.*)',body)
        if resumed:
            name,tail=resumed.groups(); first=pending.pop((pid,name),None)
            if first is None: continue
            body=first+tail
        elif '<unfinished ...>' in body:
            name=body.split('(',1)[0]; pending[pid,name]=body.split('<unfinished ...>',1)[0]; continue
        rows.append({'wall_ns':ns,'body':body})
    target=re.compile(r'TCP:\[[^\]]+->127\.0\.0\.1:'+str(port)+r'\]')
    selected=[r for r in rows if target.search(r['body'])]
    received=bytearray(); count=0; complete=True; receive_calls=[]
    for row in selected:
        body=row['body']
        if not body.startswith('recvfrom('): continue
        result=re.search(r'\)\s+=\s+(\d+)',body)
        if not result: continue
        size=int(result.group(1)); count+=size
        quoted=re.search(r'recvfrom\(\d+<TCP:\[[^\]]+\]>,\s*("(?:\\.|[^"\\])*")',body)
        data=ast.literal_eval(quoted.group(1)).encode('latin1') if quoted else b''
        complete &= len(data)==size and 'MSG_PEEK' not in body
        received.extend(data); receive_calls.append({'wall_ns':row['wall_ns'],'bytes':size})
    return {'received_bytes':count,'reconstructed_hex':bytes(received).hex() if complete else None,
            'payload_reconstruction_complete':complete,'receive_calls':receive_calls,
            'close_calls':[r for r in selected if r['body'].startswith('close(')],
            'linger_calls':[r for r in rows if 'setsockopt(' in r['body'] and 'SO_LINGER' in r['body']]}


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('cohort',type=Path)
    out=p.parse_args().cohort.resolve(); read=lambda n:json.loads((out/n).read_text())
    r=read('result.json'); n=read('node-result.json'); assert r['syscall_trace']
    port=read('serial-port.json')['port']; trace=syscalls(out/'DOS-syscalls.log',port)
    serial=(out/'serial-in.bin').read_bytes(); submitted=(out/'serial-submitted.bin').read_bytes()
    inputs=[json.loads(v) for v in (out/'serial-input-events.jsonl').read_text().splitlines()]
    relay=[json.loads(v) for v in (out/'BBS-relay-events.jsonl').read_text().splitlines()]
    closes=[e for e in n['events'] if e['type']=='serial-close']; assert len(closes)==1
    close_ns=int(closes[0]['monotonicNs']); checks={}; at=0
    for v in inputs: assert v['offset']==at; at+=v['length']
    checks['complete_serial_input_timeline']=at==len(serial)
    app_by_direction={}; app_events=[]
    for direction,leaf in [('to_bbs','bbs-input.bin'),('from_bbs','bbs-output.bin')]:
        raw=(out/leaf).read_bytes(); decoder=Telnet(); at=0; app=bytearray()
        for event in [v for v in relay if v['direction']==direction]:
            assert event['offset']==at; end=at+event['count']; block,_=decoder.feed(raw[at:end]); at=end
            if direction=='from_bbs' and block:
                app_events.append({'start':len(app),'end':len(app)+len(block),'monotonic_ns':int(event['monotonic_ns'])})
            app.extend(block)
        checks['complete_'+direction+'_timeline']=at==len(raw)
        expected,_=Telnet().feed(raw); checks['streamed_'+direction+'_decode_identity']=bytes(app)==expected
        app_by_direction[direction]=bytes(app)
    checks['producer_capture_hashes']=all(sha(out/name)==h for name,h in r['captures_sha256'].items())
    checks['tool_identities']=all(sha(Path(name))==h for name,h in r['tool_inputs'].items())
    checks['one_traced_socket_close']=len(trace['close_calls'])==1
    checks['complete_socket_payload_reconstruction']=trace['payload_reconstruction_complete']
    actual_recv=bytes.fromhex(trace['reconstructed_hex']) if trace['reconstructed_hex'] is not None else b''
    checks['DOS_socket_received_exact_submitted_prefix']=submitted.startswith(actual_recv) and bool(actual_recv)
    final=next(v for v in inputs if v['offset']<=len(serial)-1<v['offset']+v['length'])
    final_ns=int(final['monotonicNs']); last_byte=serial[-1]
    target=serial[9:].split(b'\r',1)[0]
    bridge=(b'PCPLUS DSP LAB V22 1200\r\nCONNECT> Connecting to '+target+b'...\r\r\nConnected to '+target+
            b'.\r\r\nIn-band menu escape disabled; remote close returns to menu. QUIT there hangs up.\r\r\n\r\r\n')
    expected=bridge+app_by_direction['from_bbs']; caller=(out/'caller-decoded.bin').read_bytes()
    exact_prefix=expected.startswith(caller); missing=[]
    if exact_prefix:
        app_start=max(0,len(caller)-len(bridge))
        for event in app_events:
            overlap=max(0,event['end']-max(event['start'],app_start))
            if overlap: missing.append({'bytes':overlap,'observed_after_final_input_ms':(event['monotonic_ns']-final_ns)/1e6,
                                        'observed_before_close_ms':(close_ns-event['monotonic_ns'])/1e6})
    anchor=r['clock_anchors'][-1]; mono_mid=(int(anchor['monotonic_before_ns'])+int(anchor['monotonic_after_ns']))//2
    wall_offset=int(anchor['wall_ns'])-mono_mid
    result={'evidence_consistent':all(checks.values()),'checks':checks,
            'serial_input_bytes':len(serial),'final_input_byte_hex':bytes([last_byte]).hex(),
            'final_input_before_close_ms':(close_ns-final_ns)/1e6,
            'actual_socket_received_bytes':trace['received_bytes'],'submitted_bytes':len(submitted),
            'submitted_but_not_socket_received_bytes':len(submitted)-trace['received_bytes'],
            'caller_is_exact_bridge_and_BBS_prefix':exact_prefix,
            'missing_caller_suffix_bytes':len(expected)-len(caller) if exact_prefix else None,
            'missing_suffix_observation_events':missing,
            'missing_suffix_observed_after_final_input':bool(missing) and all(v['observed_after_final_input_ms']>=0 for v in missing),
            'traced_close_to_frontend_close_ms':[(close_ns-(v['wall_ns']-wall_offset))/1e6 for v in trace['close_calls']],
            'clock_anchor_window_ns':int(anchor['monotonic_after_ns'])-int(anchor['monotonic_before_ns']),
            'traced_close_calls':trace['close_calls'],'SO_LINGER_calls':trace['linger_calls'],
            'capture_sha256':{name:sha(out/name) for name in ['result.json','node-result.json','serial-port.json','DOS-syscalls.log',
                 'serial-input-events.jsonl','BBS-relay-events.jsonl','clock-anchors.json','serial-in.bin','serial-submitted.bin',
                 'caller-decoded.bin','bbs-input.bin','bbs-output.bin']},'auditor_sha256':sha(Path(__file__)),
            'scope':'Read-only syscall byte reconstruction and actual observed relay/input/close timing. Linux monotonic clocks align Node hrtime with Python monotonic; final bracketed realtime anchor maps strace timestamps near close. BBS times are relay observations, not internal server-generation timestamps. Socket reads do not prove UART/application consumption; no error or complete-downstream gate is waived.'}
    (out/'close-timing-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2)); assert result['evidence_consistent']


if __name__=='__main__': main()
