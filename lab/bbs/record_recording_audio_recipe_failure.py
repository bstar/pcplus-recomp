#!/usr/bin/env python3
"""Preserve a normal-exit audio run whose recorder BIOS helper never starts."""
import argparse, json, struct
from pathlib import Path
from synthmodem_vm_control import ROOT, sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.cohort.resolve();target=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
    read=lambda name:json.loads((out/name).read_text())
    r=read('result.json');audit=read('independent-audit.json');io=read('serial-io-audit.json');offline=read('offline-caller.json')
    assert r['route']=='recording' and not r['passed'] and not audit['passed']
    assert {k for k,v in r['checks'].items() if not v}=={'recorded_source_complete','exact_recorded_user_bytes','DOS_compiled_exact_source','helper_completed_recipe','exact_record_replay_and_manual_route','exact_online_navigation_tail','final_manual_search_visible'}
    assert {k for k,v in audit['checks'].items() if not v}=={'complete_caller_stream_equals_bridge_plus_BBS_display','recording_exact_source_payload','DOS_created_source_and_bytecode','recording_script_replay_and_manual_bytes','recording_exact_authoritative_route','recording_helper_completed','recording_final_manual_search'}
    assert audit['checks']['producer_inputs_unchanged'] and r['checks']['VM_exited'] and r['checks']['script_completed']
    assert read('exit-status.json')==dict(DOS=0,node=0)
    assert io['evidence_consistent'] and all(io['checks'].values()) and not io['error_events']
    for name,digest in r['frozen_inputs'].items():assert sha(ROOT/name)==sha(out/'frozen-source'/name)==digest,name
    for name,digest in r['captures_sha256'].items():assert sha(out/name)==digest,name
    assert offline['checker_sha256']==r['frozen_inputs']['lab/bbs/diagnose_audio_caller.js']
    assert offline['capture_sha256']==sha(out/'rtp-from-caller.bin')
    serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(b'ATZ\rATD1\r')
    assert bytes.fromhex(''.join(row['hex'] for row in offline['received']))==serial[9:]
    words=struct.unpack('<8H',(out/'RECKEY.BIN').read_bytes());assert words[:5]==(0x524b,0,0,2,32000)
    assert not (out/'program/PCPLUS.ASP').exists() and not (out/'program/PCPLUS.ASX').exists()
    assert r['script_stages']=='BRIDGE|FORM|MAIN|MESSAGES|RETURN|FILES|'
    assert r['recording']['menus_after_file_base']==['fileBaseMainMenu','idleLogoff']
    assert r['recording']['recorded_payload_hex']==''
    retained={str(path.relative_to(ROOT)):sha(path) for path in out.rglob('*') if path.is_file()}
    result=dict(diagnostic_evidence_preserved=True,actual_audio_accepted=False,cohort=str(out.relative_to(ROOT)),failure_kind='recorder-helper-never-started',terminal_sha256=sha(out/'program/TERMINAL.EXE'),ASPECT_sha256=sha(out/'program/ASPECT.EXE'),helper_report=list(words),exact_online_bytes=len(serial)-9,producer_checks=r['checks'],independent_checks=audit['checks'],serial_checks=io['checks'],payloads=audit['payloads'],frozen_inputs=r['frozen_inputs'],runtime_inputs=r['runtime_inputs'],retained_sha256=retained,recorder_sha256=sha(Path(__file__)),scope='Normal DOS/gateway exit and startup navigation through Files; helper phase0 delivers no recipe keys and its32000-tick watchdog exits. The BBS logs off for inactivity; no recorded ASP/ASX, replay or final Search exists. Waveform-decoded guest stream and serial accounting agree; complete caller-display equality remains failed. This receipt preserves the failure without changing acceptance gates. No audio, physical modem or full application acceptance.')
    target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(diagnostic_evidence_preserved=True,actual_audio_accepted=False,files=len(retained))))


if __name__=='__main__':main()
