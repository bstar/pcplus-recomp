#!/usr/bin/env python3
"""Freeze independent compiler-emission cases and source-level predictions."""
import json
from pathlib import Path
from aspect_compiler_validation_probe import ROOT, COMPILER, sha, corpus

REPORT = 'analysis/aspect-compiler-validation/compiler-01/report.json'
REPORT_SHA = '3812326cc6dad73f98c4222e1e7879537f95343bc26f59abde3aff4f36aad0c0'
EXPECTED = {
    'NESTSUB': {'integer4': 65532}, 'NESTMUL': {'integer4': 65531},
    'NESTDIV': {'integer4': 65531}, 'NESTMOD': {'integer4': 0},
    'NESTCMP': {'integer4': 1}, 'NESTADD': {'integer4': 14},
    'BOOLAND': {'integer4': 9}, 'BOOLOR': {'integer4': 7},
    'BOOLA11': {'integer4': 7}, 'BOOLO00': {'integer4': 9},
    'BOOLMIX': {'integer4': 7}, 'BOOLVAR': {'integer4': 7},
    'NEWFRAME': {'integer0': 47}, 'NEWSTR': {'string0': 'WIFI MODEM'},
    'NEWCONV': {'long0': 4294843840, 'string0': '-123456'},
}


def main():
    raw = (ROOT / REPORT).read_bytes()
    assert sha(raw) == REPORT_SHA
    report = json.loads(raw)
    assert report['compiler_sha256'] == COMPILER
    assert report['harness_sha256'] == sha((ROOT / 'standalone/aspect_compiler_validation_probe.py').read_bytes())
    cases = corpus()
    assert len(report['cases']) == 15
    assert set(c['name'] for c in report['cases']) == set(EXPECTED)
    vectors = []
    for case in report['cases']:
        name = case['name']
        assert case['success'] and case['source'] == cases[name]['source']
        assert sha(case['source'].encode('cp437')) == case['source_sha256']
        assert sha(bytes.fromhex(case['hex'])) == case['asx_sha256']
        vector = {key: case[key] for key in ['name', 'source', 'source_sha256', 'hex', 'asx_sha256']}
        vector.update(source_encoding='cp437', expected=EXPECTED[name], dos_excluded=False)
        vectors.append(vector)
    result = dict(compiler_sha256=COMPILER, private_report=REPORT, private_report_sha256=sha(raw),
                  probe_sha256=report['harness_sha256'], freezer_sha256=sha(Path(__file__).read_bytes()),
                  source_encoding='cp437', vectors=vectors, rejected=[],
                  expectation_model='Independent arithmetic, signed division/remainder, conventional boolean precedence and explicit string predictions fixed before composed execution. Nested operands require distinct expression staging slots.',
                  scope='15 novel emission cases beyond the previous222 fixtures; no complete compiler claim.')
    out = ROOT / 'standalone/fixtures/aspect_compiler_validation_vectors.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
