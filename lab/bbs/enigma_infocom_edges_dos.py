#!/usr/bin/env python3
"""Actual DOS save-dialog cancellation, overwrite and malformed-restore routes."""
import argparse
import asyncio
import contextlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys

import test_dos
from enigma_key_stream_fixture import ROOT, PORT, owned, verify_running, sha
from enigma_notes_dos import messages
from enigma_infocom_save_dos import quetzal_identity
from enigma_infocom_probe import ordered
from enigma_script_login import source as login_source

COMMANDS = {
    'cancel': ['ZORK', 'save', 'CANCEL', 'save', '../x', 'CANCEL', 'restore', 'missing', 'look', 'quit', 'y'],
    'overwrite': ['ZORK', 'north', 'save', 'locprobe', 'restart', 'y', 'save', 'locprobe', 'north', 'quit', 'y',
                  'ZORK', 'north', 'restore', 'locprobe', 'look', 'quit', 'y'],
    'corrupt': ['ZORK', 'north', 'restore', 'broken', 'look', 'restore', 'locprobe', 'look', 'quit', 'y'],
}


def audit(mode, display, wire, rows):
    checks = dict(commands_emitted=ordered(wire, [command.encode() + b'\r' for command in COMMANDS[mode]]) is not None,
        no_worker_errors=not any('zmachine' in row.get('msg', '').lower() and
            ('error' in row['msg'].lower() or 'non-zero' in row['msg'].lower()) for row in rows),
        menu_return=display.count('Main Menu') >= (3 if mode == 'overwrite' else 2))
    lifecycle = [row['msg'] for row in rows if row.get('name') == 'PCPlus-Zork-Save-Probe' and
        row.get('msg') in ('Z-Machine VM ready', 'Z-Machine VM stopped')]
    checks['complete_worker_lifecycles'] = lifecycle == ['Z-Machine VM ready', 'Z-Machine VM stopped'] * (2 if mode == 'overwrite' else 1)
    if mode == 'cancel':
        checks['cancel_invalid_and_missing_return_to_game'] = ordered(display, ['West of House', 'Save name [save]',
            'Save name [save]', 'Use letters, numbers', 'Save name [save]', 'Restore name [save]', 'West of House']) is not None
    elif mode == 'overwrite':
        checks['overwrite_and_cross_worker_restore'] = ordered(display, ['West of House', 'North of House',
            'Save name [save]', 'West of House', 'Save name [save]', 'North of House',
            'West of House', 'North of House', 'Restore name [save]', 'West of House', 'West of House']) is not None
    else:
        checks['rejected_corruption_preserves_game_and_valid_restore'] = ordered(display, ['West of House', 'North of House',
            'Restore name [save]', 'Cannot restore this save file.', 'North of House',
            'Restore name [save]', 'West of House', 'West of House']) is not None
    return checks


async def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    candidate = owned(args.candidate)
    log = verify_running(candidate)
    meta = json.loads((candidate / 'infocom-save-instance.json').read_text())
    assert meta['save_read_experiment']
    for name, digest in meta['source_inputs'].items():
        assert sha(args.server_root / name) == digest
    for name, digest in meta['fixture_inputs'].items():
        assert sha(candidate / name) == digest
    root = candidate / meta['save_root']
    story_path = next(candidate / name for name in meta['fixture_inputs'] if name.startswith('local/infocom/'))
    story = story_path.read_bytes()
    initial = [path for path in root.rglob('*') if path.is_file()]
    if args.mode != 'corrupt':
        assert not initial, 'Fresh save data required before cancel/overwrite'
    else:
        assert len(initial) == 1 and initial[0].name == 'locprobe.glksave' and quetzal_identity(initial[0].read_bytes(), story)
    out = ROOT / 'build/bbs-lab/results/enigma' / args.label
    out.mkdir(parents=True, exist_ok=False)
    good_before = {str(path.relative_to(root)): sha(path) for path in initial}
    if args.mode == 'corrupt':
        broken = initial[0].with_name('broken.glksave')
        with broken.open('xb') as stream:
            stream.write(b'not a Quetzal save\n')
        shutil.copyfile(broken, out / 'broken-fixture.bin')
    stage = out / 'program'
    stage.mkdir()
    inputs = {f'candidate/{name}': candidate / name for name in meta['fixture_inputs']}
    inputs.update({f'source/{name}': args.server_root / name for name in meta['source_inputs']})
    for rel in ('terminal/TERMINAL.EXE', 'aspect-runner/ASPECT.EXE', 'aspect-compiler-dos/ASPCOMP.EXE'):
        path = ROOT / 'build' / rel
        shutil.copyfile(path, stage / path.name)
        inputs[rel] = path
        inputs['staged/' + path.name] = stage / path.name
    script = login_source()
    (stage / 'LOGON.ASP').write_bytes(script.replace('\n', '\r\n').encode('ascii'))
    inputs.update(runner=Path(__file__), harness=Path(test_dos.__file__), login=stage / 'LOGON.ASP')
    before = {name: sha(path) for name, path in inputs.items()}
    original_directory = test_dos.directory_image
    def directory(**kwargs):
        data = bytearray(original_directory(**kwargs))
        at = 250 + (kwargs['entry'] - 1) * 114
        data[at+52:at+61] = b'LOGON\0\0\0\0'
        return bytes(data)
    keys = 'p85000 c-y '
    for command in COMMANDS[args.mode]:
        keys += ' '.join(command) + ' enter ' + ('p3000 ' if command == 'ZORK' else 'p1600 ')
    assert len('ADDKEY p1000 ' + keys + ' p2000 a-x') < 500
    options = argparse.Namespace(name='enigma', label=args.label, port=PORT, com=2, baud=19200, flow='HARD',
        packet_delay_ms=0, dial_fixture=True, directory_fixture=True, directory_browser=False, entry=3,
        binary=stage / 'TERMINAL.EXE', config_fixture=False, keymap_fixture=ROOT / 'build/keyboard-profiles/NETWORK.KBD',
        server_log=log, keys=keys, wait=2, timeout=230)
    snapshots = []
    finished = asyncio.Event()
    async def watch():
        while not finished.is_set():
            if args.mode == 'overwrite':
                for path in root.rglob('locprobe.glksave'):
                    try:
                        data = path.read_bytes()
                        if quetzal_identity(data, story):
                            import hashlib
                            digest = hashlib.sha256(data).hexdigest()
                            if not snapshots or snapshots[-1]['sha256'] != digest:
                                target = out / ('save-' + str(len(snapshots)) + '.glksave')
                                target.write_bytes(data)
                                snapshots.append(dict(path=str(path.relative_to(root)), sha256=digest, bytes=len(data), snapshot=target.name))
                    except OSError:
                        pass
            await asyncio.sleep(.05)
    task = asyncio.create_task(watch())
    count = messages(candidate)
    inode, offset = log.stat().st_ino, log.stat().st_size
    test_dos.directory_image = directory
    try:
        with (out / 'harness.log').open('w') as capture, contextlib.redirect_stdout(capture):
            code = await test_dos.run(options)
    finally:
        test_dos.directory_image = original_directory
        finished.set()
        await task
    harness = json.loads((out / 'result.json').read_text())
    wire = (out / 'bbs-sent.bin').read_bytes()
    display = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', (out / 'display.bin').read_bytes()).decode('cp437')
    (out / 'display-clean.txt').write_text(display)
    assert log.stat().st_ino == inode
    with log.open('rb') as stream:
        stream.seek(offset)
        rows = [json.loads(line) for line in stream if line.strip()]
    sessions = {row['sessionId'] for row in rows if row.get('msg') == 'User "loclab" successfully logged in'}
    own = [row for row in rows if row.get('sessionId') in sessions]
    (out / 'server-session.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in own))
    checks = audit(args.mode, display, wire, own)
    sys.path.insert(0, str(ROOT / 'src/aspect'))
    from compiler import compile_source
    checks.update(DOS_harness=code == 0 and harness['passed'], unique_session=len(sessions) == 1,
        inputs_unchanged=before == {name: sha(path) for name, path in inputs.items()}, no_post_saved=count == messages(candidate),
        DOS_compiler_exact=(stage / 'LOGON.ASX').read_bytes() == compile_source(script),
        scripted_login=(stage / 'LOGIN.LOG').read_bytes() == b'STARTAUTHREADY')
    saves = [path for path in root.rglob('*') if path.is_file()]
    if args.mode == 'cancel':
        checks['no_file_created'] = not saves
    elif args.mode == 'overwrite':
        checks['two_valid_different_saves_same_path'] = len(snapshots) == 2 and snapshots[0]['path'] == snapshots[1]['path'] and snapshots[0]['sha256'] != snapshots[1]['sha256']
        checks['one_valid_final_save'] = len(saves) == 1 and quetzal_identity(saves[0].read_bytes(), story) and sha(saves[0]) == snapshots[-1]['sha256']
    else:
        checks['good_save_unchanged'] = all(sha(root / name) == digest for name, digest in good_before.items())
        checks['only_known_save_fixtures'] = {path.name for path in saves} == {'locprobe.glksave', 'broken.glksave'} and broken.read_bytes() == (out / 'broken-fixture.bin').read_bytes()
    with sqlite3.connect(f'file:{candidate / "db/user.sqlite3"}?mode=ro', uri=True) as db:
        user = db.execute("SELECT id FROM user WHERE user_name='loclab'").fetchone()[0]
        namespace = db.execute("SELECT prop_value FROM user_property WHERE user_id=? AND prop_name='loc_zmachine_save_namespace'", (user,)).fetchone()[0]
    checks['all_files_in_owned_namespace'] = all(path.parent == root / (str(user) + '-' + namespace) / meta['story_sha256'] for path in saves)
    result = dict(passed=all(checks.values()), mode=args.mode, checks=checks, input_hashes=before, snapshots=snapshots,
        saved_files=[dict(path=str(path.relative_to(root)), bytes=path.stat().st_size, sha256=sha(path)) for path in saves],
        scope='Actual source-built DOS terminal, DOS-compiled ASPECT login and exact owned door with explicit save-read candidate. Isolated namespace/direct ZORK route, modeled19200/HARD UART; no live or physical claim.')
    (out / 'infocom-edge-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks), indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--mode', choices=COMMANDS, required=True)
    raise SystemExit(asyncio.run(run(parser.parse_args())))
