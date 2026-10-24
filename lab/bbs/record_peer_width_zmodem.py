#!/usr/bin/env python3
"""Seal wide-view DOS ZMODEM using the independent passive wire decoder."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_zmodem import audit_batch, scan

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', type=Path, action='append', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    required = {('rx-default', False), ('rx-crc16', False), ('tx-default', False),
                ('tx-escape', False), ('rx-default', True), ('rx-crc16', True)}
    assert len(a.case) == 6
    cases, variants, artifacts = {}, set(), {}
    identity = None
    for value in a.case:
        folder = value.resolve()
        assert folder.is_relative_to(ROOT / 'build') and folder.name not in cases
        report_file = folder / 'checks.json'
        report = json.loads(report_file.read_text())
        result = report['result']
        assert report['passed'] and result['passed'] and all(result['checks'].values())
        variant = (result['case'], report['automatic'])
        assert variant in required and variant not in variants
        variants.add(variant)
        if identity is None:
            identity = report['binary_sha256']
        assert report['binary_sha256'] == result['binary_sha256'] == identity
        for section in ['inputs', 'artifacts']:
            for name, digest in report[section].items():
                assert sha(ROOT / name) == digest, name
        peer = report['peer']
        assert Path(peer['path']).is_relative_to('/nix/store')
        assert sha(Path(peer['path'])) == peer['sha256']
        assert Path(result['peer_command'][0]).resolve() == Path(peer['path'])
        assert result['peer_exit'] == 0 and not result['errors']
        product = folder / 'wide' / result['case']
        before = (product / 'BEFORE.BIN').read_bytes()
        assert len(before) == 42 and before == (product / 'AFTER.BIN').read_bytes()
        screen = (product / 'SCREEN.BIN').read_bytes()
        assert len(screen) == 4000 and screen[:28:2] == b'AFTER TRANSFER'
        expected = {'EMPTY.BIN': b'', 'ODD.BIN': b'A',
                    'ALL.BIN': bytes(range(256)) * 257 + b'\0\x1a\xff@\r'}
        sending = result['case'].startswith('tx-')
        for part in (('SEND', 'PEER') if sending else ('PEER', 'RECV')):
            assert {f.name: f.read_bytes() for f in (product / part).iterdir()} == expected
        assert result['files'] == {n: hashlib.sha256(data).hexdigest() for n, data in expected.items()}
        wire = (product / 'serial.bin').read_bytes()
        remote = (product / 'peer.bin').read_bytes()
        sender, opposite = (wire, remote) if sending else (remote, wire)
        audit = audit_batch(sender, expected)
        assert len(audit['files']) == 3
        offers = [e for e in audit['events'] if e['kind'] == 'header' and e['type'] == 4]
        assert offers and all(e['format'] == (65 if result['case'] == 'rx-crc16' else 67) for e in offers)
        controls = list(scan(opposite))
        assert sum(h['type'] == 9 and h['position'] == 0 for h in controls) >= 3
        assert any(h['type'] == 8 for h in controls)
        if not sending:
            credit = 256 if report['automatic'] else 8192
            assert result['receive_credit'] == (256 if report['automatic'] else None)
            ready = [h for h in controls if h['type'] == 1]
            assert len(ready) >= 4
            assert all(h['position'] == ((33 if credit < 8192 else 35) << 24 | credit) for h in ready)
        assert wire.count(b'\x1b[2;128R') == 2 and wire.count(b'\x1b[2;80R') == 1
        assert wire.rindex(b'\x1b[2;128R') < wire.index(b'ready') < wire.index(b'\x1b[2;80R')
        if sending:
            assert wire.index(b'\x1b[2;128R') < audit['start'] < audit['end'] <= wire.rindex(b'\x1b[2;128R')
        else:
            assert remote.index(b'\x1b[?3h') < audit['start'] < audit['end'] <= remote.index(b'\x1b[2;121HRESUMED')
        kinds = [e['event'] for e in json.loads((product / 'events.json').read_text())]
        assert kinds.index('wide-before-protocol') < kinds.index('protocol-start') < kinds.index('peer-completed')
        assert kinds.index('peer-completed') < kinds.index('wide-after-protocol') < kinds.index('narrow-after-keyboard') < kinds.index('terminal-resumed')
        config = (product / 'dosbox.conf').read_text()
        assert 'cputype=8086\n' in config and 'COM1 38400 8N1 HARD' in config
        if report['automatic']:
            assert not {'a-r', 'f2', 'enter'} & set(result['keys'])
            assert result['checks']['saved_preferences_unchanged']
        for f in audit['files']:
            del f['source']
        cases[folder.name] = dict(report=report, independent_wire_audit=audit)
        artifacts.update(report['artifacts'])
        artifacts[str(report_file.relative_to(ROOT))] = sha(report_file)
    assert variants == required
    output = dict(passed=True, binary_sha256=identity, full_compatibility=False,
                  accepted_for_deployment=False, cases=cases, artifacts=artifacts,
                  recorder_sha256=sha(Path(__file__)), audit_sha256=sha(ROOT / 'lab/bbs/audit_zmodem.py'),
                  limitations=['Actual8086 DOS with independent pinned lrzsz and passive CRC/metadata/data/EOF/ZFIN/OO audit; no stock BBS/audio or physical modem claim.',
                               'Width132 before/after protocol and width80 after keyboard; no width command is inserted into binary protocol data.',
                               'This audit does not establish response timing from TCP chunk timestamps; full application, other protocols and card deployment remain open.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(output, indent=2) + '\n')
    print(f'Sealed six wide ZMODEM workflows and {len(artifacts)} artifacts')


if __name__ == '__main__':
    main()
