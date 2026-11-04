#!/usr/bin/env python3
"""Independently replay current stock-BBS cancellation/retry capture gates."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from product_inputs import ROOT,sha
from audit_zmodem import scan,packet,metadata,audit_batch,audit_controls
from test_transfer_dos import timestamp,offset_after
from audit_size_probe_screen import telnet
from paced_bios_keys import source as keyboard_source
from zmodem_cancel_disk_watch import SAMPLER


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    cap,bridge,out=[p.resolve() for p in (a.capture,a.bridge,a.output)]
    assert all(p.is_relative_to(ROOT/'build') for p in (cap,bridge,out));out.mkdir(parents=True,exist_ok=False)
    r=json.loads((cap/'cancel-checks.json').read_text());assert r['passed'] and not r['errors'] and all(r['checks'].values())
    for n,h in r['sources'].items():assert sha(ROOT/n)==h,n
    harness=json.loads((cap/'result.json').read_text());assert harness['passed'] and all(harness['checks'].values())
    assert harness['cpu']=='8086' and harness['serial']['com']==3 and harness['serial']['irq']==5 and harness['serial']['flow']=='HARD'
    assert sha(cap/'program/TERMINAL.EXE')==r['terminal_sha256']
    assert (cap/'PASS.TXT').exists() and not (cap/'FAIL.TXT').exists()
    before=(cap/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(cap/'AFTER.BIN').read_bytes()
    assert len((cap/'SCREEN.BIN').read_bytes())==8000 and not list(cap.rglob('PCRX.$$$'))
    recipe=json.loads((cap/'recipe.json').read_text())['recipe']
    assert (cap/'KEYS.ASM').read_text()==keyboard_source(recipe)
    subprocess.run(['nasm','-fbin',str(cap/'KEYS.ASM'),'-o',str(out/'PACED.COM')],check=True)
    assert sha(out/'PACED.COM')==sha(cap/'PACED.COM')==sha(cap/'KEYS.COM')
    sampler=SAMPLER.replace('mov cx,4000','mov cx,8000')
    for off in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+off),hex(0x3e8+off))
    assert sampler==(cap/'sampler.asm').read_text()
    subprocess.run(['nasm','-fbin',str(cap/'sampler.asm'),'-o',str(out/'SNAP.COM')],check=True)
    assert sha(out/'SNAP.COM')==sha(cap/'SNAP.COM')
    labels=(cap/'LABELS.BIN').read_bytes()
    assert len(labels)==2566 and struct.unpack_from('<H',labels)[0]==0x4e5a and struct.unpack_from('<H',labels,4)[0]&0x8000
    raw=(cap/'TEST.PRM').read_bytes()
    assert [struct.unpack_from('<H',raw,n)[0] for n in (0x42c,0x1c2,0x1c8,0x1ca,0x4ec)]==[1,0,2,25,0]
    geometry=struct.unpack('<4H',(cap/'GEOM.BIN').read_bytes());assert (geometry[0],geometry[1],geometry[2],geometry[3]>>8)==(25,16,0x5003,0)
    name=r['payload_name'];payload=(cap/'RECV'/name).read_bytes()
    assert len(payload)==r['payload_bytes']==65539 and set(payload)==set(range(256))
    assert hashlib.sha256(payload).hexdigest()==r['payload_sha256'] and payload.count(b'\x1b[8;50;80t')==215
    assert {p.name for p in (cap/'RECV').iterdir()}=={name}
    snapshots=json.loads((cap/'cancel-snapshots.json').read_text());assert snapshots==r['snapshots']
    partial=[s for s in snapshots if s['kind']=='partial'];clean=[s for s in snapshots if s['kind']=='after-cancel-before-retry']
    assert len(partial)==len(clean)==1 and snapshots.index(partial[0])<snapshots.index(clean[0])
    part=partial[0];assert part['before_cancel'] and part['source_prefix'] and 0<part['length']<len(payload)
    assert part['sha256']==hashlib.sha256(payload[:part['length']]).hexdigest() and clean[0]['files']=={}
    stream=(cap/'display.bin').read_bytes();keys=(cap/'serial-received.bin').read_bytes();trace=json.loads((cap/'trace.json').read_text())
    online=(cap/'bbs-sent.bin').read_bytes()
    assert stream==(bridge/'1-serial-output.bin').read_bytes() and online==(bridge/'1-serial-input.bin').read_bytes()
    before_commands=b'ATZ\r'+f"ATDlab.local:{r['proxy']['endpoint']['port']}\r".encode()
    assert keys==before_commands+online+b'+++ATH\r'
    cancel=keys.index(b'\x18'*8+b'\x08'*10);cancel_time=timestamp(trace,'dos',cancel)
    first=[h for h in scan(stream) if h['type']==4 and timestamp(trace,'bbs',h['offset'])<cancel_time];assert len(first)==1
    offer=packet(stream,first[0]['end'],first[0]['format']);assert metadata(offer['payload'])==(name,len(payload))
    data=[h for h in scan(stream) if h['type']==10 and first[0]['offset']<h['offset'] and timestamp(trace,'bbs',h['offset'])<cancel_time];assert data
    body=packet(stream,data[0]['end'],data[0]['format'])['payload'];assert body and body==payload[:len(body)]
    assert not any(h['type']==11 and first[0]['offset']<h['offset'] and timestamp(trace,'bbs',h['offset'])<cancel_time for h in scan(stream))
    query=keys.index(b'\x1b\x1bS\r',cancel+18)+2;query_time=timestamp(trace,'dos',query)
    retry_command=keys.index(b'D\r',query+2);retry_time=timestamp(trace,'dos',retry_command)
    assert part['seconds']<cancel_time<clean[0]['seconds']<retry_time
    start=offset_after(trace,'bbs',retry_time);assert start is not None
    retry=audit_batch(stream,{name:payload},start)
    query_start=offset_after(trace,'bbs',query_time);assert query_start is not None
    # Require target response BEFORE the retry command, not just a helper's
    # filename banner or ZFILE after it.
    assert (name+' ').encode() in stream[query_start:start]
    end_time=timestamp(trace,'bbs',retry['end']-1);cut=offset_after(trace,'dos',end_time);assert cut is not None
    final=keys.index(b'\x1b\x1bS\r',cut)+2;final_time=timestamp(trace,'dos',final)
    controls=audit_controls(retry,keys,trace,'bbs',final_time,False)
    tail=offset_after(trace,'bbs',final_time);assert tail is not None and (name+' ').encode() in stream[tail:]
    assert retry['finish'] and controls==r['protocol']['retry']['controls'] and cancel==r['protocol']['cancel_offset']
    client,subs,_=telnet((bridge/'1-telnet-input.bin').read_bytes());server,_,_=telnet((bridge/'1-telnet-output.bin').read_bytes())
    prefix=b'loc\r\x1b[8;24;80t';assert online.startswith(prefix) and client==online[len(prefix):] and stream.endswith(server)
    assert [list(struct.unpack('>HH',s[1:])) for s in subs if s[0]==31]==[[80,24]]
    model=json.loads((cap/'modem.json').read_text())
    assert len([e for e in model['events'] if e['kind']=='bbs-connected'])==1
    assert len([e for e in model['events'] if e['kind']=='guarded-hangup'])==1
    assert len(list(bridge.glob('*-closed.json')))==1
    rows=[json.loads(line) for line in (cap/'server-session.jsonl').read_text().splitlines()]
    sessions={r['sessionId'] for r in rows};assert len(sessions)==1
    assert sum(r.get('msg')=='User "loclab" successfully logged in' for r in rows)==1
    executions=[i for i,r in enumerate(rows) if r.get('msg')=='Executing external protocol']
    exits=[(i,r.get('exitCode')) for i,r in enumerate(rows) if r.get('msg')=='Process exited']
    assert len(executions)==len(exits)==2 and executions[0]<exits[0][0]<executions[1]<exits[1][0]
    assert exits[0][1]!=0 and exits[1][1]==0 and [v for _,v in exits]==r['server_exit_codes']
    for lo,hi in [(exits[0][0],executions[1]),(exits[1][0],len(rows))]:
        menus=[r.get('menuName') for r in rows[lo:hi] if r.get('msg')=='Goto menu module']
        assert 'fileBaseSearch' in menus and 'fileBaseListEntries' in menus
    captures=list(cap.glob('*.BIN'))+[cap/n for n in ['cancel-checks.json','result.json','recipe.json','KEYS.ASM','PACED.COM','KEYS.COM','sampler.asm','SNAP.COM','trace.json','cancel-snapshots.json','server-session.jsonl','server-log-start.json','modem.json','bbs-sent.bin','display.bin','serial-received.bin','PASS.TXT','program/TERMINAL.EXE','RECV/'+name]]
    captures+=list(bridge.glob('*.bin'))+list(bridge.glob('*.json'))
    result=dict(passed=True,terminal_sha256=r['terminal_sha256'],payload_bytes=len(payload),payload_sha256=r['payload_sha256'],
        partial_disk_bytes=part['length'],first_CRC_packet_bytes=len(body),server_exit_codes=r['server_exit_codes'],
        same_DOS_process=True,authenticated_sessions=1,proxy_connections=1,NAWS=[[80,24]],
        exact_retry=True,source_only_keyboard_rebuild=True,captures={str(p.relative_to(ROOT)):sha(p) for p in captures},
        sources={n:sha(ROOT/n) for n in ['lab/bbs/audit_proxy_cancel_retry.py','lab/bbs/audit_zmodem.py',
            'lab/bbs/test_transfer_dos.py','lab/bbs/audit_size_probe_screen.py','lab/bbs/paced_bios_keys.py',
            'lab/bbs/zmodem_cancel_disk_watch.py','lab/bbs/zmodem_cancel_watch.py','lab/bbs/zmodem_label_watch.py',
            'standalone/test_terminal.py']},
        scope=__doc__+' Actual BIOS Escape after visible8KiB,nonempty source-prefix disk stage then empty receive directory before retry,target search before retry command and after completed retry,raw proxy equality,standard CRC/control/finish,exact binary destination. Synthetic nullmodem CTS-ready; no physical/SIP/DSP/carrier-loss or all-layout/protocol acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS independent proxy cancellation/retry:',len(payload),'exact bytes; partial',part['length'])


if __name__=='__main__':main()
