#!/usr/bin/env python3
"""Publish composed PROGRAM evidence without original images/private captures."""
import argparse,json,re
from pathlib import Path
from build_native_program import ROOT,OUT,sha


def read(path):return json.loads(path.read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True);parser.add_argument('--source-label',required=True)
    parser.add_argument('--failed-label',action='append',default=[])
    parser.add_argument('--rea-bundle',type=Path,required=True)
    args=parser.parse_args()
    for label in [args.label,args.source_label,*args.failed_label]:assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
    folder=OUT/'runs'/args.label;run=read(folder/'result.json');manifest=read(OUT/'manifest.json')
    assert run['passed'] and len(run['cases'])==8
    assert {(c['port'],c['flow']) for c in run['cases']}=={(p,f) for p in (1,2) for f in 'NSHB'}
    assert run['binary_sha256']==manifest['binary_sha256']==sha(OUT/'PROGRAM.EXE')
    assert run['manifest_sha256']==sha(OUT/'manifest.json')==sha(folder/'manifest.json')
    assert run['checker_sha256']==sha(ROOT/'standalone/test_native_program_dos.py')
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==sha(folder/'sources'/name)==digest,name
    for case in run['cases']:
        assert case['passed'] and all(case['checks'].values()) and case['assertions']==47667
        sub=folder/f"com{case['port']}-{case['flow']}"
        for name,digest in case['artifacts'].items():assert sha(sub/name)==digest,name
    proof_folder=OUT/'source-proofs'/args.source_label;source=read(proof_folder/'result.json')
    assert source['passed'] and source['manifest_sha256']==sha(OUT/'manifest.json')
    assert source['checker_sha256']==sha(ROOT/'standalone/check_native_program_source.py')
    assert source['build_log_sha256']==sha(proof_folder/'build.log') and len(source['products'])==20
    for name,item in source['products'].items():
        assert item['expected']==item['actual']==sha(ROOT/'build'/name)==sha(proof_folder/'source/build'/name)
    for name,digest in source['sources'].items():assert sha(ROOT/name)==sha(proof_folder/'source'/name)==digest
    admission=read(OUT/'admission.json')
    assert admission['passed'] and len(admission['cases'])==13 and all(c['passed'] for c in admission['cases'])
    assert admission['binary_sha256']==manifest['binary_sha256'] and admission['manifest_sha256']==sha(OUT/'manifest.json')
    assert admission['checker_sha256']==sha(ROOT/'standalone/check_native_program_admission.py')
    bundle=read(args.rea_bundle);mappings={r['parameters']['address']:r for r in bundle['records'] if r['operation']=='address_to_file_offset'}
    native=read(ROOT/'reconstruction/program_ui/provenance.json');evidence=[]
    for unit in native['units']:
        address=hex(0x10000+unit['start']);item=mappings[address]
        assert item['normalized_result']['file_offset']==unit['file_offset']
        assert item['subject']['digest']['sha256']==native['original_sha256']
        assert sha(OUT/(Path(unit['file']).stem+'.bin'))==unit['sha256']
        evidence.append(dict(address=address,file_offset=unit['file_offset'],mapping_evidence_id=item['evidence_id'],function_evidence_id=unit['rea_evidence_id']))
    failures=[]
    for label in args.failed_label:
        failed=read(OUT/'runs'/label/'result.json');assert not failed['passed']
        failures.append(dict(label=label,result_sha256=sha(OUT/'runs'/label/'result.json'),
            cases=[dict(port=c['port'],flow=c['flow'],checks=c['checks'],tx_hex=c['tx_hex'],expected_tx_hex=c['expected_tx_hex']) for c in failed['cases']]))
    result=dict(passed=True,component_only=True,whole_application_gates_closed=[],
        runtime_external_commands_enabled=False,build_original_inputs=[],native_ui_bytes=manifest['native_ui_bytes'],
        units=manifest['units'],sources=manifest['sources'],binary_sha256=manifest['binary_sha256'],
        DOS_cases=8,DOS_assertions=sum(c['assertions'] for c in run['cases']),
        linked_admission_cases=13,linked_admission_sha256=sha(OUT/'admission.json'),
        linked_admission_checker_sha256=admission['checker_sha256'],
        source_reproduced_products=len(source['products']),source_proof_sha256=sha(proof_folder/'result.json'),
        DOS_report_sha256=sha(folder/'result.json'),DOS_checker_sha256=run['checker_sha256'],
        source_checker_sha256=source['checker_sha256'],recorder_sha256=sha(Path(__file__)),
        nix_inputs={name:sha(ROOT/name) for name in ('nix/flake.nix','nix/flake.lock')},
        evidence={str(path.relative_to(ROOT)):sha(path) for path in (folder/'result.json',
            folder/'manifest.json',proof_folder/'result.json',proof_folder/'build.log',OUT/'admission.json')},
        retained_REA_bundle=dict(path=str(args.rea_bundle),sha256=sha(args.rea_bundle)),REA_evidence=evidence,
        retained_failures=failures,
        limitations=['Composed component, not yet linked to ASPECT VM/renderer/parent leases or the terminal application controller.',
            'Maintained BIOS keyboard platform binds native WAIT drawing; original macro/mouse/window ownership remains open.',
            'Standard BIOS ROM font/geometry restoration only; arbitrary downloaded fonts and hardware adapter behavior remain unverified.',
            'Modeled nullmodem timing does not establish physical RS-232 Wi-Fi modem acceptance.',
            'ASPECT DOS/RUN/SHELL remain unsupported; complete application requirements remain open.'])
    (ROOT/'docs/validation/native-program.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recorded439 exact UI bytes,8 composed DOS cases/381336 assertions and20 fresh source products.')


if __name__=='__main__':main()
