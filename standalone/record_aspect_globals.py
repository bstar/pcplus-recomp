#!/usr/bin/env python3
"""Freeze global-string diagnostic evidence without original binaries or data."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    paths = ['build/aspect-globals/manifest.json', 'build/aspect-globals/checks.json',
             'build/aspect-globals/checks-native.json']
    manifest, checks, native = [json.loads((ROOT/p).read_text()) for p in paths]
    assert checks['passed'] and native['passed']
    assert checks['original_inputs'] == manifest['original_inputs'] == []
    assert checks['cpu_cases'] == native['optional_original']['paired_cpu_cases'] == 616
    assert native['optional_original']['exact_bytes'] == 101
    assert checks['flat_sha256'] == native['flat_sha256'] == manifest['flat_sha256']
    assert checks['binary_sha256'] == native['binary_sha256'] == manifest['binary_sha256']
    sources = {**manifest['sources'], 'standalone/check_aspect_globals.py': checks['check_sha256']}
    for rel, digest in sources.items():
        assert sha(ROOT/rel) == digest, rel
    sources['standalone/record_aspect_globals.py'] = sha(Path(__file__).resolve())
    result = dict(passed=True, sources=sources, diagnostic=manifest, source_only_checks=checks,
        optional_native_comparison=native['optional_original'],
        local_evidence={p: sha(ROOT/p) for p in paths},
        limitations=['Recovered native allocation/release primitives, not a complete loader or VM.',
                     'DOS and CPU use declared heap/error callback substitutes.',
                     'No original heap manager, error UI or nonlocal unwind is exercised.',
                     'No rollback, bounds validation or idempotent release is implied.'])
    out = ROOT/'docs/validation/aspect-globals.json'
    out.write_text(json.dumps(result, indent=2)+'\n')
    print(f'Recorded {out.relative_to(ROOT)}')

if __name__ == '__main__':
    main()
