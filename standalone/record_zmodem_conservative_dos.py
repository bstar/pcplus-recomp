#!/usr/bin/env python3
"""Bind native conservative DOS/lrzsz interoperability and passive wire checks."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lab/bbs'))
from audit_zmodem import audit_batch, scan


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert args.label.replace('-', '').replace('_', '').isalnum()
    cohort = ROOT / 'build/terminal-zmodem-dos' / args.label
    target = args.output.resolve()
    assert target.is_relative_to(ROOT / 'docs/validation') and not target.exists()
    read = lambda path: json.loads(path.read_text())
    manifest_path = ROOT / 'build/terminal/manifest.json'
    manifest = read(manifest_path)
    binary = ROOT / 'build/terminal/TERMINAL.EXE'
    assert manifest['kind'] == 'source-only-interactive-dos-terminal'
    assert sha(binary) == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT) and not name.startswith(('build/', 'analysis/'))
        assert sha(path) == digest, name
    component_path = ROOT / 'docs/validation/zmodem-native-conservative.json'
    component = read(component_path)
    assert component['passed'] and component['native_conservative_offer_accepted']
    assert component['terminal_sha256'] == sha(binary)
    assert component['terminal_manifest_sha256'] == sha(manifest_path)
    report_path = cohort / 'checks.json'
    report = read(report_path)
    assert report['passed'] and report['binary_sha256'] == sha(binary)
    assert {case['case'] for case in report['cases']} == {'rx-default', 'rx-crc16'}
    assert len(report['cases']) == 2
    summaries = []
    captures = {str(report_path.relative_to(ROOT)): sha(report_path)}
    for case in report['cases']:
        folder = cohort / case['case']
        assert read(folder / 'result.json') == case
        assert case['passed'] and all(case['checks'].values()) and not case['errors']
        assert case['binary_sha256'] == sha(binary) and case['receive_credit'] == 256
        assert case['harness_sha256'] == sha(ROOT / 'standalone/test_terminal_zmodem_dos.py')
        assert case['peer_exit'] == 0 and case['sender_helper_sha256'] is None
        assert case['peer_command'][0].startswith('/nix/store/')
        assert Path(case['peer_command'][0]).name == 'sz'
        assert ('-o' in case['peer_command']) == (case['case'] == 'rx-crc16')
        assert case['terminal_arguments'].endswith(' /Z:256')
        assert 'a-r' not in case['keys'] and 'f2' not in case['keys']
        assert (folder / 'BEFORE.BIN').read_bytes() == (folder / 'AFTER.BIN').read_bytes()
        assert (folder / 'BEFORE.BIN').stat().st_size == 42
        assert (folder / 'SCREEN.BIN').stat().st_size == 4000
        assert (folder / 'SCREEN.BIN').read_bytes()[:28:2] == b'AFTER TRANSFER'
        expected = {name: (folder / 'PEER' / name).read_bytes() for name in case['files']}
        assert set(expected) == {'EMPTY.BIN', 'ODD.BIN', 'ALL.BIN'}
        assert expected['EMPTY.BIN'] == b'' and expected['ODD.BIN'] == b'A'
        assert expected['ALL.BIN'] == bytes(range(256)) * 257 + b'\0\x1a\xff@\r'
        assert {path.name for path in (folder / 'RECV').iterdir()} == set(expected)
        for name, content in expected.items():
            assert sha(folder / 'PEER' / name) == case['files'][name]
            assert (folder / 'RECV' / name).read_bytes() == content
        assert not any(path.name.startswith(('PCRX.', 'PCZRX.')) for path in folder.rglob('*'))
        protocol = audit_batch((folder / 'peer.bin').read_bytes(), expected)
        for file in protocol['files']:
            assert file.pop('source') == expected[file['name']]
        data_formats = {event['format'] for event in protocol['events']
                        if event['kind'] == 'header' and event['type'] == 10}
        assert data_formats == ({65} if case['case'] == 'rx-crc16' else {67})
        offers = [header for header in scan((folder / 'serial.bin').read_bytes())
                  if header['type'] == 1]
        assert len(offers) >= len(expected) + 1
        assert all(header['position'] == 0x21000100 for header in offers)
        audit_path = folder / 'native-passive-audit.json'
        audit = dict(passed=True, protocol=protocol, receive_offer_count=len(offers),
                     receive_offer=dict(credit=256, flags=33, position=0x21000100),
                     data_header_formats=sorted(data_formats),
                     auditor_sha256=sha(ROOT / 'lab/bbs/audit_zmodem.py'),
                     scope='Passive exact source/CRC/position/EOF/ZFIN/OO audit and actual receiver offers. '
                           'This harness has no per-byte timing; opposite-control causality, BBS login, '
                           'audio and physical acceptance are separate requirements.')
        with audit_path.open('x') as stream:
            stream.write(json.dumps(audit, indent=2) + '\n')
        for path in folder.rglob('*'):
            if path.is_file():
                captures[str(path.relative_to(ROOT))] = sha(path)
        summaries.append(dict(case=case['case'], checks=case['checks'],
                              files=case['files'], passive_audit=str(audit_path.relative_to(ROOT)),
                              passive_audit_sha256=sha(audit_path),
                              independent_peer=case['peer_command'],
                              independent_peer_sha256=sha(Path(case['peer_command'][0]))))
    result = dict(passed=True, actual_DOS_independent_sender_accepted=True,
                  terminal_sha256=sha(binary), terminal_manifest_sha256=sha(manifest_path),
                  native_component_record=dict(path=str(component_path.relative_to(ROOT)),
                                               sha256=sha(component_path)),
                  cases=summaries, captures_sha256=captures,
                  inputs={str(path.relative_to(ROOT)): sha(path) for path in
                          (Path(__file__).resolve(), ROOT / 'standalone/test_terminal_zmodem_dos.py',
                           ROOT / 'lab/bbs/audit_zmodem.py')},
                  scope='Two actual DOS automatic receive sessions with native256-byte flags33 offers '
                        'against pinned independent lrzsz, CRC16 and CRC32. Each session receives empty, '
                        'one-byte and65797-byte all-octet files and returns to keyboard/DSR interaction '
                        'with normal DOS/UART/IRQ restoration. Passive source/CRC/EOF/finish checks are '
                        'distinct from opposite-control timing, stock BBS/audio, sustained-load and '
                        'Boca/SPA2102 hardware acceptance. All F01-F16 application gates remain open.')
    with target.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, cases=len(summaries), terminal_sha256=sha(binary))))


if __name__ == '__main__':
    main()
