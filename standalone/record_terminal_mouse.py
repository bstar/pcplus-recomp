#!/usr/bin/env python3
"""Record selectable terminal integration, real quarantine and ASPECT recovery."""
import argparse
from datetime import date
import json
from pathlib import Path
import re
from build_native_mouse import ROOT,sha
from omf_imports import records,externals


def read(path):return json.loads(path.read_text())


def current(sources, frozen=None):
    for name,digest in sources.items():
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(ROOT/name)==digest,name
        if frozen:assert sha(frozen/name)==digest,name


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('dos-label','source-label','fault-label','both-label','soft-label','none-label','enigma-label'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--component-receipt',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--settings',action='store_true',help='Require live settings/editor acceptance and31 source products')
    parser.add_argument('--package-label',help='Require the matching mouse package DOS smoke test')
    args=parser.parse_args()
    for value in vars(args).values():
        if isinstance(value,str):assert re.fullmatch(r'[A-Za-z0-9_-]+',value)
    products={name:ROOT/'build'/name/'TERMINAL.EXE' for name in ('terminal-mouse','terminal-mouse-process')}
    manifests={name:read(path.parent/'manifest.json') for name,path in products.items()}
    evidence=[]
    for name,path in products.items():
        manifest=manifests[name]
        assert manifest['experimental_mouse'] and manifest['binary_sha256']==sha(path)
        current(manifest['sources'])
        assert manifest['memory_layout']['mouse_bridge_pairs_verified']==(10 if args.settings else 7)
        assert manifest['memory_layout']['resident_code_bytes']<65536 and manifest['data_stack_bytes']<65536
        evidence += [path.parent/'manifest.json',path.parent/'terminal.map']
    normal=products['terminal-mouse'];parent=products['terminal-mouse-process']
    policy_path=normal.parent/'mouse-policy.json';policy=read(policy_path)
    policy_cases=31 if args.settings else 17
    assert policy['passed'] and len(policy['cases'])==policy_cases and all(c['passed'] for c in policy['cases'])
    assert policy['binary_sha256']==sha(normal)
    assert policy['checker_sha256']==sha(ROOT/'standalone/check_terminal_mouse.py')
    assert policy['owner_boundary_checker_sha256']==sha(ROOT/'standalone/check_mouse_keyboard.py')
    evidence.append(policy_path)
    owner_imports=[n.decode() for k,p,r in records((normal.parent/'owner.obj').read_bytes()) if k==0x8c for n,i in externals(p)]
    assert owner_imports and all(n.startswith('_mouse_') or n=='_small_code_' for n in owner_imports)
    dos_dir=ROOT/'build/terminal-mouse-tests'/args.dos_label;dos=read(dos_dir/'checks.json')
    assert dos['passed'] and dos['sources_unchanged'] and dos['binary_sha256']==sha(normal)
    required={'normal','menu','program','quarantine','invalid-scale','no-driver','unsupported-driver'}
    if args.settings:required|={'live-save','live-cancel','live-invalid','live-child-failed','startup-repair'}
    assert {c['case'] for c in dos['cases']}==required
    current(dos['sources'],dos_dir/'sources')
    assertions=0;observations={}
    for case in dos['cases']:
        assert case['passed'] and all(case['checks'].values())
        path=dos_dir/case['case']/'MOUSE.OUT';text=path.read_text()
        assert text==case['mouse_report']
        match=re.fullmatch(r'MOUSEOBS checks=(\d+) failures=(\d+) child=(\d+) retained=(\d+) driver_bytes=(\d+) stage=(\d+) callback=(\d+) registrations=(\d+)\s*',text)
        assert match and int(match[2])==0 and int(match[5])==576
        assertions+=int(match[1])
        observations[case['case']]=dict(zip(('assertions','failures','DOS_child_status','retained_owners','driver_bytes','observer_stage','retained_callback_invoked','registrations'),map(int,match.groups())))
        evidence += [dos_dir/case['case']/'result.json',path]
    assert assertions==(119 if args.settings else 69)
    assert observations['quarantine']['DOS_child_status']==0x030e
    evidence.append(dos_dir/'checks.json')
    source_dir=ROOT/'build/aspect-unwind-mouse/source-proofs'/args.source_label;proof=read(source_dir/'result.json')
    assert proof['passed'] and proof['experimental_mouse'] and proof['original_inputs']==[] and len(proof['products'])==(31 if args.settings else 29)
    assert proof['checker_sha256']==sha(ROOT/'standalone/check_aspect_unwind_source.py')
    assert proof['log_sha256']==sha(source_dir/'build.log')
    current(proof['sources'],source_dir/'source')
    for name,pair in proof['products'].items():
        assert pair['actual']==pair['expected']==sha(ROOT/'build'/name)==sha(source_dir/'source/build'/name)
    editor_models={}
    settings_regression={}
    package_acceptance={}
    if args.settings:
        counter_path=ROOT/'build/mouse-settings-rebind-counterexample.json';counter=read(counter_path)
        assert counter['counterexample_reproduced'] and counter['expected_active']==[8,4] and counter['old_candidate_active']==[16,8]
        assert counter['checker_sha256']==sha(ROOT/'standalone/check_terminal_mouse.py')
        settings_regression=counter;evidence.append(counter_path)
        assert args.package_label
        package_dir=ROOT/'build/dos-package-mouse';package=read(package_dir/'manifest.json')
        package_path=ROOT/'build/package-mouse-tests'/args.package_label/'result.json';package_test=read(package_path)
        assert package_test['passed'] and all(package_test['checks'].values())
        assert package_test['package_manifest_sha256']==sha(package_dir/'manifest.json')
        assert package_test['checker_sha256']==sha(ROOT/'standalone/test_package_mouse.py')
        assert package['experimental_mouse'] and package['original_inputs']==[]
        current(package['sources'])
        assert all(sha(package_dir/p)==h for p,h in package['files'].items())
        assert package['files']['TERMINAL.EXE']==sha(normal)
        assert package['files']['PRMEDIT.EXE']==proof['products']['setup-mouse/PRMEDIT.EXE']['actual']
        package_acceptance=dict(files=package['files'],checks=package_test['checks'])
        evidence += [package_path,package_dir/'manifest.json']
        assert proof['products']['setup/PRMEDIT.EXE']['actual']=='0c814a4122a2b3c705fee8f17e0cd7a2a3d314493df24d164c106f3fe6058646'
        for directory,fields,inputs in [('setup-model',48,450),('setup-model-mouse',50,470)]:
            folder=ROOT/'build'/directory;model=read(folder/'checks.json')
            assert model['passed'] and model['field_count']==fields
            assert sum(c['inputs'] for c in model['cases'])==inputs and all(c['passed'] for c in model['cases'])
            current(model['sources']);assert model['binary_sha256']==sha(folder/'MODEL.EXE')
            editor_models[directory]=dict(field_count=fields,inputs=inputs,binary_sha256=model['binary_sha256'])
            evidence+=[folder/'checks.json',folder/'VALID.PRM',folder/'LOG.TXT']
        for name in ('setup','setup-mouse'):
            editor=read(ROOT/'build'/name/'manifest.json');current(editor['sources'])
            assert editor['field_count']==(50 if name=='setup-mouse' else 48)
            assert editor['binary_sha256']==proof['products'][name+'/PRMEDIT.EXE']['actual']
            evidence.append(ROOT/'build'/name/'manifest.json')
    component=read(args.component_receipt)
    assert component['passed'] and component['linked_policy_cases']==244 and component['actual_DOS_assertions']==130
    assert component['recorder_sha256']==sha(ROOT/'standalone/record_mouse_bank.py')
    for item in component['evidence']:assert sha(ROOT/item['path'])==item['sha256']
    assert len(component['preserved_application_products'])==27
    for name,digest in component['preserved_application_products'].items():assert proof['products'][name]['actual']==digest
    evidence += [source_dir/'result.json',source_dir/'build.log',args.component_receipt.resolve()]
    fault_rows=[]
    for label,expected_count,port,flow,phase in [(args.fault_label,89,1,'H',None),
            (args.both_label,1,2,'B',9),(args.soft_label,1,1,'S',6),(args.none_label,1,2,'N',10)]:
        folder=ROOT/'build/aspect-unwind-mouse/runs'/label;report=read(folder/'result.json')
        assert report['passed'] and report['experimental_mouse'] and report['parent_sha256']==sha(parent)
        assert report['checker_sha256']==sha(ROOT/'standalone/test_aspect_unwind_dos.py')
        assert len(report['cases'])==expected_count
        current(report['sources'],folder/'sources')
        for case in report['cases']:
            assert case['passed'] and all(case['checks'].values()) and case['port']==port and case['flow']==flow
            if phase is not None:assert case['phase']==phase and case['kind']=='D'
            fault_rows.append(dict(phase=case['phase'],kind=case['kind'],port=port,flow=flow,passed=True))
        if phase is None:
            assert {(c['phase'],c['kind']) for c in report['cases']}=={(p,k) for p in range(1,23) for k in 'DAFL'}|{(0,'D')}
        evidence.append(folder/'result.json')
    assert len(fault_rows)==92
    bbs_path=ROOT/'build/bbs-lab/results/enigma'/args.enigma_label/'search-checks.json';bbs=read(bbs_path)
    assert bbs['passed'] and bbs['experimental_mouse'] and bbs['terminal_sha256']==sha(normal)
    assert len(bbs['checks'])==20 and all(bbs['checks'].values())
    assert bbs['network_experiment']['requested_byte_delay_ms']==20 and bbs['network_experiment']['byte_conservation']
    assert bbs['input_hashes']['runner']==sha(ROOT/'lab/bbs/enigma_search_dos.py')
    assert bbs['input_hashes']['harness']==sha(ROOT/'lab/bbs/test_dos.py')
    assert bbs['input_hashes']['terminal_manifest']==sha(normal.parent/'manifest.json')
    evidence.append(bbs_path)
    memory=manifests['terminal-mouse']['memory_layout']
    report=dict(date=date.today().isoformat(),passed=True,selectable_only=True,
        normal_mouse_enabled=False,whole_application_gates_closed=[],original_build_inputs=[],
        products={p:v['actual'] for p,v in proof['products'].items()},normal_products_preserved=27,
        layout={n:memory[n] for n in ('resident_code_bytes','resident_code_spare_bytes','near_bytes','near_spare_bytes','mouse_code_bytes','mouse_bridge_pairs_verified','retained_parent_paragraphs')},
        foreground_policy_cases=policy_cases,component_regression_linked_cases=244,editor_models=editor_models,
        settings_regression=settings_regression,package_acceptance=package_acceptance,
        actual_terminal_DOS_cases=len(required),actual_terminal_DOS_assertions=assertions,actual_component_regression_DOS_assertions=130,
        DOS_observations=observations,actual_ASPECT_fault_DOS_cases=92,fault_cases=fault_rows,
        isolated_ENIGMA=dict(checks=bbs['checks'],network_experiment=bbs['network_experiment'],pages=bbs['pages'],route=bbs['route']),
        owner_imports=owner_imports,source_hashes=proof['sources'],
        evidence=[dict(path=str(p.resolve().relative_to(ROOT)),sha256=sha(p)) for p in evidence],
        nix_inputs={p:sha(ROOT/p) for p in ('nix/flake.nix','nix/flake.lock')},recorder_sha256=sha(Path(__file__)),
        limitations=['Mouse integration is selectable, not the normal default.',
                     'Startup directory browsing precedes mouse acquisition; return-prompt mouse acknowledgement remains open.',
                     'The ASPECT child remains BIOS-only; the parent mouse is suspended for its complete lifetime.',
                     'Quarantine intentionally retains DOS memory. Controlled repair/unload belongs only to the observer; no general unload command is provided.',
                     'ENiGMA uses the separate decoder candidate and synthetic catalog; the live board is unchanged.',
                     'Physical mouse/modem, other DOS kernels, arbitrary driver/kernel corruption and complete application coverage remain unverified.'])
    with args.output.open('x') as output:output.write(json.dumps(report,indent=2)+'\n')
    print(args.output)


if __name__=='__main__':main()
