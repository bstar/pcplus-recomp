#!/usr/bin/env python3
"""Audit private ready-marker observations without accepting diagnostic audio."""
import argparse,json,struct,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha


def read(path):return json.loads(path.read_text())


def classify(trace,helper,initial_ticks):
    assert len(trace)==11 and trace[:2]==(0x5254,1)
    assert len(helper)==8 and helper[0]==0x524b
    _,_,samples,seen,entries,first,last,longest,current,misses,cursor=trace
    assert entries<=seen<=samples<=helper[4]
    assert current<=longest<=seen and misses<=samples-seen
    if not seen:
        assert (entries,first,last,longest,current,misses,cursor)==(0,0,0,0,0,0,0)
        assert helper[1:3]==(0,0)
        verdict='not_observed_by_helper'
    else:
        assert entries and 0<first<=last<=helper[4] and longest
        if helper[1] or helper[2]:
            assert helper[1]>0 and helper[2]>0 and longest>=initial_ticks+1
            verdict='recipe_started'
        elif longest<initial_ticks+1:verdict='observed_without_required_stable_run'
        else:verdict='stable_marker_observed_without_recipe_key'
    return dict(verdict=verdict,phase0_scan_samples=samples,matching_samples=seen,matching_runs=entries,first_tick=first,last_tick=last,longest_consecutive_samples=longest,required_consecutive_samples=initial_ticks+1,missing_samples_after_first_match=misses,first_observed_BIOS_cursor=cursor,helper_phase=helper[1],delivered_recipe_keys=helper[2],helper_exit_reason=helper[3])


def probes(a):
    normal=read(a.normal);trace=read(a.trace);guard=read(a.admission)
    baseline=read(a.baseline)
    assert baseline['passed'] and sha(a.baseline.parent/'PRODUCTION.COM')==baseline['production_helper_sha256']
    assert normal['passed'] and not normal['diagnostic_marker_trace'] and len(normal['cases'])==7
    assert trace['passed'] and trace['diagnostic_marker_trace'] and len(trace['cases'])==8
    assert normal['production_helper_sha256']==trace['production_helper_sha256']==baseline['production_helper_sha256']
    assert guard['passed'] and len(guard['cases'])==3 and all(c['rejected'] for c in guard['cases'])
    assert guard['normal_proof_sha256']==sha(a.normal) and guard['trace_proof_sha256']==sha(a.trace)
    for name,digest in guard['inputs'].items():assert sha(ROOT/name)==digest
    rows=[]
    for report,path in [(normal,a.normal),(trace,a.trace)]:
        for name,digest in report['inputs'].items():assert sha(ROOT/name)==digest
        for case in report['cases']:
            assert case['passed'] and all(case['checks'].values())
            folder=path.parent/case['name']
            for name,digest in case['captures_sha256'].items():assert sha(folder/name)==digest
            if report is trace:
                words=struct.unpack('<11H',(folder/'RECTRACE.BIN').read_bytes())
                helper=struct.unpack('<8H',(folder/'RECKEY.BIN').read_bytes())
                assert list(words)==case['marker_trace'] and list(helper)==case['helper_report']
                rows.append(dict(case=case['name'],**classify(words,helper,2)))
    assert rows[-1]['verdict']=='observed_without_required_stable_run' and rows[-1]['matching_samples'] in (1,2)
    assert next(r for r in rows if r['case']=='file-screen-without-ready-watchdog')['verdict']=='not_observed_by_helper'
    return dict(passed=True,production_helper_unchanged=True,normal_BIOS_cases=7,diagnostic_BIOS_cases=8,production_admission_rejections=3,production_helper_sha256=normal['production_helper_sha256'],cases=rows,baseline_proof_sha256=sha(a.baseline),normal_proof_sha256=sha(a.normal),trace_proof_sha256=sha(a.trace),guard_proof_sha256=sha(a.admission),scope='Actual8086 owned BIOS probes with shortened timings. Raw counter/key reports, hashes and restoration checks verified; transient and absent markers stay distinct. Ordinary helper equals the retained preceding production binary. This is not a BBS or audio outcome.')


def flight(a):
    out=a.cohort.resolve();work=a.work.resolve()
    assert out.is_relative_to(ROOT/'build') and work.is_relative_to(ROOT/'build') and not work.exists()
    r=read(out/'result.json');start=read(out/'run-start.json');audit=read(out/'independent-audit.json');io=read(out/'serial-io-audit.json')
    assert r['route']=='recording' and r['recording_marker_trace'] and start['recording_marker_trace']
    assert r['recording_marker_watchdog_ticks']==start['recording_marker_watchdog_ticks']==12000
    assert not r['passed'] and not r['checks']['diagnostic_marker_trace_is_not_production']
    assert not audit['passed'] and not audit['checks']['diagnostic_marker_trace_is_not_production']
    assert audit['checks']['producer_inputs_unchanged'] and io['evidence_consistent'] and all(io['checks'].values())
    for name,digest in r['frozen_inputs'].items():assert sha(ROOT/name)==sha(out/'frozen-source'/name)==digest
    for name,digest in r['captures_sha256'].items():assert sha(out/name)==digest
    for name,digest in start['generated_inputs'].items():assert sha(out/name)==digest
    tools=[name for name in r['tool_inputs'] if Path(name).name=='nasm'];assert len(tools)==1
    nasm=Path(tools[0]);assert str(nasm).startswith('/nix/store/') and sha(nasm)==r['tool_inputs'][str(nasm)]
    work.mkdir(parents=True);source=out/'frozen-source/lab/bbs/audio_recording_keys.asm'
    for leaf,flags in [('KEYBASE.COM',[]),('EXITKEY.COM',['-DRECORD_MARKER_TRACE=1','-DRECORD_WATCHDOG_TICKS=12000'])]:
        subprocess.run([str(nasm),'-fbin',*flags,str(source),'-o',str(work/leaf)],check=True)
        assert sha(work/leaf)==sha(out/'program'/leaf)
    trace=struct.unpack('<11H',(out/'RECTRACE.BIN').read_bytes());helper=struct.unpack('<8H',(out/'RECKEY.BIN').read_bytes())
    assert list(trace)==r['recording']['diagnostic_marker_trace']
    assert helper[3] in (1,2) and helper[4]>0
    if helper[3]==2:assert helper[4]>=12000
    return dict(diagnostic_evidence_preserved=True,actual_audio_accepted=False,cohort=str(out.relative_to(ROOT)),terminal_sha256=sha(out/'program/TERMINAL.EXE'),diagnostic_helper_sha256=sha(work/'EXITKEY.COM'),production_helper_sha256=sha(work/'KEYBASE.COM'),trace=list(trace),helper_report=list(helper),observation=classify(trace,helper,90),producer_checks=r['checks'],independent_checks=audit['checks'],serial_checks=io['checks'],serial_error_events=io['error_events'],retained_sha256={str(path.relative_to(ROOT)):sha(path) for path in out.rglob('*') if path.is_file()},scope='Diagnostic V22/audio run with private BIOS ready-marker counters and12000-tick watchdog. Helper binaries reproduce from frozen source using the admitted Nix NASM. Observations cover helper samples, not every painted video frame. Diagnostic producer/auditor gates stay failed; no normal audio, physical modem or full application acceptance.')


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    probe=sub.add_parser('probes')
    for name in ('normal','trace','admission','baseline'):probe.add_argument('--'+name,type=Path,required=True)
    live=sub.add_parser('flight');live.add_argument('cohort',type=Path);live.add_argument('--work',type=Path,required=True)
    for parser in (probe,live):parser.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert a.output.resolve().is_relative_to(ROOT/'docs/validation') and not a.output.exists()
    result=probes(a) if a.mode=='probes' else flight(a);result['auditor_sha256']=sha(Path(__file__))
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(mode=a.mode,output=str(a.output),actual_audio_accepted=False)))


if __name__=='__main__':main()
