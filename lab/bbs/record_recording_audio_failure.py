#!/usr/bin/env python3
"""Preserve the early local-menu injection counterexample, without acceptance."""
import argparse,json
from pathlib import Path
from synthmodem_vm_control import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.cohort.resolve();target=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
    read=lambda name:json.loads((out/name).read_text())
    r=read('result.json');audit=read('independent-audit.json');io=read('serial-io-audit.json');offline=read('offline-caller.json')
    assert r['route']=='recording' and not r['passed'] and not r['checks']['script_completed']
    assert not audit['passed'] and audit['checks']['producer_inputs_unchanged']
    assert io['evidence_consistent'] and all(io['checks'].values()) and not io['error_events']
    assert r['checks']['VM_exited'] and r['checks']['no_gateway_errors']
    assert audit['checks']['complete_caller_stream_equals_bridge_plus_BBS_display']
    for name,digest in r['frozen_inputs'].items():assert sha(ROOT/name)==sha(out/'frozen-source'/name)==digest,name
    for name,digest in r['captures_sha256'].items():assert sha(out/name)==digest,name
    assert offline['checker_sha256']==r['frozen_inputs']['lab/bbs/diagnose_audio_caller.js']
    assert offline['capture_sha256']==sha(out/'rtp-from-caller.bin')
    serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(b'ATZ\rATD1\r')
    assert bytes.fromhex(''.join(row['hex'] for row in offline['received']))==serial[9:]
    assert not (out/'program/PCPLUS.ASP').exists() and not (out/'program/PCPLUS.ASX').exists()
    stop=read('diagnostic-stop.json');assert stop['intentional'] and stop['signal']=='SIGABRT'
    assert read('exit-status.json')==dict(DOS=-6,node=0)
    helper=read('diagnostic-helper.json');assert helper['report'][:4]==[0x524b,1,1,0]
    screens=read('diagnostic-screens.json');assert len(screens)==1
    text=(out/Path(screens[0]['screen']).with_suffix('.txt')).read_text()
    assert 'File Base >> active filter:' in text and 'error 3, opcode D5' in text and 'ASPECT returned an error.' in text
    paths=[path for path in out.rglob('*') if path.is_file()]
    result=dict(diagnostic_evidence_preserved=True,actual_audio_accepted=False,cohort=str(out.relative_to(ROOT)),
        observed_helper=helper,observed_screen=text,diagnostic_stop=stop,
        producer_checks=r['checks'],independent_checks=audit['checks'],serial_checks=io['checks'],
        exact_online_bytes=len(serial)-9,payloads=audit['payloads'],
        terminal_sha256=sha(out/'program/TERMINAL.EXE'),ASPECT_sha256=sha(out/'program/ASPECT.EXE'),
        frozen_inputs=r['frozen_inputs'],runtime_inputs=r['runtime_inputs'],
        retained_sha256={str(path.relative_to(ROOT)):sha(path) for path in paths},recorder_sha256=sha(Path(__file__)),
        scope='Intentional diagnostic termination of a stalled owned DOSBox test, not an unexplained DOSBox crash. Audio/guest/serial/Telnet bytes are exact and Node/VM retire, but the BIOS helper opened Alt-Z while startup ASPECT still owned WAITQUIET (D5). The VGA-referenced text cache shows typed error3; private helper state shows phase1, one delivered key, no recording. Normal DOS/hardware/timer restoration and recorder functionality are unaccepted. Original systemd core remains under its normal retention; extracted temporary core copies were deleted. No physical modem or full application acceptance.')
    with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(diagnostic_evidence_preserved=True,actual_audio_accepted=False,retained_files=len(paths))))


if __name__=='__main__':main()
