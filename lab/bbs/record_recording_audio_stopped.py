#!/usr/bin/env python3
"""Preserve a deliberately stopped recorder test and observed private helper phase."""
import argparse,json,shutil
from pathlib import Path
from synthmodem_vm_control import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.cohort.resolve();target=a.output.resolve();assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
    read=lambda name:json.loads((out/name).read_text())
    r=read('result.json');audit=read('independent-audit.json');io=read('serial-io-audit.json');stop=read('diagnostic-stop.json');memory=read('diagnostic-memory.json')
    assert r['route']=='recording' and not r['recording_marker_trace'] and not r['passed'] and not audit['passed']
    assert stop['intentional'] and stop['signal']=='SIGABRT' and stop['script_OK_age_seconds']>120
    assert read('exit-status.json')==dict(DOS=-6,node=0)
    assert not r['checks']['DOS_normal_exit'] and not r['checks']['UART_restored'] and not r['checks']['keyboard_helper_retired']
    assert audit['checks']['producer_inputs_unchanged'] and io['evidence_consistent'] and all(io['checks'].values())
    for name,digest in r['frozen_inputs'].items():assert sha(ROOT/name)==sha(out/'frozen-source'/name)==digest
    for name,digest in r['captures_sha256'].items():assert sha(out/name)==digest
    assert memory['intentional_diagnostic'] and memory['PID']==stop['PID'] and memory['temporary_core_deleted_on_exit']
    assert memory['helper_file_sha256']==sha(out/'program/EXITKEY.COM')
    assert len(memory['observations'])==1
    helper=memory['observations'][0]['helper_report'];assert helper[:4]==[0x524b,0,0,0] and helper[5]==0
    assert not (out/'program/PCPLUS.ASP').exists() and not (out/'program/PCPLUS.ASX').exists()
    assert not any(path.suffix=='.core' for path in out.rglob('*'))
    result=dict(diagnostic_evidence_preserved=True,actual_audio_accepted=False,intentionally_stopped=True,cohort=str(out.relative_to(ROOT)),stop=stop,helper_memory=memory,producer_checks=r['checks'],independent_checks=audit['checks'],serial_checks=io['checks'],terminal_sha256=sha(out/'program/TERMINAL.EXE'),retained_sha256={str(path.relative_to(ROOT)):sha(path) for path in out.rglob('*') if path.is_file()},recorder_sha256=sha(Path(__file__)),scope='Owned test deliberately aborted after SCRIPT.OK/Files without recorder navigation. The helper remains phase0 with no recipe keys/retries. Guest RAM identification supports helper private state; packed screen candidates are not resolved VGA storage. Temporary extracted cores were deleted; systemd retention is unchanged. No accidental application crash, normal hardware/timer cleanup, production audio or physical acceptance is claimed.')
    target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(diagnostic_evidence_preserved=True,intentionally_stopped=True,actual_audio_accepted=False)))


if __name__=='__main__':main()
