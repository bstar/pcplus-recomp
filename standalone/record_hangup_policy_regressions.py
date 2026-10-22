#!/usr/bin/env python3
"""Record current-parent stock BBS, startup and attached-PROGRAM regressions."""
import argparse,json,re
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('recording','windows','startup','program','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();records={name:read(getattr(a,name)) for name in ('recording','windows','startup','program')}
    normal=ROOT/'build/terminal/TERMINAL.EXE';parent=sha(normal);sources={};products={}
    for directory,binary in [('terminal','TERMINAL.EXE'),('terminal-mouse','TERMINAL.EXE'),('terminal-process','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE'),('aspect-process-parent','ASPECT.EXE'),('aspect-compiler-dos','ASPCOMP.EXE')]:
        base=ROOT/'build'/directory;m=read(base/'manifest.json');assert sha(base/binary)==m['binary_sha256'];products[directory]=m['binary_sha256']
        for name,digest in m['sources'].items():
            assert name not in sources or sources[name]==digest
            assert sha(ROOT/name)==digest;sources[name]=digest
    recording=records['recording'];windows=records['windows']
    assert recording['passed'] and recording['selected_modern_BBS_recorder_workflows_accepted'] and not recording['full_F13_accepted']
    assert windows['passed'] and windows['selected_stock_BBS_script_window_accepted'] and not windows['current_audio_accepted']
    for report in (recording,windows):
        assert set(report['servers'])=={'synchronet','enigma'}
        for path,digest in report['custody_sha256'].items():assert sha(ROOT/path)==digest
        for server in report['servers'].values():assert server.get('binary_sha256',server.get('terminal_sha256'))==parent
    fixture=recording['synchronet_logon_fixture'];assert fixture['restored'] and fixture['before']==fixture['after']
    state=read(ROOT/fixture['record']);assert sha(ROOT/fixture['record'])==fixture['sha256'] and state['restored']
    startup=records['startup'];assert startup['passed'] and startup['binary_sha256']==parent and startup['invalid_abi_guards_required']
    assert len(startup['cases'])==6 and all(v['passed'] for v in startup['cases'])
    assert next(v['inputs'] for v in startup['cases'] if v['case']=='invalid-near-extents-and-overlapping-output-IO-buffers-rejected')==8
    program=records['program'];assert program['passed'] and len(program['cases'])==13
    assert program['parent_sha256']==products['terminal-process'] and program['child_sha256']==products['aspect-process-parent']
    for name,digest in program['source_hashes'].items():assert sha(ROOT/name)==digest and sha(a.program.parent/'sources'/name)==digest
    # Fixed retained regions plus every declared two-byte renderer policy word.
    policy_words=len(re.findall(r'X\((\w+)\)',(ROOT/'src/aspect/renderer_policy.h').read_text()))
    retained_bytes=10152+2*policy_words
    rows=[]
    for case in program['cases']:
        assert case['passed'] and all(case['checks'].values());folder=a.program.parent/case['case'];size=case['compared_parent_bytes'];assert size==retained_bytes
        raw=(folder/'RENDER.BIN').read_bytes();assert raw[-2*size:-size]==raw[-size:]
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes() and (folder/'BEFORE.BIN').stat().st_size==42
        assert sha(folder/'TERMINAL.EXE')==program['parent_sha256'] and sha(folder/'ASPECT.EXE')==program['child_sha256']
        assert case['resource_words'][2]==case['resource_words'][7]==0
        rows.append(dict(case=case['case'],passed=True,compared_parent_bytes=size,result_sha256=sha(folder/'result.json'),observation_sha256=sha(folder/'RENDER.BIN')))
    result=dict(passed=True,selected_current_parent_regressions_accepted=True,current_audio_accepted=False,full_application_accepted=False,physical_hardware_accepted=False,
        products=products,reports={name:dict(path=str(getattr(a,name)),sha256=sha(getattr(a,name))) for name in records},
        stock_BBS_recording_sessions=4,stock_BBS_window_sessions=2,startup_groups=6,startup_invalid_ABI_cases=8,startup_inputs=startup['inputs'],attached_PROGRAM_cases=rows,
        synchronet_logon_fixture=fixture,source_inputs=sources,auditor_sha256=sha(Path(__file__)),
        scope='Current failed-hangup parent: independently accepted stock Synchronet/ENiGMA record/DOS compilation/replay/manual navigation and script reference/help/continuation/parent-menu return, linked startup/invalid ABI checks and13 attached DOS PROGRAM regressions. Temporary synthetic-account quota exemption restored. Normal/mouse source reproduction retains the separate hangup policy receipt. No current-parent audio acceptance, sustained flow pressure, physical modem or full application claim.')
    assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,recording_sessions=4,window_sessions=2,startup_groups=6,PROGRAM_cases=13)))


if __name__=='__main__':main()
