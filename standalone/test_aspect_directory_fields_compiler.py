#!/usr/bin/env python3
"""Match the maintained host compiler to frozen original directory-field outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src/aspect'))
from compiler import CompileError, compile_source


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dos', type=Path)
    p.add_argument('--protocol', action='store_true')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    feature='proto' if a.protocol else 'fields'
    fixture = ROOT/('standalone/fixtures/aspect_directory_'+feature+'_compiler_vectors.json')
    corpus = json.loads(fixture.read_text())
    accepted = 0
    for case in corpus['cases']:
        assert hashlib.sha256(case['source'].encode('cp437')).hexdigest() == case['source_sha256']
        try:
            data = compile_source(case['source'])
            success = True
        except CompileError:
            success = False
        assert success == case['success'], case['label']
        if success:
            assert data == bytes.fromhex(case['hex']), case['label']
            accepted += 1
    count,good=(10,6) if a.protocol else (80,48)
    assert len(corpus['cases']) == count and accepted == good
    receipts = {}
    if a.dos:
        checks = json.loads((a.dos/'checks.json').read_text())
        manifest = json.loads((a.dos/'manifest.json').read_text())
        assert checks['passed'] and checks['original_inputs'] == manifest['original_inputs'] == []
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        assert checks['binary_sha256'] == manifest['binary_sha256'] == digest(a.dos/'ASPCOMP.EXE')
        for path, expected in manifest['sources'].items():
            assert digest(ROOT/path) == expected, path
        assert checks['fixture_sources'][str(fixture.relative_to(ROOT))] == digest(fixture)
        assert checks['case_manifest_sha256'] == digest(a.dos/'cases.json')
        rows = json.loads((a.dos/'cases.json').read_text())
        indexed = {r['source_sha256']: (i, r) for i, r in enumerate(rows)}
        for case in corpus['cases']:
            i, row = indexed[case['source_sha256']]
            assert row['accepted'] == case['success'], case['label']
            if case['success']:
                assert (a.dos/'tests'/f'P{i:05}.ASX').read_bytes() == bytes.fromhex(case['hex'])
        receipts = {str((a.dos/leaf).resolve().relative_to(ROOT)): digest(a.dos/leaf)
                    for leaf in ('checks.json', 'manifest.json', 'cases.json')}
    if a.output:
        assert a.output.resolve().is_relative_to(ROOT/'build') and not a.output.exists()
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(dict(passed=True, original_inputs=[], cases=count,
            accepted=good, rejected=count-good, exact_DOS_bytes=bool(a.dos), receipts=receipts,
            fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
            checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2)+'\n')
    print('PASS',count,'original compiler directory-'+feature+' cases:',good,'accepted,',count-good,'rejected')


if __name__ == '__main__':
    main()
