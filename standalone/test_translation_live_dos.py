#!/usr/bin/env python3
"""Actual DOS startup XLT selection, main receive mapping and raw TX/parser."""
import hashlib
import json
from pathlib import Path
from test_connection_dos import run, ROOT, BINARY


def main():
    mapping = bytearray(range(256))
    mapping[ord('Q')] = 27
    mapping[ord('x')] = ord('y')
    mapping[ord('[')] = ord('!')
    banner = b'Q[2JQ[HFIRST BYTE SAFEQ[6nQ[0cQ[2;1HxQ[6n'
    cases = []
    proof = run('xlt-mapped-controls', 'success', 'p3000 x p500 a-x',
                arguments='@D:\\TEST.PRM /D:CaseTest:23 /X:D:\\TEST.XLT',
                files={'TEST.XLT': bytes(mapping)}, banner=banner)
    folder = ROOT / 'build/connection-dos/xlt-mapped-controls'
    wire = (folder / 'serial.bin').read_bytes()
    screen = (folder / 'SCREEN.BIN').read_bytes()
    proof['checks'].update(mapped_character=screen[160:162] == b'y\x07',
                          raw_continuation_and_reply=b'\x1b[2;2R' in wire,
                          typed_x_stays_x=b'\x1b[2;2Rx' in wire and b'\x1b[2;2Ry' not in wire)
    proof['passed'] = all(proof['checks'].values())
    (folder / 'result.json').write_text(json.dumps(proof, indent=2) + '\n')
    assert proof['passed'], proof
    cases.append(proof)
    cases.append(run('xlt-identity', 'success', 'p2500 a-x',
                     arguments='@D:\\TEST.PRM /D:CaseTest:23 /X:D:\\TEST.XLT',
                     files={'TEST.XLT': bytes(range(256))}))
    cases.append(run('xlt-disabled', 'success', 'p2500 a-x',
                     files={'TEST.XLT': bytes([ord('Z')]) * 256}))
    for name, data in [('empty', b''), ('short', bytes(255)), ('suffix', bytes(257)), ('missing', None)]:
        cases.append(run('xlt-reject-' + name, 'reject', 'p500 a-x', expected=7,
                         arguments='/X:D:\\TEST.XLT',
                         files={'TEST.XLT': data} if data is not None else None))
    assert all(case['passed'] for case in cases)
    sources = [__file__, str(ROOT / 'standalone/test_connection_dos.py'),
               str(ROOT / 'standalone/test_terminal.py')]
    result = {'passed': True, 'binary_sha256': hashlib.sha256(BINARY.read_bytes()).hexdigest(),
              'cases': cases,
              'sources': {str(Path(p).resolve().relative_to(ROOT)):
                          hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
              'scope': 'Actual DOS main-loop input mapping, native raw parser continuation and replies, unchanged typed output/modem commands, identity/disabled selection and startup rejection with hardware restoration. Synthetic files/loopback modem only.'}
    out = ROOT / 'build/terminal/translation-dos-checks.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print('Live XLT DOS:', len(cases), 'cases passed')


if __name__ == '__main__':
    main()
