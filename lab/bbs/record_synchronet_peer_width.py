#!/usr/bin/env python3
"""Independently bind DOS width replies, server getxy results and stock return."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
    output = ROOT / 'build/bbs-lab/results/synchronet' / a.label
    wrapper = output.with_name(a.label + '-wrapper')
    report = json.loads((wrapper / 'checks.json').read_text())
    assert report['passed'] and all(report['checks'].values())
    assert report['checks']['stock_file_menu'] and report['checks']['final_file_prompt']
    assert report['modem_packet_delay_ms'] == 0
    for name, digest in report['inputs'].items():
        assert sha(ROOT / name) == digest, name
    custody = dict(report['artifacts'])
    for name, digest in custody.items():
        assert sha(ROOT / name) == digest, name
    events = [json.loads(line) for line in (wrapper / 'peer-width.jsonl').read_text().splitlines()]
    assert [(e['width'], e['selection']) for e in events if e['kind'] == 'paint'] == [(132, 0), (132, 1), (132, 0), (80, 0), (132, 0)]
    assert [e['position'] for e in events if e['kind'] == 'cpr'] == [dict(x=128, y=2)] * 3 + [dict(x=80, y=2), dict(x=128, y=2)]
    assert [e['key'] for e in events if e['kind'] == 'key' and e['key'] != ' '] == ['\x06', '\x1d', 'n', 'w', 'q']
    wire = (output / 'serial-received.bin').read_bytes()
    assert wire.count(b'\x1b[2;128R') == 4 and wire.count(b'\x1b[2;80R') == 1
    assert b'\x1b[C' in wire and b'\x1b[D' in wire
    assert b'/text/menu/transfer.' in (wrapper / 'server-session.log').read_bytes()
    assert '■ File ■' in (output / 'screen.txt').read_text()
    assert (output / 'BEFORE.BIN').read_bytes() == (output / 'AFTER.BIN').read_bytes()
    assert len((output / 'BEFORE.BIN').read_bytes()) == 42
    custody[str((wrapper / 'checks.json').relative_to(ROOT))] = sha(wrapper / 'checks.json')
    result = dict(passed=True, full_compatibility=False, accepted_for_deployment=False,
                  label=a.label, checks=report['checks'], binary_sha256=report['binary_sha256'],
                  inputs=report['inputs'], artifact_hashes=custody, recorder_sha256=sha(Path(__file__)),
                  scope=report['scope'], limitations=['Explicit synthetic shell followed by the stock File Transfer menu; no stock132-column-art adaptation claim.',
                                                   'No active ASPECT/BBS width composition, wide file transfer, carrier/OS cancellation or physical modem acceptance.',
                                                   'Application source proof and card release remain separate gates.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Sealed Synchronet width/arrow/stock-return run and {len(custody)} artifacts')


if __name__ == '__main__':
    main()
