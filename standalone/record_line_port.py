#!/usr/bin/env python3
"""Bind the accepted selector component results; no deployment or runtime claim."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/line-port'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths = [OUT / p for p in ('manifest.json', 'selector-results.json',
                              'dos-results.json', 'source-proof/result.json')]
    records = [json.loads(p.read_text()) for p in paths]
    manifest, selector, dos, proof = records
    assert all(r['passed'] for r in (selector, dos, proof))
    assert selector['cases'] == 262144 and dos['vectors'] == 40
    assert manifest == selector['manifest']
    assert manifest['original_inputs'] == []
    assert manifest['exe_sha256'] == dos['binary_sha256'] == sha(OUT / 'LINEPORT.EXE')
    assert proof['exact_outputs']['LINEPORT.EXE'] == dos['binary_sha256']
    assert proof['exact_outputs']['key.bin'] == manifest['flat_sha256'] == sha(OUT / 'key.bin')
    for record in (manifest, selector, proof):
        for source, digest in record['sources'].items():
            assert sha(ROOT / source) == digest, source
    sources = list((ROOT / 'reconstruction/line_port').glob('*'))
    sources += [ROOT / 'standalone' / p for p in ('build_line_port.py',
        'check_line_port.py', 'line_port_host.asm', 'test_line_port_dos.py',
        'prove_line_port_source.py', 'record_line_port.py')]
    sources += [ROOT / 'reconstruction/uart/encodings.inc', ROOT / 'docs/LINE_PORT_RECOVERY.md']
    sources = [p for p in sources if p.is_file()]
    result = {
        'component_verified': True, 'application_integrated': False,
        'physical_runtime_verified': False, 'installed_package_changed': False,
        'sources': {str(p.relative_to(ROOT)): sha(p) for p in sorted(sources)},
        'receipts': {str(p.relative_to(ROOT)): sha(p) for p in paths},
        'summary': {'exact_bytes': 414, 'instructions': 135,
                    'exhaustive_cases': selector['cases'], 'dos_8086_vectors': dos['vectors'],
                    'isolated_source_files': len(proof['sources'])},
        'limitations': ['Bell/quiesce hardware services are recording boundaries.',
            'Popup rendering, checked save/apply and live terminal integration remain open.',
            'The installed RBADE091 payload and its physical acceptance are separate.']}
    (ROOT / 'docs/validation/line-port-recovery.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Recorded Line/Port component receipts; application/physical gates remain open')


if __name__ == '__main__':
    main()
