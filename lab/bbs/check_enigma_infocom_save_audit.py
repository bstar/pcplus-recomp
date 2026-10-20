#!/usr/bin/env python3
"""Reject incomplete save/restore evidence from a retained successful DOS run."""
import argparse
import json
from pathlib import Path
import re

from enigma_infocom_save_dos import audit, quetzal_identity
from enigma_key_stream_fixture import ROOT, owned
from enigma_notes_fixture import sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    folder = ROOT / 'build/bbs-lab/results/enigma' / args.label
    candidate = owned(args.candidate)
    report_path = folder / 'infocom-save-checks.json'
    report = json.loads(report_path.read_text())
    assert report['passed'] and all(report['checks'].values())
    text = (folder / 'display-clean.txt').read_text()
    sent = (folder / 'bbs-sent.bin').read_bytes()
    rows = [json.loads(line) for line in (folder / 'server-session.jsonl').read_text().splitlines()]
    assert all(audit(text, sent, rows).values())
    cases = [
        ('missing-restored-room', text[:text.index('Restore name [save]')] +
            text[text.index('Restore name [save]'):].replace('North of House', ''),
            sent, rows, 'rooms_across_worker_restart'),
        ('missing-save-prompt', text.replace('Save name [save]', ''), sent, rows,
            'rooms_across_worker_restart'),
        ('missing-restore-command', text, sent.replace(b'restore\r', b''), rows,
            'emitted_save_restore'),
        ('missing-second-game', text, sent.replace(b'ZORK\r', b'', 1), rows,
            'emitted_save_restore'),
        ('missing-worker-stop', text, sent,
            [r for r in rows if r.get('msg') != 'Z-Machine VM stopped'], 'two_worker_lifecycles'),
        ('worker-error', text, sent, rows + [dict(msg='zmachine worker error')], 'no_worker_errors'),
        ('missing-menu-return', text.replace('Main Menu', ''), sent, rows, 'returned_to_menu'),
    ]
    rejected = []
    for name, display, wire, events, check in cases:
        assert not audit(display, wire, events)[check], name
        rejected.append(dict(case=name, rejected=True))
    meta = json.loads((candidate / 'infocom-save-instance.json').read_text())
    saved = candidate / meta['save_root'] / report['saved_files'][0]['path']
    story_path = next(candidate / p for p in meta['fixture_inputs'] if p.startswith('local/infocom/'))
    data, story = saved.read_bytes(), story_path.read_bytes()
    assert sha(saved) == report['saved_files'][0]['sha256']
    assert quetzal_identity(data, story)
    wrong_story = bytearray(story)
    wrong_story[2] ^= 1
    wrong_save = bytearray(data)
    wrong_save[4:8] = b'\0\0\0\0'
    for name, content, source in [
        ('empty-save', b'', story), ('truncated-save', data[:-1], story),
        ('wrong-iff-size', bytes(wrong_save), story),
        ('wrong-story-identity', data, bytes(wrong_story))]:
        assert not quetzal_identity(content, source), name
        rejected.append(dict(case=name, rejected=True))
    result = dict(passed=True, negative_cases=rejected,
        report_sha256=sha(report_path), runner_sha256=sha(ROOT / 'lab/bbs/enigma_infocom_save_dos.py'),
        checker_sha256=sha(Path(__file__)),
        inputs={str(p.relative_to(ROOT)): sha(p) for p in (
            folder / 'display-clean.txt', folder / 'bbs-sent.bin', folder / 'server-session.jsonl', saved, story_path)},
        scope='Corruptions of actual DOS/isolated door evidence and persisted save; no generated replies or server execution.')
    (folder / 'save-audit-negative-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Save/restore baseline passes; eleven incomplete/corrupt evidence cases rejected.')


if __name__ == '__main__':
    main()
