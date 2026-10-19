#!/usr/bin/env python3
"""Bind the selected SET emission checkpoint to source and checked reports."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    reports = {}
    for name in ('aspect-set-compiler', 'aspect-compiler', 'aspect-when-compiler'):
        path = ROOT / 'build' / name / 'checks.json'
        report = json.loads(path.read_text())
        assert report['success'] if name == 'aspect-compiler' else report['passed']
        assert report['compiler_sha256'] == sha(ROOT / 'src/aspect/compiler.py')
        reports[str(path.relative_to(ROOT))] = dict(sha256=sha(path), result=report)
    files = ('src/aspect/compiler.py', 'standalone/freeze_aspect_set_compiler.py',
             'standalone/test_aspect_set_compiler.py',
             'standalone/fixtures/aspect_set_compiler_vectors.json',
             'docs/ASPECT_SET_COMPILER.md', 'standalone/record_aspect_set_compiler.py')
    fixture = json.loads((ROOT / files[3]).read_text())
    assert len(fixture['vectors']) == 33 and len(fixture['rejected']) == 19
    result = dict(schema='aspect-set-compiler-validation-v1', passed=True,
                  scope='Selected host compiler grammar/encoding. DOS runtime SET support remains WHENCASE only; full application gates stay open.',
                  original_inputs=[], sources={f: sha(ROOT / f) for f in files},
                  oracle=dict(compiler_sha256=fixture['compiler_sha256'],
                              report_sha256=fixture['private_report_sha256'],
                              followup_report_sha256=fixture['private_followup_report_sha256']),
                  reports=reports)
    out = ROOT / 'docs/validation/aspect-set-compiler.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
