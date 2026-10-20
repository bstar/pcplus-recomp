#!/usr/bin/env python3
"""Reject damaged evidence for actual DOS save-dialog edge workflows."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from enigma_infocom_edges_dos import audit, quetzal_identity
from enigma_key_stream_fixture import ROOT, owned, sha


def save_policy(report, snapshots, story):
    mode = report['mode']
    if mode == 'cancel':
        assert not report['saved_files'] and not snapshots
    elif mode == 'overwrite':
        assert len(snapshots) == 2 and snapshots[0]['path'] == snapshots[1]['path']
        assert snapshots[0]['sha256'] != snapshots[1]['sha256']
        assert len(report['saved_files']) == 1 and report['saved_files'][0]['sha256'] == snapshots[-1]['sha256']
    else:
        assert {Path(row['path']).name for row in report['saved_files']} == {'locprobe.glksave', 'broken.glksave'}


def main(args):
    candidate = owned(args.candidate)
    assert args.label.replace('-', '').replace('_', '').isalnum()
    folder = ROOT / 'build/bbs-lab/results/enigma' / args.label
    report = json.loads((folder / 'infocom-edge-checks.json').read_text())
    assert report['passed'] and all(report['checks'].values())
    mode = report['mode']
    display = (folder / 'display-clean.txt').read_text()
    wire = (folder / 'bbs-sent.bin').read_bytes()
    rows = [json.loads(line) for line in (folder / 'server-session.jsonl').read_text().splitlines()]
    assert all(audit(mode, display, wire, rows).values())
    meta = json.loads((candidate / 'infocom-save-instance.json').read_text())
    story = (candidate / next(name for name in meta['fixture_inputs'] if name.startswith('local/infocom/'))).read_bytes()
    snapshots = report['snapshots']
    save_policy(report, snapshots, story)
    for snapshot in snapshots:
        data = (folder / snapshot['snapshot']).read_bytes()
        assert sha(folder / snapshot['snapshot']) == snapshot['sha256'] and quetzal_identity(data, story)
    for saved in report['saved_files']:
        path = candidate / meta['save_root'] / saved['path']
        assert sha(path) == saved['sha256'] and path.stat().st_size == saved['bytes']
    cases = []
    def reject(name, text=display, sent=wire, events=rows):
        assert not all(audit(mode, text, sent, events).values()), name
        cases.append(dict(case=name, rejected=True))
    reject('missing-game-command', sent=wire.replace(b'ZORK\r', b'', 1))
    reject('missing-worker-stop', events=[row for row in rows if row.get('msg') != 'Z-Machine VM stopped'])
    reject('worker-error', events=rows + [dict(msg='zmachine worker error')])
    reject('missing-menu-return', text=display.replace('Main Menu', ''))
    reject('missing-game-room', text=display.replace('West of House', ''))
    if mode == 'cancel':
        reject('missing-invalid-name-rejection', text=display.replace('Use letters, numbers', ''))
        reject('missing-cancel-input', sent=wire.replace(b'CANCEL\r', b''))
        reject('missing-missing-file-input', sent=wire.replace(b'missing\r', b''))
        changed = copy.deepcopy(report)
        changed['saved_files'] = [dict(path='unexpected.glksave')]
        try:
            save_policy(changed, snapshots, story)
        except AssertionError:
            cases.append(dict(case='file-created-on-cancel', rejected=True))
        else:
            raise AssertionError('Cancellation save evidence accepted')
    else:
        reject('missing-restore-input', sent=wire.replace(b'restore\r', b'', 1))
        if mode == 'corrupt':
            reject('missing-rejection-message', text=display.replace('Cannot restore this save file.', ''))
            reject('missing-post-error-room', text=display[:display.index('Cannot restore this save file.')] +
                display[display.index('Cannot restore this save file.'):].replace('North of House', ''))
            reject('missing-valid-restore-after-error', sent=wire.replace(b'locprobe\r', b''))
        else:
            changed = copy.deepcopy(snapshots)
            changed[1]['sha256'] = changed[0]['sha256']
            try:
                save_policy(report, changed, story)
            except AssertionError:
                cases.append(dict(case='overwrite-did-not-change-save', rejected=True))
            else:
                raise AssertionError('Unchanged overwrite accepted')
            data = (folder / snapshots[-1]['snapshot']).read_bytes()
            wrong = bytearray(data)
            wrong[4:8] = b'\0\0\0\0'
            for name, content in [('empty-save', b''), ('truncated-save', data[:-1]), ('invalid-IFF-size', bytes(wrong))]:
                assert not quetzal_identity(content, story)
                cases.append(dict(case=name, rejected=True))
    result = dict(passed=True, cases=cases, checker_sha256=sha(Path(__file__)),
        runner_sha256=sha(ROOT / 'lab/bbs/enigma_infocom_edges_dos.py'),
        captures={str(path.relative_to(ROOT)): sha(path) for path in [folder / 'infocom-edge-checks.json',
            folder / 'display-clean.txt', folder / 'bbs-sent.bin', folder / 'server-session.jsonl',
            *[folder / snapshot['snapshot'] for snapshot in snapshots]]},
        scope='Passive retained actual DOS route/lifecycle/save evidence with individually rejected corruptions; no replies generated.')
    (folder / 'infocom-edge-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(mode, 'edge audit:', len(cases), 'corruptions rejected')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--label', required=True)
    main(parser.parse_args())
