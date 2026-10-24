#!/usr/bin/env python3
"""Seal actual BBS width requests across source/precompiled ASPECT and window states."""
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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label', action='append', required=True)
    p.add_argument('--stock-label', help='Optional stock-server source/window case with explicit modem buffering')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert len(a.label) == len(set(a.label)) == 4
    cases = {}
    artifacts = {}
    variants = set()
    binary = runner = None
    assert not a.stock_label or a.stock_label not in a.label
    for label in a.label + ([a.stock_label] if a.stock_label else []):
        assert label and all(c.isalnum() or c in '-_' for c in label)
        output = ROOT / 'build/bbs-lab/results/enigma' / label
        wrapper = output.with_name(label + '-wrapper')
        report = json.loads((wrapper / 'checks.json').read_text())
        assert report['passed'] and all(report['checks'].values())
        stock = label == a.stock_label
        if stock:
            assert 0 < report['modem_packet_delay_ms'] <= 100
            assert report['source_compilation'] and report['window']
        else:
            assert report['modem_packet_delay_ms'] == 0
        for name, digest in report['inputs'].items():
            assert sha(ROOT / name) == digest, name
        for name, digest in report['artifacts'].items():
            assert sha(ROOT / name) == digest, name
        if binary is None:
            binary, runner = report['binary_sha256'], report['runner_sha256']
        assert (report['binary_sha256'], report['runner_sha256']) == (binary, runner)
        if not stock:
            variants.add((report['source_compilation'], report['window']))
        state = struct.unpack('<21H', (output / 'BBSOBS.BIN').read_bytes())
        assert list(state) == report['state']
        assert state[:2] == (0x4257, 1) and state[2] == state[3] != 0
        assert state[4:6] == (1, 0) and state[6] == state[7] != 0 and state[8] == 0
        assert state[6] != state[2], 'Child and parent must have distinct real DS/SS images'
        assert state[9] > 0 and state[10] > 0 and (state[11] > 0) == report['window']
        assert state[12:] == (80, 0, 0, 0, 0, 0, 0, 0, 1)
        assert (output / 'WIDE.LOG').read_bytes() == b'START|0|1|2|3|4|RETURN|'
        assert (output / 'WIDE.ASX').read_bytes() == compile_source(report['script'])
        if report['source_compilation']:
            assert (output / 'WIDE.ASP').read_text(encoding='ascii') == report['script']
        assert len((output / 'BEFORE.BIN').read_bytes()) == 42
        assert (output / 'BEFORE.BIN').read_bytes() == (output / 'AFTER.BIN').read_bytes()
        wire = (output / 'serial-received.bin').read_bytes()
        assert wire.count(b'\x1b[2;128R') == 4 and wire.count(b'\x1b[2;80R') == 1
        assert b'WIDTH\r' in wire and b'\x1b[C' in wire and b'\x1b[D' in wire
        events = [json.loads(line) for line in (wrapper / 'peer-width.jsonl').read_text().splitlines()]
        assert [(e['width'], e['selection']) for e in events if e['kind'] == 'paint'] == [(132, 0), (132, 1), (132, 0), (80, 0), (132, 0)]
        assert [e['args'] for e in events if e['kind'] == 'cpr'] == [[2, 128]] * 3 + [[2, 80], [2, 128]]
        names = [n for n in report['inputs'] if n.endswith('/peer-width-instance.json')]
        assert len(names) == 1
        instance = json.loads((ROOT / names[0]).read_text())
        if stock:
            assert not instance.get('decoder_inputs')
        else:
            assert set(instance['decoder_inputs']) == {'core/client.js', 'core/key_stream.js'}
        artifacts.update(report['artifacts'])
        artifacts[str((wrapper / 'checks.json').relative_to(ROOT))] = sha(wrapper / 'checks.json')
        cases[label] = report
    assert variants == {(s, w) for s in (False, True) for w in (False, True)}
    result = dict(passed=True, accepted_for_deployment=False, full_compatibility=False,
                  cases=cases, artifacts=artifacts, binary_sha256=binary, runner_sha256=runner,
                  stock_buffered_label=a.stock_label,
                  recorder_sha256=sha(Path(__file__)),
                  limitations=['The four-case matrix uses the explicit incremental decoder candidate. An optional stock case uses declared modem buffering; stock immediate fragmentation failures remain valid.',
                               'Synthetic width menu, actual DOS8086 process/serial ownership; this is not stock132-column artwork adaptation.',
                               'No active-Synchronet width composition, carrier/OS interruption, wide file transfer or physical modem/card acceptance.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Sealed {len(cases)} genuine ASPECT/BBS width cases and {len(artifacts)} artifacts')


if __name__ == '__main__':
    main()
