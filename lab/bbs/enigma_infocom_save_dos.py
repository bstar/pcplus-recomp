#!/usr/bin/env python3
"""Actual DOS -> isolated owned ENiGMA door -> SAVE -> new worker -> RESTORE."""
import argparse
import asyncio
import contextlib
import json
from pathlib import Path
import re
import shutil
import sqlite3

import test_dos
from enigma_key_stream_fixture import ROOT, PORT, owned, verify_running
from enigma_notes_fixture import sha
from enigma_notes_dos import messages
from enigma_infocom_probe import ordered


BODY = ('c-y Z O R K enter p3000 n o r t h enter p1000 '
        's a v e enter p1000 l o c p r o b e enter p1500 '
        'q u i t enter p1000 y enter p2000 '
        'Z O R K enter p3000 r e s t o r e enter p1000 '
        'l o c p r o b e enter p1500 l o o k enter p1000 '
        'q u i t enter p1000 y enter p2000')


def audit(display, wire, rows):
    lifecycle = [r['msg'] for r in rows if r.get('name') == 'PCPlus-Zork-Save-Probe'
                 and r.get('msg') in ('Z-Machine VM ready', 'Z-Machine VM stopped')]
    return dict(
        rooms_across_worker_restart=ordered(display, (
            'West of House', 'North of House', 'Save name [save]',
            'West of House', 'Restore name [save]',
            'North of House', 'North of House')) is not None,
        emitted_save_restore=ordered(wire, (
            b'ZORK\r', b'north\r', b'save\r', b'locprobe\r',
            b'quit\r', b'y\r', b'ZORK\r', b'restore\r', b'locprobe\r',
            b'look\r', b'quit\r', b'y\r')) is not None,
        two_worker_lifecycles=lifecycle == ['Z-Machine VM ready', 'Z-Machine VM stopped'] * 2,
        no_worker_errors=not any('zmachine' in r.get('msg', '').lower()
            and ('error' in r['msg'].lower() or 'non-zero' in r['msg'].lower()) for r in rows),
        returned_to_menu=display.count('Main Menu') >= 3)


def quetzal_identity(data, story):
    """Check the actual on-disk IFF extent and story identity, not just existence."""
    if data[:4] != b'FORM' or data[8:12] != b'IFZS':
        return False
    if int.from_bytes(data[4:8], 'big') + 8 != len(data):
        return False
    at, chunks = 12, {}
    while at + 8 <= len(data):
        size = int.from_bytes(data[at+4:at+8], 'big')
        end = at + 8 + size
        if end > len(data) or data[at:at+4] in chunks:
            return False
        chunks[data[at:at+4]] = data[at+8:end]
        at = end + (size & 1)
    identity = chunks.get(b'IFhd', b'')
    return (at == len(data) and len(identity) == 13
            and identity[:10] == story[2:4] + story[0x12:0x18] + story[0x1c:0x1e]
            and b'Stks' in chunks and (b'CMem' in chunks or b'UMem' in chunks))


async def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    candidate, server = owned(args.candidate), args.server_root.resolve()
    log = verify_running(candidate)
    meta = json.loads((candidate / 'infocom-save-instance.json').read_text())
    for p, h in meta['source_inputs'].items():
        assert sha(server / p) == h, p
    for p, h in meta['fixture_inputs'].items():
        assert sha(candidate / p) == h, p
    save_root = candidate / meta['save_root']
    assert save_root.resolve().is_relative_to(candidate)
    assert not list(save_root.rglob('*')), 'Fresh isolated save namespace required'
    out = ROOT / 'build/bbs-lab/results/enigma' / args.label
    out.mkdir(parents=True, exist_ok=False)
    stage = out / 'program'
    stage.mkdir()
    binary = ROOT / 'build/terminal/TERMINAL.EXE'
    shutil.copyfile(binary, stage / binary.name)
    inputs = {f'source/{p}': server / p for p in meta['source_inputs']}
    inputs.update({f'candidate/{p}': candidate / p for p in meta['fixture_inputs']})
    inputs.update(terminal=binary, staged_terminal=stage / binary.name,
                  runner=Path(__file__), harness=Path(test_dos.__file__))
    before = {p: sha(f) for p, f in inputs.items()}
    count = messages(candidate)
    inode, offset = log.stat().st_ino, log.stat().st_size
    canonical = json.loads((ROOT / 'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
    prefix = canonical[:canonical.index('M enter')].replace('n p6000 n p3000 enter', 'n p6000 enter')
    keys = prefix + BODY
    assert len('ADDKEY p1000 ' + keys + ' p2000 a-x') < 500
    options = argparse.Namespace(name='enigma', label=args.label, port=PORT,
        com=2, baud=19200, flow='HARD', packet_delay_ms=0, dial_fixture=True,
        directory_fixture=False, directory_browser=False, entry=3, binary=stage / binary.name,
        config_fixture=False, keymap_fixture=ROOT / 'build/keyboard-profiles/NETWORK.KBD',
        server_log=log, keys=keys, wait=2, timeout=190)
    with (out / 'harness.log').open('w') as capture, contextlib.redirect_stdout(capture):
        code = await test_dos.run(options)
    harness = json.loads((out / 'result.json').read_text())
    display = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', (out / 'display.bin').read_bytes()).decode('cp437')
    (out / 'display-clean.txt').write_text(display)
    assert log.stat().st_ino == inode, 'Retain rotated-log attempt'
    with log.open('rb') as f:
        f.seek(offset)
        rows = [json.loads(line) for line in f if line.strip()]
    sessions = {r['sessionId'] for r in rows if r.get('msg') == 'User "loclab" successfully logged in'}
    own = [r for r in rows if r.get('sessionId') in sessions]
    (out / 'server-session.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in own))
    checks = audit(display, (out / 'bbs-sent.bin').read_bytes(), own)
    checks.update(DOS_harness=code == 0 and harness['passed'], unique_session=len(sessions) == 1,
        inputs_unchanged=before == {p: sha(f) for p, f in inputs.items()},
        no_post_saved=count == messages(candidate))
    saves = [p for p in save_root.rglob('*') if p.is_file()]
    story_path = next(candidate / p for p in meta['fixture_inputs'] if p.startswith('local/infocom/'))
    checks['one_valid_story_save'] = len(saves) == 1 and quetzal_identity(saves[0].read_bytes(), story_path.read_bytes())
    with sqlite3.connect(f'file:{candidate / "db/user.sqlite3"}?mode=ro', uri=True) as db:
        user = db.execute("SELECT id FROM user WHERE user_name='loclab'").fetchone()[0]
        namespace = db.execute("SELECT prop_value FROM user_property WHERE user_id=? AND prop_name='loc_zmachine_save_namespace'", (user,)).fetchone()
    checks['synthetic_account_save_namespace'] = bool(namespace) and len(saves) == 1 and saves[0].parent == save_root / (str(user) + '-' + namespace[0]) / meta['story_sha256']
    report = dict(passed=all(checks.values()), checks=checks, input_hashes=before,
        source_revision=meta['source_revision'], story_sha256=meta['story_sha256'],
        saved_files=[dict(path=str(p.relative_to(save_root)), bytes=p.stat().st_size, sha256=sha(p)) for p in saves],
        artifacts={p.name: sha(p) for p in out.iterdir() if p.is_file()},
        scope=meta['scope'] + ' Actual source-built DOS terminal, immediate modeled modem, two worker lifetimes. No physical modem claim.')
    (out / 'infocom-save-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args)))
