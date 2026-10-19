#!/usr/bin/env python3
"""Original file-command and FGETS_CRLF grammar, reproduced without originals."""
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source, CompileError


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    accepted = rejected = 0
    fixtures = {}
    for name in ('aspect_script_file_compiler_vectors.json', 'aspect_script_file_setting_vectors.json'):
        path = ROOT / 'standalone/fixtures' / name
        fixtures[str(path.relative_to(ROOT))] = sha(path)
        for case in json.loads(path.read_text())['cases']:
            assert hashlib.sha256(case['source'].encode('cp437')).hexdigest() == case['source_sha256']
            try:
                wire = compile_source(case['source'])
            except CompileError:
                assert not case['success'], case['label']
                rejected += 1
            else:
                assert case['success'] and wire == bytes.fromhex(case['hex']), case['label']
                assert hashlib.sha256(wire).hexdigest() == case['asx_sha256']
                accepted += 1
    assert (accepted, rejected) == (126, 119)
    validation = ROOT / 'standalone/fixtures/aspect_script_file_validation_vectors.json'
    invalid = json.loads(validation.read_text())['cases']
    for case in invalid:
        try:
            compile_source(case['source'])
        except CompileError:
            pass
        else:
            raise AssertionError(case['name'])
    out = ROOT / 'build/aspect-script-files'
    out.mkdir(parents=True, exist_ok=True)
    report = dict(passed=True, accepted=accepted, rejected=rejected, fixtures=fixtures,
                  additional_invalid=len(invalid), validation_fixture_sha256=sha(validation),
                  checker_sha256=sha(Path(__file__)), compiler_sha256=sha(ROOT / 'src/aspect/compiler.py'),
                  original_inputs=[], scope='245 frozen authored original compiler cases: exact accepted ASX and matching rejection for13 file commands and FGETS_CRLF SET/FETCH. Runtime/filesystem behavior verified separately.')
    (out / 'compiler-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Script-file compiler:', accepted, 'accepted,', rejected, 'rejected PASS')


if __name__ == '__main__':
    main()
