#!/usr/bin/env python3
"""Seal the failed second-script invocation without accepting audio reconnect."""
import argparse,hashlib,json,re,struct
from pathlib import Path
from audio_synchronet import ROOT,sha,snapshot
from audio_synchronet_download import source
from audio_carrier_adapter import PREFIX
from synthmodem_gateway import records
from test_transfer_dos import packet_at
from modem import Telnet

def guest_data(path):
    raw=path.read_bytes();at=0;data=bytearray()
    while at<len(raw):
        size,kind=struct.unpack_from('<HB',raw,at);assert 1<=size<=4094 and at+size+2<=len(raw)
        if kind==0x15:data.extend(raw[at+3:at+size+2])
        at+=size+2
    return bytes(data)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path)
    p.add_argument('--keys',type=Path,required=True);p.add_argument('--adapter',type=Path,required=True)
    p.add_argument('--relay',type=Path,required=True);p.add_argument('--queue-probe',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.cohort.resolve();target=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
    r=json.loads((out/'result.json').read_text());assert not r['passed']
    failed=[k for k,v in r['checks'].items() if not v]
    assert set(failed)=={'complete_retry_observed','exact_retry','only_expected_receive','two_BBS_connections'}
    assert r['checks']['normal_DOS_exit'] and r['checks']['hardware_restored'] and r['checks']['timer_restored']
    assert r['checks']['carrier_loss_observed'] and r['checks']['directory_two_calls'] and r['checks']['partial_removed_before_second_call']
    screen=(out/'SCREEN.BIN').read_bytes();text='\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25))
    error='ASPECT: unsupported command or service (error 3, opcode D4, step 2)'
    assert error in text and '57600.ASX' in text
    expected=source().read_bytes();partial=(out/'interrupted-partial.bin').read_bytes()
    assert len(partial)==8192 and expected.startswith(partial) and sha(source())==r['source_sha256']
    assert hashlib.sha256(partial).hexdigest()==r['partials'][0]['sha256']
    first=out/'call-1';second=out/'call-2';up=(first/'adapter-up.bin').read_bytes()
    address=up.split(b'\r',1)[0]+b'\r';sent,_=Telnet().feed((out/'bbs-1/input.bin').read_bytes())
    guest=guest_data(first/'control-wire.bin')
    assert up==guest+b'\x06' and up==address+sent+b'\x06'
    offline=json.loads((first/'offline-caller.json').read_text())
    assert bytes.fromhex(''.join(v['hex'] for v in offline['received']))==up
    decoded=(first/'adapter-down.bin').read_bytes()
    at=next(i for i in range(len(decoded)) if (f:=packet_at(decoded,i,True)) and f['number']==1 and f['payload']==expected[:f['size']])
    seq=1;verified=bytearray()
    while (f:=packet_at(decoded,at,True)) is not None:
        assert f['number']==seq;seq+=1;verified.extend(f['payload']);at=f['end']
    assert seq==11 and len(verified)==10240 and expected.startswith(verified) and at==len(decoded)
    io_results=[]
    for folder in (first,second):
        node=json.loads((folder/'node-result.json').read_text());io=json.loads((folder/'serial-io-audit.json').read_text());adapter=json.loads((folder/'adapter.json').read_text())
        assert io['evidence_consistent'] and all(io['checks'].values()) and not io['error_events']
        assert io['auditor_sha256']==sha(ROOT/'lab/bbs/audit_audio_reconnect_io.py')
        for n,h in io['capture_sha256'].items():assert sha(folder/n)==h,n
        assert not node['errors'] and node['VM_exited'] and node['pool']=='stopped'
        assert node['callerInfo']['bps']==node['answerInfo']['bps']==1200
        assert adapter['done'] and not adapter['errors'] and adapter['frontend_exit']==0
        offline=json.loads((folder/'offline-caller.json').read_text())
        assert offline['checker_sha256']==sha(ROOT/'lab/bbs/diagnose_audio_caller.js')
        assert offline['capture_sha256']==sha(folder/'rtp-from-caller.bin')
        decoder=next(h for n,h in r['runtime_inputs'].items() if n.endswith('/src/dsp/protocols/V22Demodulator.js'))
        assert offline['decoder_sha256']==decoder
        assert bytes.fromhex(''.join(v['hex'] for v in offline['received']))==(folder/'adapter-up.bin').read_bytes()
        assert (folder/'serial-out.bin').read_bytes()==PREFIX+(folder/'caller-decoded.bin').read_bytes()
        requests=records((folder/'sip-to-server.bin').read_bytes());responses=records((folder/'sip-to-caller.bin').read_bytes())
        assert any(b.startswith(b'INVITE ') for b in requests) and any(b.startswith(b'ACK ') for b in requests)
        assert any(b.startswith(b'BYE ') for b in responses) and any(b.startswith(b'SIP/2.0 200') and b' BYE\r\n' in b for b in requests)
        io_results.append(io['checks'])
    assert (second/'adapter-up.bin').read_bytes()==guest_data(second/'control-wire.bin')==b''
    assert (second/'adapter-down.bin').read_bytes()==b'PCPLUS DSP LAB V22 1200\r\nCONNECT> '
    assert not list((out/'RECV').iterdir()) and not (out/'bbs-2').exists()
    assert len(re.findall(rb'LABUSER\s+Logon ',(out/'server-session.log').read_bytes()))==1
    for n,h in r['frozen_inputs'].items():assert sha(ROOT/n)==h,n
    for n,h in r['runtime_inputs'].items():assert sha(Path(n))==h,n
    assert snapshot()==r['server']
    prerequisites={}
    for name,path in [('keys',a.keys),('adapter',a.adapter),('relay',a.relay),('queue_probe',a.queue_probe)]:
        path=path.resolve();assert path.is_relative_to(ROOT/'build');d=json.loads(path.read_text())
        assert d.get('passed',d.get('source_queue_probe_passed'))
        for n,h in d['inputs'].items():assert sha(ROOT/n)==h,n
        prerequisites[name]=dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
    result=dict(passed=False,actual_audio_reconnect_accepted=False,cohort=str(out.relative_to(ROOT)),
        terminal_sha256=r['frozen_inputs']['build/terminal/TERMINAL.EXE'],producer_checks=r['checks'],failed_checks=failed,
        runtime_error=error,observed_status_label='57600.ASX',root_cause_identified=False,
        partial_bytes=8192,CRC_verified_prefix_bytes=10240,first_DOS_online_bytes=len(up),first_guest_online_bytes=len(guest),
        first_tail_not_delivered_to_guest_or_BBS_hex='06',first_offline_caller_equals_DOS=True,
        second_real_DSP_training=True,second_bridge_prompt_exact=True,second_online_input_bytes=0,
        serial_ownership_checks=io_results,prerequisites=prerequisites,
        independent_inputs={n:sha(ROOT/n) for n in ('lab/bbs/audit_audio_reconnect_io.py','lab/bbs/test_transfer_dos.py','lab/bbs/modem.py','lab/bbs/synthmodem_gateway.py','lab/bbs/diagnose_audio_caller.js')},
        inputs=r['frozen_inputs'],runtime_inputs=r['runtime_inputs'],recorder_sha256=sha(Path(__file__)),
        capture_sha256={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
        scope='Failed actual source-built DOS two-call SIP/audio bridge-restart campaign. First verified partial triggers real frontend/SIP shutdown, emulated DCD loss, partial removal and redial. Second DSP call trains and delivers CONNECT>, but ASPECT reports unsupported D4 at step2 and sends no BBS address. First transfer has ten exact CRC blocks; the final DOS ACK exists in offline caller audio but does not reach the guest/BBS before shutdown. Preserve that tail loss rather than claim full first-stream identity. Independent exit watchdog restores DOS/UART/timer state; no retry file or second BBS login. No fix, physical compatibility, waveform-loss detection or whole-application completion claim.')
    with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=False,failed_checks=failed,runtime_error=error,receipt=str(target))))

if __name__=='__main__':main()
