#!/usr/bin/env python3
"""Audit strict X/YMODEM bytes, files and width recovery for all six workflows."""
import argparse
import binascii
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'standalone'))
from test_clipboard_transfer_dos import recipes


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packet(stream, position):
    assert stream[position] in (1, 2)
    size = 128 if stream[position] == 1 else 1024
    data = stream[position + 3:position + 3 + size]
    assert len(data) == size and stream[position + 1] ^ stream[position + 2] == 255
    assert int.from_bytes(stream[position + 3 + size:position + 5 + size], 'big') == binascii.crc_hqx(data, 0)
    return stream[position + 1], data, position + 5 + size


def locate(stream, number, prefix):
    for position in range(len(stream)):
        if stream[position] not in (1, 2):
            continue
        try:
            seq, data, end = packet(stream, position)
        except (AssertionError, IndexError):
            continue
        if seq == number and data.startswith(prefix):
            return position
    raise AssertionError('No matching integrity-checked first frame')


def body(stream, position, expected):
    sequence = 1
    data = bytearray()
    while stream[position] in (1, 2):
        seq, part, position = packet(stream, position)
        assert seq == sequence & 255
        sequence += 1
        data.extend(part)
    assert stream[position] == 4
    while stream[position] == 4:
        position += 1
    assert data[:len(expected)] == expected and len(data) >= len(expected)
    assert data[len(expected):] == b'\x1a' * (len(data) - len(expected))
    return position, sequence - 1


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', type=Path, action='append', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    required = {r['name']: r for r in recipes()}
    assert len(a.case) == len(required) == 6
    cases, artifacts = {}, {}
    identity = None
    for value in a.case:
        folder = value.resolve()
        assert folder.is_relative_to(ROOT / 'build')
        report_file = folder / 'checks.json'
        report = json.loads(report_file.read_text())
        assert report['passed'] and all(report['result']['checks'].values())
        name = report['case']
        assert name in required and name not in cases
        recipe = required[name]
        if identity is None:
            identity = report['binary_sha256']
        assert identity == report['binary_sha256']
        for section in ['inputs', 'artifacts']:
            for path, digest in report[section].items():
                assert sha(ROOT / path) == digest, path
        product = folder / 'wide' / name
        before = (product / 'BEFORE.BIN').read_bytes()
        assert len(before) == 42 and before == (product / 'AFTER.BIN').read_bytes()
        screen = (product / 'SCREEN.BIN').read_bytes()
        assert len(screen) == 4000 and screen[:28:2] == b'AFTER TRANSFER'
        wire = (product / 'serial.bin').read_bytes()
        peer = (product / 'peer.bin').read_bytes()
        events = json.loads((product / 'events.json').read_text())
        kinds = [e['event'] for e in events]
        # The wrapper verifies post-protocol width before entering the legacy
        # menu-resume method, which emits its own protocol-complete log marker.
        assert kinds.index('wide-before-selection') < kinds.index('wide-after-protocol')
        assert kinds.index('wide-after-protocol') < kinds.index('protocol-complete') < kinds.index('narrow-after-keyboard')
        assert wire.count(b'\x1b[2;128R') == 2 and wire.count(b'\x1b[2;80R') == 1
        assert wire.index(b'\x1b[2;128R') < report['result']['selections'][0]['wire_offset']
        assert wire.rindex(b'\x1b[2;128R') < wire.rindex(b'ready') < wire.index(b'\x1b[2;80R')
        for selection in report['result']['selections']:
            start = selection['wire_offset']
            data = bytes.fromhex(selection['packet_hex'])
            assert wire[start:start + len(data)] == data
        sender = peer if recipe['direction'] == 'rx' else wire
        expected = {n: recipe['catalog'][n] for n in recipe['chosen']}
        if recipe['protocol'] == 'XMODEM':
            content = next(iter(expected.values()))
            position = locate(sender, 1, content[:128])
            start = position
            end, blocks = body(sender, position, content)
            assert blocks > 0
        else:
            position = locate(sender, 0, recipe['chosen'][0].encode() + b'\0')
            start = position
            for filename, content in expected.items():
                seq, header, position = packet(sender, position)
                assert seq == 0
                remote_name, metadata = header.split(b'\0', 1)
                assert remote_name.decode('ascii') == filename
                assert int(metadata.split(b'\0', 1)[0].split(b' ', 1)[0]) == len(content)
                position, blocks = body(sender, position, content)
            seq, header, end = packet(sender, position)
            assert seq == 0 and header == bytes(128)
        if recipe['direction'] == 'rx':
            assert end <= peer.index(b'\x1b[2;121HRESUMED\x1b[6n')
        else:
            assert end <= wire.rindex(b'\x1b[2;128R')
        destination = product / ('RECV' if recipe['direction'] == 'rx' else 'SEND')
        assert {path.name: path.read_bytes() for path in destination.iterdir()} == expected
        assert not any(path.name.upper().startswith(('PCRX.', 'PCYM.')) for path in product.rglob('*'))
        config = (product / 'dosbox.conf').read_text()
        assert 'cputype=8086\n' in config and 'COM1 38400 8N1 HARD' in config
        cases[name] = dict(report=report, independent_sender_range=[start, end])
        artifacts.update(report['artifacts'])
        artifacts[str(report_file.relative_to(ROOT))] = sha(report_file)
    assert set(cases) == set(required)
    result = dict(passed=True, full_compatibility=False, accepted_for_deployment=False,
                  binary_sha256=identity, cases=cases, artifacts=artifacts,
                  recorder_sha256=sha(Path(__file__)),
                  limitations=['Independent strict X/YMODEM peers and synthetic files, not stock BBS/audio or physical modem acceptance.',
                               'Width132 before selection and after protocol, followed by keyboard/narrow recovery; no injected width request inside binary protocol data.',
                               'ZMODEM, other protocols, full application families and card deployment remain separate requirements.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Sealed six wide X/YMODEM workflows and {len(artifacts)} artifacts')


if __name__ == '__main__':
    main()
