#!/usr/bin/env python3
"""Exercise bank-linked terminal connect/redial on8086 with valid synthetic settings."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

import test_connection_dos as terminal
from modem_fixtures import fixture

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', type=Path, required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    parent = args.terminal.resolve()
    assert parent.is_relative_to(ROOT / 'build') and re.fullmatch('[a-z0-9-]+', args.label)
    manifest = json.loads((parent / 'manifest.json').read_text())
    assert manifest['experimental_phone_log_bank']
    binary = parent / 'TERMINAL.EXE'
    assert sha(binary) == manifest['binary_sha256']
    terminal.BINARY = binary
    sources = dict(manifest['sources'])
    names = ['standalone/test_phone_log_bank_terminal.py', 'standalone/test_connection_dos.py',
             'standalone/modem_fixtures.py', 'standalone/terminal_config_fixtures.py',
             'standalone/directory_test_support.py', 'standalone/test_terminal.py']
    sources.update({name: sha(ROOT / name) for name in names})
    settings = bytearray(fixture(timeout=5))
    if manifest.get('experimental_mouse'):
        struct.pack_into('<HH', settings, 0x4e4, 8, 4)
    results, artifacts = [], {}
    for mode, keys in [('success', 'p4000 a-x'), ('redial', 'p3500 a-d p3500 a-x')]:
        if manifest.get('special_edition'):
            keys = 'p900 enter ' + keys
        name = args.label + '-' + mode
        folder = ROOT / 'build/connection-dos' / name
        assert not folder.exists(), folder
        results.append(terminal.run(name, mode, keys, prm=bytes(settings), cpu='8086'))
        artifacts.update({str(path.relative_to(ROOT)): sha(path) for path in folder.rglob('*') if path.is_file()})
    checks = dict(actual_DOS_cases=all(row['passed'] for row in results),
                  inputs_unchanged=all(sha(ROOT / name) == digest for name, digest in sources.items()),
                  terminal_unchanged=sha(binary) == manifest['binary_sha256'])
    out = ROOT / 'build/phone-log-bank-terminal' / args.label
    out.mkdir(parents=True, exist_ok=False)
    report = dict(passed=all(checks.values()), checks=checks, cases=results, sources=sources,
                  terminal_sha256=sha(binary), artifacts=artifacts,
                  scope='Actual8086 synthetic-modem connect/banner and busy/redial with the bank linked, valid8/4 mouse settings and restored hardware. Logger event integration remains disabled.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(checks, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
