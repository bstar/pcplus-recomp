#!/usr/bin/env python3
"""Actual native SET/status compositions using the existing passive DOS observer.
Each run requires frozen products and a fresh output label; no product rebuild.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
import test_aspect_status_dos as status

ROOT = status.ROOT
OUT = ROOT / 'build/aspect-set-status-dos'
BASE_DEFINITIONS = status.definitions


def definitions():
    base = BASE_DEFINITIONS()[0]
    cases = []
    for name, settings, half in (
        ('DISPLAY-off-still-refreshes', 'set display off\n', False),
        ('MESSAGE-and-KEYS-state', 'set msg_crlf off\nset keys on\n', False),
        ('line-policy-paced-transmit', 'set pausechar 65\nset waitcase on\nset txpace 37\n', False),
        ('RXDATA-native-gate', 'set rxdata on\nset rxdata off\n', False),
        ('DUPLEX-half-snapshot', 'set duplex half\n', True),
        ('DISPLAY-off-DUPLEX-half', 'set display off\nset duplex half\n', True),
    ):
        case = dict(base, name=name, when_value=0)
        # Only the first PAUSE is sampled. Restore FULL before sending the
        # synthetic password, preserving the existing independent wire/CPR
        # predictions. There is no second child PAUSE to overwrite the sample.
        restore = 'set duplex full\n' if half else ''
        case['source'] = ('proc main\nwaitfor "LOGIN:" 5\n' + settings +
                          'pause 1\n' + restore +
                          'transmit $D_PWORD\ntransmit "^M"\nendproc\n')
        if half:
            rows = []
            for row in case['expected_status_rows']:
                value = bytearray(row)
                cell = row[::2].index(b'FDX')
                value[cell*2] = ord('H')
                rows.append(bytes(value))
            case['expected_status_rows'] = rows
        cases.append(case)
    return cases


def main():
    if '--prepare' in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument('--prepare', action='store_true')
        parser.add_argument('--label', required=True)
        args = parser.parse_args()
        assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
        folder = OUT / args.label
        folder.mkdir(parents=True, exist_ok=False)
        cases = definitions()
        for case in cases:
            status.renderer.compile_source(case['source'])
        (folder / 'predictions.json').write_text(json.dumps(status.encode(cases), indent=2)+'\n')
        print('Prepared', len(cases), 'native SET/status cases; no product execution')
        return 0
    observer_source = Path(status.__file__)
    status.OUT = OUT
    status.definitions = definitions
    status.__file__ = __file__
    result = status.run_product()
    # This binding supplements the reused parser/observer and fixture hashes.
    label = sys.argv[sys.argv.index('--label')+1]
    assert re.fullmatch(r'[A-Za-z0-9_-]+', label)
    folder = OUT / label
    path = folder / 'checks.json'
    report = json.loads(path.read_text())
    report['reused_status_checker_sha256'] = hashlib.sha256(observer_source.read_bytes()).hexdigest()
    report['scope'] = ('Actual native SET handlers and parent STATUS with passive child-PAUSE row '
                       'sampling. DISPLAY OFF does not suppress status; explicit HALF projects HDX '
                       'without parent duplex adoption. FULL is restored before password transmission. '
                       'Other setters execute but their broader consumers require separate evidence. '
                       'No physical carrier/timing or complete application claim.')
    path.write_text(json.dumps(report, indent=2)+'\n')
    return result


if __name__ == '__main__':
    raise SystemExit(main())
