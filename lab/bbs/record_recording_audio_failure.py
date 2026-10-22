#!/usr/bin/env python3
"""Preserve the early local-menu injection counterexample, without acceptance."""
import argparse,json,struct
from modem import Telnet
from pathlib import Path
from synthmodem_vm_control import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--kind',choices=('early-menu','final-page'),default='early-menu')
    a=p.parse_args();out=a.cohort.resolve();target=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
    read=lambda name:json.loads((out/name).read_text())
    r=read('result.json');audit=read('independent-audit.json');io=read('serial-io-audit.json');offline=read('offline-caller.json')
    assert r['route']=='recording' and not r['passed']
    assert not audit['passed'] and audit['checks']['producer_inputs_unchanged']
    assert io['evidence_consistent'] and all(io['checks'].values())
    if a.kind=='early-menu':assert not io['error_events']
    else:assert io['error_events'] and all(event.get('code')=='ECONNRESET' for event in io['error_events'])
    assert r['checks']['VM_exited']
    for name,digest in r['frozen_inputs'].items():assert sha(out/'frozen-source'/name)==digest,name
    for name,digest in r['captures_sha256'].items():assert sha(out/name)==digest,name
    assert offline['checker_sha256']==r['frozen_inputs']['lab/bbs/diagnose_audio_caller.js']
    assert offline['capture_sha256']==sha(out/'rtp-from-caller.bin')
    serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(b'ATZ\rATD1\r')
    assert bytes.fromhex(''.join(row['hex'] for row in offline['received']))==serial[9:]
    stop=None;helper=None;text='';truncation=None
    if a.kind=='early-menu':
        assert not r['checks']['script_completed'] and r['checks']['no_gateway_errors']
        assert audit['checks']['complete_caller_stream_equals_bridge_plus_BBS_display']
        assert not (out/'program/PCPLUS.ASP').exists() and not (out/'program/PCPLUS.ASX').exists()
        stop=read('diagnostic-stop.json');assert stop['intentional'] and stop['signal']=='SIGABRT'
        assert read('exit-status.json')==dict(DOS=-6,node=0)
        helper=read('diagnostic-helper.json');assert helper['report'][:4]==[0x524b,1,1,0]
        screens=read('diagnostic-screens.json');assert len(screens)==1
        text=(out/Path(screens[0]['screen']).with_suffix('.txt')).read_text()
        assert 'File Base >> active filter:' in text and 'error 3, opcode D5' in text and 'ASPECT returned an error.' in text
        scope='Intentional diagnostic termination of a stalled owned DOSBox test. The BIOS helper opened Alt-Z while startup ASPECT still owned WAITQUIET/D5; VGA-referenced text shows typed error3 and helper phase1/one key. No recording or normal DOS/hardware/timer restoration acceptance. Extracted temporary cores were deleted; the original systemd core follows normal retention.'
    else:
        assert {name for name,value in r['checks'].items() if not value}=={'no_gateway_errors'}
        assert {name for name,value in audit['checks'].items() if not value}=={'complete_BBS_display_survives_DSP','complete_caller_stream_equals_bridge_plus_BBS_display'}
        assert read('exit-status.json')==dict(DOS=0,node=0)
        assert read('node-result.json')['errors']==['read ECONNRESET']
        words=struct.unpack('<8H',(out/'RECKEY.BIN').read_bytes());assert words[:4]==(0x524b,14,26,1)
        helper=dict(report=words)
        display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
        bridge=audit['payloads']['expected_bridge_bytes'];received=(out/'caller-decoded.bin').read_bytes()[bridge:]
        assert received and len(received)<len(display) and display.startswith(received)
        truncation=dict(expected_display_bytes=len(display),exact_received_prefix_bytes=len(received),
            missing_suffix_bytes=len(display)-len(received),missing_suffix_hex=display[len(received):].hex())
        assert truncation['missing_suffix_bytes']==473
        scope='Normal DOS recording, actual ASP compilation/replay, manual Search and hardware/timer restoration pass. The selected final Search footer preceded473 remaining form bytes; the decoded display is an exact prefix and the socket reports read ECONNRESET. Complete display and no-gateway-error gates remain failed. Local write callbacks are not peer-read acknowledgments; the exact kernel unread count was not traced.'
    paths=[path for path in out.rglob('*') if path.is_file()]
    result=dict(diagnostic_evidence_preserved=True,actual_audio_accepted=False,cohort=str(out.relative_to(ROOT)),
        failure_kind=a.kind,observed_helper=helper,observed_screen=text,diagnostic_stop=stop,display_truncation=truncation,
        producer_checks=r['checks'],independent_checks=audit['checks'],serial_checks=io['checks'],
        exact_online_bytes=len(serial)-9,payloads=audit['payloads'],
        terminal_sha256=sha(out/'program/TERMINAL.EXE'),ASPECT_sha256=sha(out/'program/ASPECT.EXE'),
        frozen_inputs=r['frozen_inputs'],runtime_inputs=r['runtime_inputs'],
        retained_sha256={str(path.relative_to(ROOT)):sha(path) for path in paths},recorder_sha256=sha(Path(__file__)),
        scope=scope+' No actual audio acceptance, physical modem or full application acceptance.')
    with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(diagnostic_evidence_preserved=True,actual_audio_accepted=False,retained_files=len(paths))))


if __name__=='__main__':main()
