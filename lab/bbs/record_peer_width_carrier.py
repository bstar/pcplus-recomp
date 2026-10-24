#!/usr/bin/env python3
"""Seal real emulated carrier-loss cleanup, native WAITFOR controls and redial."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src/aspect'))
from compiler import compile_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert len(args.case) == 6
    cases = {}
    variants = set()
    controls = set()
    artifacts = {}
    binary = runner = None
    for value in args.case:
        directory = value.resolve()
        assert directory.is_relative_to(ROOT / 'build') and directory.name not in cases
        report_path = directory / 'checks.json'
        report = json.loads(report_path.read_text())
        assert report['passed'] and all(report['checks'].values())
        for name, digest in report['inputs'].items():
            assert sha(ROOT / name) == digest, name
        for name, digest in report['artifacts'].items():
            assert sha(ROOT / name) == digest, name
        if binary is None:
            binary, runner = report['binary_sha256'], report['runner_sha256']
        assert (report['binary_sha256'], report['runner_sha256']) == (binary, runner)
        if report['disconnect_handler']:
            assert report['wait_seconds'] == 3
            variants.add((report['source_compilation'], report['window']))
        else:
            assert not report['source_compilation'] and report['window']
            controls.add(report['wait_seconds'])
        state = struct.unpack('<64H', (directory / 'BBSOBS.BIN').read_bytes())
        assert list(state) == report['state']
        assert state[:2] == (0x4357, 1) and state[2] == state[3] != 0
        assert state[4:6] == (1, 0) and state[6] == state[7] != 0 and state[6] != state[2]
        assert state[8] == 0 and state[9] > 0 and state[10] > 0
        assert (state[11] > 0) == report['window']
        assert state[12:21] == (132, 0, 0, 0, 0, 0, 0, 0, 1)
        assert state[21] >= 12 and state[22] > 0 and state[23] > 0 and state[24] > 0
        assert state[25:34] == (132, 0, 0, 0, 0, 0, 0, 0, 6)
        assert state[36:39] == (1, 1, 1)
        assert state[39:45] == (1, 0, 1, 0, 0, 0) and state[50] > 0
        assert state[51] == 1, 'The child must have exited before the redial key'
        assert state[55:] == (65535,) * 9, 'Never inspect a released child allocation'
        before = (directory / 'BEFORE.BIN').read_bytes()
        assert len(before) == 46 and before == (directory / 'AFTER.BIN').read_bytes()
        assert (directory / 'WIDE.ASX').read_bytes() == compile_source(report['script'])
        if report['source_compilation']:
            assert (directory / 'WIDE.ASP').read_text(encoding='ascii') == report['script']
        expected = b'START|WIDE|LOST|' if report['disconnect_handler'] else b'START|WIDE|RETURN|'
        assert (directory / 'WIDE.LOG').read_bytes() == expected
        assert len(report['sessions']) == 2 and not any(s['errors'] for s in report['sessions'])
        events = report['sessions'][0]['events']
        names = [e['kind'] for e in events]
        assert names == ['connected', 'wide-request', 'partial-command', 'carrier-drop', 'closed']
        partial = next(e['seconds'] for e in events if e['kind'] == 'partial-command')
        drop = next(e['seconds'] for e in events if e['kind'] == 'carrier-drop')
        assert .9 <= drop - partial < 2
        sent = (directory / 'connection-1/sent.bin').read_bytes()
        first = (directory / 'connection-1/received.bin').read_bytes()
        second = (directory / 'connection-2/received.bin').read_bytes()
        assert sent.endswith(b'\x1b[?3') and b'END' not in sent
        assert b'SCRIPTREADY\r' in first and b'\x1b[2;128R' in first and b'WIDEACK\r' in first
        assert all(reply in second for reply in [b'\x1b[2;80R', b'\x1b[2;128R', b'\x1b[3;6R', b'ready'])
        modem = (directory / 'dosbox.log').read_text()
        assert modem.count('Command sent to modem: ->AT&K3<-') == 2
        assert 'Modem response: NO CARRIER' in modem and 'Modem response: ERROR' not in modem
        artifacts.update(report['artifacts'])
        artifacts[str(report_path.relative_to(ROOT))] = sha(report_path)
        cases[directory.name] = report
    assert variants == {(s, w) for s in (False, True) for w in (False, True)}
    assert controls == {3, 30}
    result = dict(passed=True, full_compatibility=False, accepted_for_deployment=False,
                  cases=cases, artifacts=artifacts, binary_sha256=binary, runner_sha256=runner,
                  recorder_sha256=sha(Path(__file__)),
                  limitations=['The native WHEN DISCONNECT CALL worker waits for the active WAITFOR to finish; these runs do not claim immediate abort of every script on DCD loss.',
                               'DOSBox built-in Hayes modem and emulated DCD, raw deterministic loopback peer; no real BBS through this carrier path or physical Boca/SPA2102 acceptance.',
                               'Interruption is after a committed wide mode while a second CSI is incomplete, not a forced failure in the native transaction body.',
                               'General DOS/OS interruption, wide transfers, unsupported application families and card deployment remain open.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Sealed six carrier/width workflows and {len(artifacts)} artifacts')


if __name__ == '__main__':
    main()
