#!/usr/bin/env python3
"""Freeze native-flow and real-file evidence, excluding all original artifacts."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    flow_paths=[f'build/aspect-flow/{p}.json' for p in ('manifest','checks','checks-native')]
    file_paths=[f'build/aspect-file/{p}.json' for p in ('manifest','checks')]
    flow,checks,native=[json.loads((ROOT/p).read_text()) for p in flow_paths]
    file_manifest,file_checks=[json.loads((ROOT/p).read_text()) for p in file_paths]
    assert checks['passed'] and native['passed'] and file_checks['passed']
    assert flow['original_inputs']==checks['original_inputs']==file_manifest['original_inputs']==file_checks['original_inputs']==[]
    assert flow['binary_sha256']==checks['binary_sha256']==native['binary_sha256']
    assert checks['cpu_scenarios']==native['optional_original']['paired_cpu_scenarios']==457
    assert native['optional_original']['original_sha256']==ORIGINAL
    assert native['optional_original']['exact_flow_bytes']==sum(u['bytes'] for u in flow['units'])==330
    assert native['optional_original']['exact_stack_bytes']==197 and native['optional_original']['exact_copy_bytes']==72
    assert checks['check_sha256']==native['check_sha256']
    for unit in flow['units']:
        assert checks['units'][unit['name']]==native['units'][unit['name']]==unit['sha256']
    assert file_manifest['binary_sha256']==file_checks['binary_sha256']
    assert file_checks['manifest_sha256']==sha(ROOT/file_paths[0])
    assert file_checks['DOS_fixture_sha256']==file_checks['host_fixture_sha256']
    sources={}
    for manifest,report,name in ((flow,checks,'flow'),(file_manifest,file_checks,'file')):
        current={**manifest['sources'],f'standalone/check_aspect_{name}.py':report['check_sha256']}
        for path,digest in current.items():
            assert sha(ROOT/path)==digest,path
            assert path not in sources or sources[path]==digest
            sources[path]=digest
    local={p:sha(ROOT/p) for p in flow_paths+file_paths}
    carrier_path=ROOT/'analysis/pcplus-overlay-entry-images/manifest.json'
    carrier_manifest=json.loads(carrier_path.read_text());assert carrier_manifest['original_sha256']==ORIGINAL
    carrier=next(i for i in carrier_manifest['images'] if i['overlay']==16)
    assert sha(carrier_path.parent/carrier['file'])==carrier['sha256']
    region=next(r for r in carrier['source_ranges'] if r['role']=='overlay-16')
    for unit in flow['units']:
        assert region['relative_address']<=unit['start']<unit['end_exclusive']<=region['relative_address']+region['bytes']
        assert unit['source_file_start']==region['source_file_offset']+unit['start']-region['relative_address']
    local[str(carrier_path.relative_to(ROOT))]=sha(carrier_path)
    evidence=[]
    for address in ('d1f2','d27d','d282','d287','d2d6','d2f9','d307','d310','d317','d339','d349','d352','e129','e176'):
        rel=f'analysis/pcplus-overlay-anchored-16/functions/0x1{address}-asm.json'
        tool_result=json.loads((ROOT/rel).read_text())
        record=json.loads(next(c['text'] for c in tool_result['content'] if c['type']=='text'))
        assert record['subject']['digest']['sha256']==carrier['sha256']
        local[rel]=sha(ROOT/rel)
        evidence.append(dict(evidence_id=record['evidence_id'],parameters=record['parameters'],
            subject_sha256=carrier['sha256'],scope='Retained static assembly on synthetic carrier; never executed'))
    sources['standalone/record_aspect_file.py']=sha(Path(__file__).resolve())
    result=dict(passed=True,sources=sources,local_evidence=local,
        native_flow=dict(manifest=flow,source_only_checks=checks,optional_original=native['optional_original']),
        real_file=dict(manifest=file_manifest,checks=file_checks),retained_rea=evidence,
        limits=['Native handlers preserve unchecked IO and stack/frame/local-count semantics in isolation.',
          'Maintained file callbacks abort short operand reads and failed positions through actual native abort/longjmp.',
          'The real-file fixture invokes native routines directly; no opcode loop or complete script interpreter exists here.',
          'Error abort does not roll back already changed depth/stack; the diagnostic owner resets state and closes real files explicitly.',
          'No full compiler, expressions, loader owner, recorder, live terminal integration or physical hardware proof.'])
    out=ROOT/'docs/validation/aspect-file.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(f'Recorded {out.relative_to(ROOT)}')

if __name__=='__main__':main()
