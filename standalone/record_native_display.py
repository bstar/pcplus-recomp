#!/usr/bin/env python3
"""Publish bounded native display evidence without original images or captures."""
import argparse,json,re
from pathlib import Path
from build_native_display import ROOT,OUT,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True)
    parser.add_argument('--original-comparison',action='store_true')
    parser.add_argument('--rea-bundle',type=Path)
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    folder=OUT/'runs'/args.label;report=json.loads((folder/'result.json').read_text())
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert report['passed'] and not report['timed_out'] and report['checks']==13045
    assert report['binary_sha256']==manifest['binary_sha256']==sha(folder/'DISPLAY.EXE')==sha(OUT/'DISPLAY.EXE')
    assert report['manifest_sha256']==sha(folder/'manifest.json')==sha(OUT/'manifest.json')
    assert sha(folder/'VIDEO.COM')==manifest['child_sha256']
    assert report['checker_sha256']==sha(ROOT/'standalone/test_native_display_dos.py')
    for p,h in report['artifacts'].items():assert sha(folder/p)==h,p
    for p,h in {**manifest['sources'],**manifest['process_sources']}.items():assert sha(ROOT/p)==sha(folder/'sources'/p)==h,p
    cpu_path=OUT/('cpu-original.json' if args.original_comparison else 'cpu.json')
    cpu=json.loads(cpu_path.read_text());assert cpu['passed'] and cpu['cases']==963
    assert cpu['manifest_sha256']==sha(OUT/'manifest.json')
    assert cpu['checker_sha256']==sha(ROOT/'standalone/check_native_display.py')
    if args.original_comparison:assert cpu['original_comparisons']==963
    result=dict(passed=True,component_only=True,whole_application_gates_closed=[],
        build_original_inputs=[],runtime_external_commands_enabled=False,
        native_display_bytes=manifest['native_display_bytes'],units=manifest['units'],
        sources=manifest['sources'],process_manifest_sha256=manifest['process_manifest_sha256'],
        binary_sha256=manifest['binary_sha256'],DOS_assertions=report['checks'],
        CPU_cases=cpu['cases'],analyst_original_comparisons=cpu['original_comparisons'],
        checks=['Exact40x25/color80x25/mono80x25 and VGA80x50 cell restoration through real far heap.',
            'Owned DOS graphics child exit37, geometry mismatch retains snapshot, matching-mode retry restores and frees.',
            'Allocation failure leaves video untouched; BUSY/repeated restore/discard do not double-free.',
            'Graphics/nonzero-page/oversized BDA geometry reject before snapshot allocation.',
            'Raw geometry byte stores, row29 clamp, sixteen-bit overflow and native even-byte copy truncation.',
            'Declared CGA ports prove blank/copy/unblank ordering and characterize an unbounded no-retrace wait.'],
        limitations=manifest['limitations']+['No BIOS mode/font/cursor restoration, WAIT/NOCLEAR lifecycle, production state or UART owner is enabled by this component.'],
        evidence={str(p.relative_to(ROOT)):sha(p) for p in (folder/'result.json',folder/'manifest.json',folder/'CHECKS.TXT',cpu_path)},
        recorder_sha256=sha(Path(__file__)),DOS_checker_sha256=report['checker_sha256'],CPU_checker_sha256=cpu['checker_sha256'])
    if args.rea_bundle:
        bundle=json.loads(args.rea_bundle.read_text())
        mappings={r['parameters']['address']:r for r in bundle['records'] if r['operation']=='address_to_file_offset'}
        result['REA_mapping_evidence']=[]
        for unit in manifest['units']:
            address=hex(0x10000+unit['start']);item=mappings[address]
            assert item['raw_result']['file_offset']==unit['file_offset']
            assert item['subject']['digest']['sha256']==json.loads((ROOT/'reconstruction/program_display/provenance.json').read_text())['original_sha256']
            result['REA_mapping_evidence'].append(dict(address=address,file_offset=unit['file_offset'],evidence_id=item['evidence_id']))
        result['retained_REA_bundle']=dict(path=str(args.rea_bundle),sha256=sha(args.rea_bundle))
    (ROOT/'docs/validation/native-display.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recorded310 exact display bytes,963 CPU cases and13045 actual DOS assertions; full controller remains open.')


if __name__=='__main__':main()
