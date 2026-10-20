#!/usr/bin/env python3
"""Record the experimental full-VM binding separately from normal ASPECT."""
import argparse,itertools,json,re
from pathlib import Path
from build_aspect_process import ROOT,OUT,sha


def read(path):return json.loads(path.read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True)
    parser.add_argument('--source-label',required=True);parser.add_argument('--failed-label',action='append',default=[])
    args=parser.parse_args()
    for label in [args.label,args.source_label,*args.failed_label]:assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
    folder=OUT/'runs'/args.label;run=read(folder/'result.json');manifest=read(OUT/'manifest.json')
    assert run['passed'] and len(run['cases'])==56
    assert {(c['port'],c['flow'],c['kind']) for c in run['cases']}==set(itertools.product((1,2),'NSHB',('full','fallback','large','memory','divide','abort','budget')))
    assert manifest['diagnostic_build'] and manifest['experimental_external_commands'] and not manifest['production_dispatch_changed']
    assert run['binary_sha256']==manifest['binary_sha256']==sha(OUT/'ASPECT.EXE')
    assert run['manifest_sha256']==sha(OUT/'manifest.json')==sha(folder/'manifest.json')
    assert run['checker_sha256']==sha(ROOT/'standalone/test_aspect_process_dos.py')
    for name,digest in {**manifest['sources'],**run['owned_sources']}.items():assert sha(ROOT/name)==sha(folder/'sources'/name)==digest,name
    overlaps=[];groups={}
    for case in run['cases']:
        assert case['passed'] and all(case['checks'].values()) and not case['timed_out']
        sub=folder/f"com{case['port']}-{case['flow']}-{case['kind']}"
        for name,digest in case['artifacts'].items():assert sha(sub/name)==digest,name
        if case['kind']=='large':
            match=re.search(r'ARENA borrowed(\d+) live-frame(\d+)',(sub/'CHECKS.TXT').read_text())
            assert match and int(match[1])>int(match[2])>0
            overlaps.append(dict(port=case['port'],flow=case['flow'],borrowed_bytes=int(match[1]),live_frame_offset=int(match[2])))
        group=groups.setdefault(case['kind'],dict(cases=0,assertions=0,external_calls=0,DOS_compiler_calls=0))
        group['cases']+=1;group['assertions']+=case['assertions'];group['external_calls']+=case['calls'];group['DOS_compiler_calls']+=case['compiler_calls']
    proof_folder=OUT/'source-proofs'/args.source_label;proof=read(proof_folder/'result.json')
    assert proof['passed'] and len(proof['products'])==23 and proof['manifest_sha256']==sha(OUT/'manifest.json')
    assert proof['checker_sha256']==sha(ROOT/'standalone/check_aspect_process_source.py')
    for name,item in proof['products'].items():assert item['expected']==item['actual']==sha(ROOT/'build'/name)==sha(proof_folder/'source/build'/name)
    for name,digest in proof['sources'].items():assert sha(ROOT/name)==sha(proof_folder/'source'/name)==digest,name
    handles=read(OUT/'handles.json');assert handles['passed'] and len(handles['cases'])==19
    assert handles['binary_sha256']==manifest['binary_sha256'] and handles['manifest_sha256']==sha(OUT/'manifest.json')
    assert handles['checker_sha256']==sha(ROOT/'standalone/check_process_handles.py')
    policy=read(OUT/'policy.json');assert policy['passed'] and len(policy['cases'])==14
    assert policy['binary_sha256']==manifest['binary_sha256'] and policy['manifest_sha256']==sha(OUT/'manifest.json')
    assert policy['checker_sha256']==sha(ROOT/'standalone/check_aspect_process_policy.py')
    before=read(OUT/'policy-before.json');assert not before['passed'] and before['checker_sha256']==policy['checker_sha256']
    assert {c['case'] for c in before['cases'] if not c['passed']}=={'process-state-fatal','process-busy-fatal','unknown-program-result-fatal','unknown-process-result-fatal','contradictory-process-result-fatal'}
    runtime=read(ROOT/'build/aspect-runtime/checks.json');serial=read(ROOT/'build/aspect-serial/checks.json')
    assert runtime['passed'] and runtime['supported_slot_count']==105 and runtime['unsupported_slot_cases']==110
    assert serial['passed'] and sum(g['inputs'] for g in serial['groups'])==108
    normal_sha=sha(ROOT/'build/aspect-runner/ASPECT.EXE')
    assert normal_sha=='aef146fdf62846a2dfc5d73413f435a8bfe68ca4f68d639178083d4d21e559f5'
    failures=[]
    for label in args.failed_label:
        old=read(OUT/'runs'/label/'result.json');assert not old['passed']
        failures.append(dict(label=label,sha256=sha(OUT/'runs'/label/'result.json'),
            checks=[c['checks'] for c in old['cases']],reason='Retained recipe failure; not counted as accepted compatibility evidence.'))
    result=dict(passed=True,experimental_only=True,whole_application_gates_closed=[],
        normal_supported_slots=105,experimental_supported_slots=108,normal_dispatch_changed=False,
        original_build_inputs=[],experimental_binary_sha256=manifest['binary_sha256'],normal_binary_sha256=normal_sha,
        DOS_cases=56,DOS_assertions=sum(c['assertions'] for c in run['cases']),groups=groups,
        frame_overlap_cases=overlaps,linked_JFT_cases=19,linked_policy_models=14,fresh_source_products=23,
        policy_counterexample=dict(binary_sha256=before['binary_sha256'],failed_cases=[c['case'] for c in before['cases'] if not c['passed']]),
        normal_runtime_summary=runtime['DOS_summary'],normal_serial_inputs=108,
        sources=manifest['sources'],owned_test_sources=run['owned_sources'],
        nix_inputs={name:sha(ROOT/name) for name in ('nix/flake.nix','nix/flake.lock')},
        recorder_sha256=sha(Path(__file__)),DOS_checker_sha256=run['checker_sha256'],
        evidence={str(path.relative_to(ROOT)):sha(path) for path in (folder/'result.json',folder/'manifest.json',
            proof_folder/'result.json',proof_folder/'build.log',OUT/'handles.json',OUT/'policy.json',OUT/'policy-before.json',
            ROOT/'build/aspect-runtime/checks.json',ROOT/'build/aspect-serial/checks.json')},retained_failures=failures,
        limitations=['Normal ASPECT still rejects DOS/RUN/SHELL; the108-slot variant is experimental and separately built.',
            'Attached parent renderers reject before flushing or modifying ownership. ASIOv4 parent renderer and actual selected directory/translation leases remain open.',
            'Standard ROM font/BIOS keyboard platform only; complete original macro/mouse/window/error-notice services and other views remain open.',
            'Abort/budget recovery is after external return. Nonlocal parent faults during the owned external operation require separate unwind evidence.',
            'The 14 policy cases model owner/file/renderer outcomes and are not counted as actual DOS executions.',
            'DOSBox internal DOS/default20-entry JFT execution is covered;40/255-entry tables are linked scalar PSP models, not other-kernel/hardware execution.',
            'Physical RS-232 Wi-Fi modem and complete live ENiGMA/Synchronet workflows remain unverified by these tests.'])
    (ROOT/'docs/validation/aspect-process.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recorded56 real ASPECT/DOS cases,19 JFT models and23 fresh products; normal ASPECT remains105 slots.')


if __name__=='__main__':main()
