#!/usr/bin/env python3
"""Private original-compiler oracle for authored CONNECTED operand grammar."""
import json
from pathlib import Path
import sys
import aspect_compiler_probe as oracle


def corpus():
    cases = {}
    def add(label, body, declarations='integer i\nlong l\nstring s\n'):
        source = (declarations + 'proc main\n' + body + '\nendproc\n').replace('\n', '\r\n')
        cases['C'+str(len(cases))] = (label, source)
    for label, body in [
        ('integer value', 'i=connected'), ('mixed case', 'i=CoNnEcTeD'),
        ('comparison', 'if connected == 128\ni=1\nendif'),
        ('boolean branch', 'if connected\ni=1\nendif'),
        ('numeric command', 'itoa connected s'), ('pause operand', 'pause connected'),
        ('repeated expression', 'i=connected+connected'), ('parenthesized', 'i=(connected)'),
        ('promoted long', 'l=connected+1L'), ('readonly assignment', 'connected=1'),
        ('not a command', 'connected'), ('not a function', 'i=connected()'),
        ('wrong string type', 'strcpy s connected'),
        ('similar identifier', 'integer connectedx\nconnectedx=7\ni=connectedx')]:
        add(label, body)
    for kind in ('integer', 'long', 'float', 'string'):
        add('reserved local '+kind, kind+' connected')
        add('reserved global '+kind, 'i=0', kind+' connected\ninteger i\n')
    return cases


def main():
    cases = corpus()
    oracle.corpus = lambda: {name: source.encode('cp437') for name, (_, source) in cases.items()}
    oracle.main()
    out = Path(sys.argv[sys.argv.index('--output')+1]).resolve()
    result = json.loads((out/'report.json').read_text())
    rows = []
    for case in result['cases']:
        label, source = cases[case['name']]
        assert oracle.digest(source.encode('cp437')) == case['source_sha256']
        rows.append(dict(label=label, source=source, source_sha256=case['source_sha256'],
                         success=case['success'], **({'hex': case['hex']} if case['success'] else {})))
    (out/'fixture.json').write_text(json.dumps(dict(compiler_sha256=result['compiler_sha256'],
        probe_sha256=oracle.digest(Path(__file__).read_bytes()), cases=rows,
        scope=__doc__+' Original compiler executes in DOS; generated ASX is never executed.'), indent=2)+'\n')


if __name__ == '__main__':
    main()
