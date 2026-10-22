#!/usr/bin/env python3
"""Seal BIOS/TCP preparation and immutable admission inputs, not live audio."""
import argparse,json,shutil
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from synthmodem_buffered_runtime import validate


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('keys','tcp','runtime','runtime-proof','audio-cohort','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();target=a.output.resolve();cohort=a.cohort.resolve()
    assert target.is_relative_to(ROOT/'docs/validation') and not target.exists()
    assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    selected={Path(__file__).resolve(),ROOT/'lab/bbs/synthmodem_audio_dos.py',ROOT/'lab/bbs/audit_synthmodem_audio_dos.py'}
    keys=a.keys.resolve();tcp=a.tcp.resolve();audio=a.audio_cohort.resolve()
    assert all(path.is_relative_to(ROOT/'build') for path in (keys,tcp,audio))
    k=json.loads(keys.read_text());t=json.loads(tcp.read_text());start=json.loads((audio/'run-start.json').read_text())
    assert k['passed'] and len(k['cases'])==7 and all(c['passed'] and all(c['checks'].values()) for c in k['cases'])
    assert t['passed'] and all(t['checks'].values()) and t['helper_sha256']==k['production_helper_sha256']
    for r in (k,t):
        for name,digest in r['inputs'].items():assert sha(ROOT/name)==digest,name
    for name,digest in t['captures_sha256'].items():assert sha(tcp.parent/name)==digest,name
    if start.get('initialization_wait_seconds') is not None:
        assert t['initialization_wait_seconds']==start['initialization_wait_seconds']
    assert start['route']=='recording'
    assert not start.get('recording_marker_trace',False),'Diagnostic helper cannot establish production preparation'
    assert start['generated_inputs']['program/EXITKEY.COM']==k['production_helper_sha256']
    for name,digest in start['frozen_inputs'].items():assert sha(ROOT/name)==sha(audio/'frozen-source'/name)==digest,name
    for name,digest in start['generated_inputs'].items():assert sha(audio/name)==digest,name
    runtime=validate(a.runtime.resolve(),a.runtime_proof.resolve());assert runtime==start['runtime_inputs']
    assert 'program/PCPLUS.ASP' not in start['generated_inputs'] and 'program/PCPLUS.ASX' not in start['generated_inputs']
    selected.update(p for p in keys.parent.rglob('*') if p.is_file())
    selected.update(p for p in tcp.parent.rglob('*') if p.is_file())
    selected.add(audio/'run-start.json')
    selected.update(audio/name for name in start['generated_inputs'])
    selected.update(p for p in (audio/'frozen-source').rglob('*') if p.is_file())
    # Earlier attempts are evidence of a missing transient screen observation
    # and a mismatched TCP hangup fixture, never successful helper controls.
    for label in ('audio-recording-control-01','audio-recording-control-02'):
        folder=ROOT/'build/bbs-lab/results/enigma'/label
        selected.update(p for p in folder.rglob('*') if p.is_file())
    for label in ('recording-audio-keys-01','recording-audio-keys-02','recording-audio-keys-03'):
        folder=ROOT/'build/bbs-lab'/label
        selected.update(p for p in folder.rglob('*') if p.is_file())
    cohort.mkdir();kept={}
    for path in sorted(selected):
        copy=cohort/'accepted'/path.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,copy);assert sha(copy)==sha(path)
        kept[str(copy.relative_to(ROOT))]=sha(copy)
    result=dict(passed=True,preparation_only=True,actual_audio_accepted=False,
        initialization_wait_seconds=start.get('initialization_wait_seconds'),BIOS_cases=7,TCP_checks=t['checks'],terminal_sha256=t['binary_sha256'],helper_sha256=t['helper_sha256'],
        runtime_inputs=runtime,audio_admission=str((audio/'run-start.json').relative_to(ROOT)),custody_sha256=kept,
        earlier_audio_failure='docs/validation/recording-audio-early-menu-failure.json',
        earlier_final_page_failure='docs/validation/recording-audio-final-page-failure.json',
        scope='Actual8086 BIOS key/gate/queue/watchdog/vector probes and an actual DOS/Telnet BBS control pass. The helper requires startup RECORDER READY before opening the menu; visible File Base without readiness cannot admit keys. Final exit requires late Search fields, the focused input cursor and180 quiet screen ticks; incomplete forms block exit and display changes restart the interval. The same helper is admitted to pinned200ms V22/1200 SIP/audio with immutable admission/source inputs preserved. Live audio captures are not sealed here. No audio outcome, physical hardware or full application acceptance.')
    with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,preparation_only=True,actual_audio_accepted=False,custody_files=len(kept))))


if __name__=='__main__':main()
