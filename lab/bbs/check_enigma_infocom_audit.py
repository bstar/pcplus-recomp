#!/usr/bin/env python3
"""Reject incomplete/replayed door evidence using a retained successful DOS run."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from enigma_infocom_probe import audit

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    out = ROOT / 'build/bbs-lab/results/enigma-owned' / args.label
    report = json.loads((out / 'owned-server-checks.json').read_text())
    assert report['passed'] and report['mode'] == 'infocom'
    sources = [out / name for name in ('display.bin', 'bbs-sent.bin', 'server-session.jsonl')]
    display = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', sources[0].read_bytes()).decode('cp437')
    sent = sources[1].read_bytes()
    rows = [json.loads(line) for line in sources[2].read_text().splitlines()]
    ready = [r for r in rows if r.get('msg') == 'Z-Machine VM ready']
    assert len(ready) == 1
    story = ready[0]['name'].removeprefix('LoC-Infocom-')
    assert re.fullmatch('[0-9a-f]{64}', story)
    assert all(audit(display, sent, rows, story).values())
    cases = [
        ('missing-library-page', display.replace('Page 2 / 4', ''), sent, rows, story,
         'infocom_route_gameplay_and_return'),
        ('missing-game-input-response', display.replace('North of House', ''), sent, rows, story,
         'infocom_route_gameplay_and_return'),
        ('missing-final-menu', display.replace('M A I N   M E N U', ''), sent, rows, story,
         'infocom_route_gameplay_and_return'),
        ('missing-quit-command', display, sent.replace(b'quit\r', b''), rows, story,
         'infocom_commands_emitted'),
        ('missing-worker-stop', display, sent,
         [r for r in rows if r.get('msg') != 'Z-Machine VM stopped'], story,
         'infocom_worker_lifecycle'),
        ('wrong-story', display, sent, rows, '0' * 64, 'infocom_worker_lifecycle'),
        ('worker-error', display, sent, rows + [{'msg': 'zmachine worker error'}], story,
         'infocom_no_worker_errors'),
        ('unexpected-save', display, sent + b'save\r', rows, story,
         'infocom_no_save_requested'),
    ]
    rejected = []
    for name, text, wire, events, identity, check in cases:
        result = audit(text, wire, events, identity)
        assert not result[check], name
        rejected.append(dict(case=name, rejected=True, failed_check=check))
    result = dict(passed=True, baseline_checks=5, negative_cases=rejected,
                  inputs={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  report_sha256=sha(out / 'owned-server-checks.json'),
                  audit_sha256=sha(ROOT / 'lab/bbs/enigma_infocom_probe.py'),
                  checker_sha256=sha(Path(__file__)),
                  scope='Mutations of retained actual DOS/live-door evidence; no server execution or replies.')
    (out / 'audit-negative-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Infocom audit: successful baseline and eight incomplete/corrupt evidence cases rejected')


if __name__ == '__main__':
    main()
