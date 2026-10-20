#!/usr/bin/env python3
"""Passively audit DOS door captures and reject individually damaged routes."""
import argparse
import json
from pathlib import Path

from enigma_v86_dos import audit
from enigma_key_stream_fixture import ROOT, sha


def main(args):
    assert args.label.replace('-', '').replace('_', '').isalnum()
    folder = ROOT / 'build/bbs-lab/results/enigma' / args.label
    report = json.loads((folder / 'v86-door-checks.json').read_text())
    assert report['passed'] and all(report['checks'].values())
    display = (folder / 'display-clean.txt').read_text()
    wire = (folder / 'bbs-sent.bin').read_bytes()
    rows = [json.loads(line) for line in (folder / 'server-session.jsonl').read_text().splitlines()]
    assert all(audit(report['game'], display, wire, rows).values())
    cases = []
    def reject(name, text=display, sent=wire, events=rows):
        assert not all(audit(report['game'], text, sent, events).values()), name
        cases.append(dict(case=name, rejected=True))
    reject('missing-worker-start', events=[r for r in rows if r.get('msg') != 'v86 emulator ready'])
    reject('missing-worker-stop', events=[r for r in rows if r.get('msg') != 'v86 emulator stopped'])
    reject('worker-error', events=rows + [dict(msg='v86 worker error')])
    reject('disconnect-causes-stop', events=rows + [dict(msg='Client disconnected — stopping v86 worker')])
    reject('missing-doors-return', events=[r for r in rows if r.get('menuName') != 'doorsMainMenu'])
    reject('missing-main-return', events=[r for r in rows if r.get('menuName') != 'mainMenu'])
    if report['game'] == 'gwar':
        reject('missing-game-selection-input', sent=wire.replace(b'1\r', b''))
        reject('missing-instructions-input', sent=wire.replace(b'I\r', b''))
        reject('missing-pager-input', sent=wire.replace(b'N\r', b''))
        reject('missing-quit-input', sent=wire.replace(b'Q\r', b''))
        reject('missing-instructions', text=display.replace('ABOUT GLOBAL WAR', ''))
        reject('missing-pager', text=display.replace('More? (Y/N)', ''))
        reject('missing-game-return', text=display.replace('Returning to LoSs oF CoNtRoL', ''))
    else:
        reject('missing-name-input', sent=wire.replace(b'LoC Lab\r', b''))
        reject('missing-quit-input', sent=wire.replace(b'0\r', b''))
        reject('missing-name-confirmation', text=display.replace('Name Your Empire', ''))
        reject('missing-game-menu', text=display.replace('[Barren Realms Elite]', ''))
    result = dict(passed=True, cases=cases, checker_sha256=sha(Path(__file__)),
        runner_sha256=sha(ROOT / 'lab/bbs/enigma_v86_dos.py'),
        captures={name: sha(folder / name) for name in ('v86-door-checks.json', 'display-clean.txt',
            'bbs-sent.bin', 'server-session.jsonl', 'result.json')},
        scope='Passive route, actual game interaction and lifecycle evidence; no game replies generated.')
    (folder / 'v86-door-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(report['game'], 'audit:', len(cases), 'corruptions rejected')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    main(parser.parse_args())
