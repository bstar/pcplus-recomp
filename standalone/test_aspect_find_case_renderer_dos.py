#!/usr/bin/env python3
"""Receive an owned peer's text, then use native FIND/CASE to choose login output.
Actual parent queries/rendering, child FILE/heap and existing passive observer.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
import test_aspect_when_renderer_dos as when

ROOT = when.ROOT
OUT = ROOT/'build/aspect-find-case-renderer-dos'


def definitions():
    header = when.ESC+b'[2J'+when.ESC+b'[HFIRST BYTE SAFE'+when.renderer.QUERY+when.renderer.DA
    frame = header+b'LOGIN:SyNcHrOnEt\r'+when.ESC+b'[1;16H'
    cases = []
    for name, setting, selection in (
        ('FIND-insensitive-received-line', 'set findcase off\n',
         'find banner, "SYNCHRONET"\nif found\ntransmit $D_PWORD\nelse\ntransmit "BAD"\nendif\n'),
        ('FIND-sensitive-received-line', 'set findcase on\n',
         'find banner, "SYNCHRONET"\nif found\ntransmit "BAD"\nelse\ntransmit $D_PWORD\nendif\n'),
        ('CASE-insensitive-received-line', 'set switchcase off\n',
         'switch banner\ncase "SYNCHRONET"\ntransmit $D_PWORD\nendcase\ndefault\ntransmit "BAD"\nendcase\nendswitch\n'),
        ('CASE-sensitive-received-line', 'set switchcase on\n',
         'switch banner\ncase "SYNCHRONET"\ntransmit "BAD"\nendcase\ndefault\ntransmit $D_PWORD\nendcase\nendswitch\n'),
    ):
        source = ('string banner\nproc main\ntransmit "READY^M"\nwaitfor "LOGIN:" 5\n'
                  'rget banner\n'+setting+selection+'transmit "^M"\npause 1\nendproc\n')
        cases.append(dict(name=name, source=source, banner=b'', success=True,
                          events=[], send_end=False, end_delay_seconds=0,
                          ready_stream=frame, post=when.renderer.QUERY,
                          post_reply=when.ESC+b'[1;16R', screen=[(0,0,'FIRST BYTE SAFE')],
                          expected_selection=b'Synth42\r'))
    return cases


def main():
    if '--prepare' in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument('--prepare', action='store_true')
        parser.add_argument('--label', required=True)
        args = parser.parse_args()
        assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
        folder = OUT/args.label
        folder.mkdir(parents=True, exist_ok=False)
        cases = definitions()
        for case in cases:
            when.renderer.compile_source(case['source'])
        (folder/'predictions.json').write_text(json.dumps(when.encoded_cases(cases), indent=2)+'\n')
        print('Prepared', len(cases), 'FIND/CASE received-line cases')
        return 0
    reused = Path(when.__file__)
    when.OUT = OUT
    when.definitions = definitions
    when.__file__ = __file__
    result = when.run_product()
    label = sys.argv[sys.argv.index('--label')+1]
    path = OUT/label/'checks.json'
    report = json.loads(path.read_text())
    predictions = {c['name']: c for c in definitions()}
    for case in report['cases']:
        folder = OUT/label/case['case']
        wire = (folder/'serial.bin').read_bytes()
        case['checks']['native_selection_password_once'] = wire.count(predictions[case['case']]['expected_selection']) == 1
        case['checks']['no_wrong_selection'] = b'BAD' not in wire
        case['passed'] = all(case['checks'].values())
        (folder/'result.json').write_text(json.dumps(case, indent=2)+'\n')
    report.update(passed=all(c['passed'] for c in report['cases']),
                  reused_when_checker_sha256=hashlib.sha256(reused.read_bytes()).hexdigest(),
                  scope='Actual source-built parent/child with READY-gated owned peer. RGET consumes '
                  'mixed-case text received through the UART; native FIND/CASE select the synthetic '
                  'password under each sensitivity mode. Actual DA/CPR, status, history, parent '
                  'ownership and keyboard/hardware resumption are checked. No peer ASX interpreter '
                  'or parser/reply substitute. No real BBS or physical modem claim.')
    path.write_text(json.dumps(report, indent=2)+'\n')
    assert report['passed']
    return result


if __name__ == '__main__':
    raise SystemExit(main())
