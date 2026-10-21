#!/usr/bin/env python3
"""Independently audit interrupted audio call and a fresh DOS download retry."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from audio_synchronet import ROOT,sha,snapshot,message_bodies
from audio_synchronet_download import source
from audio_carrier_adapter import PREFIX
from synthmodem_gateway import records
from modem import Telnet
from synchronet import Peer
from audit_audio_download import frontend_trace
from test_transfer_dos import audit_protocol,audit_controls,timestamp,packet_at

def verify_streams(call,bbs,*,complete,decoder_sha):
    node=json.loads((call/'node-result.json').read_text())
    adapter=json.loads((call/'adapter.json').read_text())
    inbound=(call/'serial-in.bin').read_bytes();caller=(call/'caller-decoded.bin').read_bytes()
    assert inbound.startswith(b'ATZ\rATD1\r') and node['commands']==['ATZ','ATD1']
    online=inbound[9:];assert (call/'adapter-up.bin').read_bytes()==online
    assert (call/'serial-out.bin').read_bytes()==PREFIX+caller
    assert (call/'adapter-down.bin').read_bytes()==caller
    sent,_=Telnet().feed((bbs/'input.bin').read_bytes());display,_=Telnet().feed((bbs/'output.bin').read_bytes())
    address=online.split(b'\r',1)[0];assert re.fullmatch(rb'127\.0\.0\.1:\d+',address)
    assert online==address+b'\r'+sent
    bridge=(b'PCPLUS DSP LAB V22 1200\r\nCONNECT> Connecting to '+address+b'...\r\r\nConnected to '+address+
        b'.\r\r\nIn-band menu escape disabled; remote close returns to menu. QUIT there hangs up.\r\r\n\r\r\n')
    assert caller.startswith(bridge)
    if complete:assert caller==bridge+display
    else:assert display.startswith(caller[len(bridge):])
    wire=(call/'control-wire.bin').read_bytes();guest=bytearray();statuses=[];at=0
    while at<len(wire):
        size,kind=struct.unpack_from('<HB',wire,at);assert 1<=size<=4094 and at+size+2<=len(wire)
        body=wire[at+3:at+size+2];at+=size+2
        if kind==0x15:guest.extend(body)
        if kind==0x13:statuses.append(json.loads(body))
    holds=re.findall(r'Post-train hold complete .*waited (\d+)ms, dropped (\d+) bytes\)',(call/'node.log').read_text())
    assert len(holds)==1 and 6000<=int(holds[0][0])<=15500 and holds[0][1]=='0'
    assert online==guest
    offline=json.loads((call/'offline-caller.json').read_text())
    assert offline['checker_sha256']==sha(ROOT/'lab/bbs/diagnose_audio_caller.js')
    assert offline['capture_sha256']==sha(call/'rtp-from-caller.bin')
    assert offline['decoder_sha256']==decoder_sha
    assert bytes.fromhex(''.join(v['hex'] for v in offline['received']))==online
    assert node['callerInfo']['bps']==node['answerInfo']['bps']==1200
    assert sum(s.get('event')=='connect' and s.get('rate')==1200 for s in statuses)==1
    assert not node['errors'] and node['VM_exited'] and node['pool']=='stopped'
    assert adapter['done'] and not adapter['errors'] and adapter['frontend_exit']==0
    io=json.loads((call/'serial-io-audit.json').read_text())
    assert io['evidence_consistent'] and all(io['checks'].values()) and not io['error_events']
    assert all(io['counters'][n]==0 for n in ('skippedBytes','pendingBytes','failedCallbackBytes'))
    assert io['auditor_sha256']==sha(ROOT/'lab/bbs/audit_audio_reconnect_io.py')
    for n,h in io['capture_sha256'].items():assert sha(call/n)==h,n
    for name in ('rtp-from-caller.bin','rtp-from-answer.bin'):
        headers=[]
        for b in records((call/name).read_bytes()):
            assert len(b)==172 and b[0]==0x80 and b[1]&127==0
            headers.append(struct.unpack_from('>HII',b,2))
        assert headers and all(seq==(headers[0][0]+i)%65536 and ts==(headers[0][1]+160*i)%2**32 and ssrc==headers[0][2] for i,(seq,ts,ssrc) in enumerate(headers))
    requests=records((call/'sip-to-server.bin').read_bytes());responses=records((call/'sip-to-caller.bin').read_bytes())
    assert any(b.startswith(b'INVITE ') for b in requests) and any(b.startswith(b'ACK ') for b in requests)
    assert any(b.startswith(b'BYE ') for b in responses) and any(b.startswith(b'SIP/2.0 200') and b' BYE\r\n' in b for b in requests)
    assert 'Response msg 200/BYE' in (call/'qemu-0.log').read_text()
    return sent,display,caller[len(bridge):],len(bridge),adapter,node

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
    assert out.is_relative_to(ROOT/'build') and not (out/'reconnect-audit.json').exists()
    r=json.loads((out/'result.json').read_text());assert r['passed'] and all(r['checks'].values())
    expected=source().read_bytes();assert sha(source())==r['source_sha256']
    decoder_sha=next(h for n,h in r['runtime_inputs'].items() if n.endswith('/src/dsp/protocols/V22Demodulator.js'))
    one=verify_streams(out/'call-1',out/'bbs-1',complete=False,decoder_sha=decoder_sha)
    two=verify_streams(out/'call-2',out/'bbs-2',complete=True,decoder_sha=decoder_sha)
    first_sent,first_display,first_decoded,_,adapter,node=one
    assert adapter['interrupted'] and not two[4]['interrupted']
    names=[e['event'] for e in adapter['events']]
    assert names.index('both-DSP-CONNECT')<names.index('owned-frontend-SIGTERM')<names.index('frontend-EOF')<names.index('DOSBox-TCP-closed')
    stop=next(int(e['monotonic_ns']) for e in adapter['events'] if e['event']=='owned-frontend-SIGTERM')
    down=next(e for e in node['events'] if e['type']=='shutdown')
    ended=next(e for e in node['events'] if e['type']=='session-ended')
    eof=next(int(e['monotonic_ns']) for e in adapter['events'] if e['event']=='frontend-EOF')
    assert stop<=int(down['monotonicNs'])<=int(ended['monotonicNs'])<=eof
    partial=(out/'interrupted-partial.bin').read_bytes()
    assert 1024<=len(partial)<len(expected) and expected.startswith(partial)
    assert hashlib.sha256(partial).hexdigest()==r['partials'][0]['sha256']
    assert int(r['partials'][0]['monotonic_ns'])<=stop and r['partials'][1]['files']==[]
    start=next(at for at in range(len(first_decoded)) if (f:=packet_at(first_decoded,at,True)) and f['number']==1 and f['payload']==expected[:f['size']])
    at=start;verified=bytearray();number=1
    while (frame:=packet_at(first_decoded,at,True)) is not None:
        assert frame['number']==number;verified.extend(frame['payload']);number+=1;at=frame['end']
    assert len(verified)>=len(partial) and expected.startswith(verified)
    assert at==len(first_decoded) or first_decoded[at] in (1,2),'Unexpected complete data after interrupted frames'
    assert len(first_decoded)-at<1029,'Complete invalid frame after interruption'
    assert b'\x1b[?1;2c' in first_sent and b'\x1b[?1;2c' in two[0]
    sent,display,_,bridge,_,_=two
    timing,provenance=frontend_trace(out/'call-2',sent,display,bridge)
    protocol=audit_protocol(display,expected)
    finish=timestamp(timing,'bbs',protocol['end']-1)
    post=next(row for row in timing if row['direction']=='dos' and row['seconds']>finish and b' ' in sent[row['offset']:row['offset']+row['size']])
    protocol['controls']=audit_controls(protocol,display,sent,timing,'bbs',post['seconds'],ack_timeout=30)
    assert [c['response'] for c in protocol['controls']]==[6]*14+[21,6]
    assert protocol.pop('padded_payload')==(out/'RECV/SYNC.BIN').read_bytes()==expected+b'\x1a'*127
    keys=re.sub(rb'\x1b\[(?:\?1;2c|\d+;\d+R)',b'',sent)
    initial=b'LABUSER\rLABPASS42\r Qn\r TJ11\rDPCXTEST.BIN\r1n'
    assert keys==initial+b'C'+b'\x06'*14+b'\x15\x06 Q'
    clean=Peer.cleaned(display);cursor=0
    for token in ['Login:','Password:','Read/Post Messages','List Files in dir','Which, Quit','PCPlus Lab:','Filespec','Protocol, Batch','Hang up after transfer?','[Hit a key]','List Files in dir','Read/Post Messages']:
        cursor=clean.index(token,cursor)+len(token)
    server_log=(out/'server-session.log').read_bytes()
    assert len(re.findall(rb'LABUSER\s+Logon ',server_log))==2
    assert len(re.findall(rb'D- downloaded PCXTEST\.BIN \(11521 bytes\) from Main PCPlus Lab',server_log))==1
    assert snapshot()==r['server']
    for n,h in r['frozen_inputs'].items():assert sha(ROOT/n)==h,n
    for n,h in r['runtime_inputs'].items():assert sha(Path(n))==h,n
    assert (out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes() and len((out/'BEFORE.BIN').read_bytes())==42
    assert (out/'KEYOLD.BIN').read_bytes()==(out/'KEYNEW.BIN').read_bytes() and len((out/'KEYOLD.BIN').read_bytes())==4
    captures={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}
    input_names=['lab/bbs/audit_synchronet_reconnect_audio.py','lab/bbs/audio_carrier_adapter.py',
        'lab/bbs/audio_synchronet.py','lab/bbs/audio_synchronet_download.py','lab/bbs/synchronet.py',
        'lab/bbs/modem.py','lab/bbs/synthmodem_gateway.py','lab/bbs/audit_audio_download.py',
        'lab/bbs/test_transfer_dos.py','lab/bbs/audit_audio_reconnect_io.py','lab/bbs/diagnose_audio_caller.js']
    result=dict(passed=True,producer_sha256=sha(out/'result.json'),protocol=protocol,interrupted_verified_bytes=len(verified),
        exact_online_bytes=[len((out/f'call-{i}/adapter-up.bin').read_bytes()) for i in (1,2)],
        decoded_BBS_bytes=[len(first_decoded),len(display)],timing=provenance,
        auditor_sha256=sha(Path(__file__)),inputs={n:sha(ROOT/n) for n in input_names},capture_sha256=captures,
        scope='Actual two-call SIP/audio/DOS bridge-process failure and fresh-call retry. Both calls have exact upstream/offline audio identity, separate real DSP/SIP/RTP/cleanup; first downstream is an explicitly interrupted verified prefix, second is the complete stream with strict CRC/ACK/EOT/menu finish. Actual frontend SIGTERM shutdown and session end precede EOF-induced emulated DCD loss. Fresh Linux frontend/VM per call; no long-lived bridge reuse, analog waveform-loss detection, physical modem/DCD/DTR or whole-application acceptance.')
    (out/'reconnect-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,interrupted_verified_bytes=len(verified),retry_blocks=protocol['accepted_blocks'])))

if __name__=='__main__':main()
