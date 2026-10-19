#!/usr/bin/env python3
"""Original-free selected SET compiler conformance; no runtime support claim."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/aspect'))
import compiler


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    fixture = ROOT / 'standalone/fixtures/aspect_set_compiler_vectors.json'
    corpus = json.loads(fixture.read_text())
    counts = dict(accepted=0, rejected=0, presentation=0)
    for vector in corpus['vectors']:
        source = vector['source']
        expected = bytes.fromhex(vector['hex'])
        assert sha(source.encode('cp437')) == vector['source_sha256']
        assert sha(expected) == vector['asx_sha256']
        assert compiler.compile_source(source) == expected, vector['label']
        counts['accepted'] += 1
        changed = re.sub(r'"[^"\r\n]*"|[a-zA-Z_$][a-zA-Z_0-9$]*',
                         lambda m: m[0] if m[0].startswith('"') else
                         ('value_word' if m[0].lower() == 'setting' else m[0]).upper(), source)
        changed = '\n'.join('\t ' + line + '  ' for line in changed.splitlines())
        assert compiler.compile_source(changed) == expected, vector['label']
        counts['presentation'] += 1
    for vector in corpus['rejected']:
        assert sha(vector['source'].encode('cp437')) == vector['source_sha256']
        try:
            compiler.compile_source(vector['source'])
        except compiler.CompileError:
            counts['rejected'] += 1
        else:
            raise AssertionError(('Original rejected source compiled', vector['label']))
    report = dict(passed=True, original_inputs=[], counts=counts,
                  compiler_sha256=sha(Path(compiler.__file__).read_bytes()),
                  checker_sha256=sha(Path(__file__).read_bytes()),
                  fixture_sha256=sha(fixture.read_bytes()),
                  scope='Host compiler grammar/emission only; DOS runtime SET support remains limited to WHENCASE.')
    out = ROOT / 'build/aspect-set-compiler'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('SET compiler:', counts, 'PASS')


if __name__ == '__main__':
    main()
