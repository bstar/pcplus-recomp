#!/usr/bin/env python3
"""Freeze authored conversions and predictions established before VM execution."""
import json
from pathlib import Path
from aspect_conversion_probe import ROOT, COMPILER, corpus, sha

REPORT = 'analysis/aspect-conversions/compiler-02/report.json'
REPORT_SHA = '20ac61d1a13ab75b3e481394769aeccab3d05ea8732fd02d701b775d4f200463'


def main():
    raw = (ROOT / REPORT).read_bytes()
    assert sha(raw) == REPORT_SHA
    report = json.loads(raw)
    assert report['compiler_sha256'] == COMPILER
    assert report['harness_sha256'] == sha((ROOT / 'standalone/aspect_conversion_probe.py').read_bytes())
    predictions = corpus()
    accepted = [c for c in report['cases'] if c['success']]
    rejected = [c for c in report['cases'] if not c['success']]
    assert len(accepted) == 38 and len(rejected) == 4
    vectors = []
    for case in accepted:
        name = case['name']
        assert case['source'] == predictions[name]['source']
        assert predictions[name]['expected'] is not None
        assert sha(case['source'].encode('cp437')) == case['source_sha256']
        assert sha(bytes.fromhex(case['hex'])) == case['asx_sha256']
        vector = {key: case[key] for key in ['name', 'source', 'source_sha256', 'hex', 'asx_sha256']}
        vector.update(source_encoding='cp437', expected=predictions[name]['expected'], dos_excluded=False)
        vectors.append(vector)
    result = dict(compiler_sha256=COMPILER, private_report=REPORT, private_report_sha256=sha(raw),
                  probe_sha256=report['harness_sha256'], freezer_sha256=sha(Path(__file__).read_bytes()),
                  source_encoding='cp437', vectors=vectors,
                  rejected=[{k: c[k] for k in ['name', 'source', 'source_sha256', 'errors']} for c in rejected],
                  expectation_model='Explicit predictions in authored probe before composed execution. Native scanner skips nonnumeric prefix; integer conversion starts at digit or minus immediately followed by digit, parses decimal prefix, wraps32bits, returns low16bits for ATOI. ITOA/LTOA emit signed decimal. No maintained runtime output informs expectations.',
                  scope='42 authored compiler cases,38 accepted; no claim of complete numeric/string/float grammar.')
    out = ROOT / 'standalone/fixtures/aspect_conversion_vectors.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out.relative_to(ROOT), sha(out.read_bytes()))


if __name__ == '__main__':
    main()
