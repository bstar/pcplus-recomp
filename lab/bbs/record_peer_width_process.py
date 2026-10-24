#!/usr/bin/env python3
"""Audit the full source/window/SAVE/graphics wide DOS-child matrix."""
import argparse
import hashlib
import itertools
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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case', action='append', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert len(a.case) == 16
    variants, cases, artifacts = set(), {}, {}
    identities = None
    for path in a.case:
        folder = path.resolve()
        assert folder.is_relative_to(ROOT / 'build') and folder.name not in cases
        report_file = folder / 'checks.json'
        report = json.loads(report_file.read_text())
        assert report['passed'] and all(report['checks'].values())
        variant = tuple(report[k] for k in ['source_compilation', 'window', 'noclear', 'graphics'])
        assert variant not in variants
        variants.add(variant)
        identity = (report['binary_sha256'], report['runner_sha256'])
        if identities is None:
            identities = identity
        assert identities == identity
        for name, digest in report['inputs'].items():
            assert sha(ROOT / name) == digest, name
        for name, digest in report['artifacts'].items():
            assert sha(ROOT / name) == digest, name
        product = folder / 'product'
        state = struct.unpack('<28H', (product / 'BBSOBS.BIN').read_bytes())
        assert list(state) == report['state']
        assert state[:2] == (0x4257, 1) and state[2] == state[3] != 0
        assert state[4:6] == (2, 0) and state[6] == state[7] != 0 and state[6] != state[2]
        assert state[8] == 0 and state[9] > 0 and state[27] > 0
        assert (state[11] > 0) == report['window']
        assert state[12:21] == (80, 0, 0, 0, 0, 0, 0, 0, 1)
        assert state[21:27] == (37, 1, 1 if report['noclear'] else 2, 0, 1, 1)
        before = (product / 'BEFORE.BIN').read_bytes()
        assert len(before) == 42 and before == (product / 'AFTER.BIN').read_bytes()
        assert (product / 'CHILD.BIN').read_bytes() == b'\x03\x50\x00'
        assert (product / 'WIDE.LOG').read_bytes() == b'START|WIDE|CHILDRETURN|RESUMED|'
        assert (product / 'WIDE.ASX').read_bytes() == compile_source(report['script'])
        if report['source_compilation']:
            assert (product / 'WIDE.ASP').read_text() == report['script']
        # Order matters: genuine wide response, nested child return, continued
        # wide renderer, then manual parent input and a narrow response.
        wire = (product / 'serial.bin').read_bytes()
        position = 0
        for token in [b'SCRIPTREADY\r', b'\x1b[2;128R', b'AFTERCHILD\r',
                      b'\x1b[3;6R', b'\x1b[3;128R', b'ready', b'\x1b[2;80R']:
            position = wire.index(token, position) + len(token)
        modem = json.loads((product / 'result.json').read_text())
        assert modem['commands'] == ['ATZ', 'ATDCaseTest:23'] and not modem['errors']
        assert modem['cpu'] == '8086' and modem['expected_exit'] == 0
        artifacts.update(report['artifacts'])
        artifacts[str(report_file.relative_to(ROOT))] = sha(report_file)
        cases[folder.name] = report
    assert variants == set(itertools.product([False, True], repeat=4))
    output = dict(passed=True, full_compatibility=False, accepted_for_deployment=False,
                  binary_sha256=identities[0], runner_sha256=identities[1],
                  cases=cases, artifacts=artifacts, recorder_sha256=sha(Path(__file__)),
                  limitations=['Logical132 on physical80; continued geometry, ownership and replies, without a full logical-plane comparison around child execution.',
                               'Actual RUN of a source-built COM child in DOSBox, not arbitrary OS interruption or every DOS command processor/kernel.',
                               'Synthetic serial modem; no BBS/audio/physical modem or card deployment acceptance.',
                               'Wide transfers, remaining application families and full F01-F16 acceptance remain open.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(output, indent=2) + '\n')
    print(f'Sealed16 wide DOS-child workflows and {len(artifacts)} artifacts')


if __name__ == '__main__':
    main()
