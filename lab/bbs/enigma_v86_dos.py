#!/usr/bin/env python3
"""Exercise owned DOS doors through the source-built DOS terminal, never live images."""
import argparse
import asyncio
import contextlib
import json
from pathlib import Path
import re
import shutil
import sys

import test_dos
from enigma_key_stream_fixture import ROOT, PORT, owned, verify_running, sha
from enigma_v86_fixture import state
from enigma_notes_dos import messages
from enigma_script_login import source as login_source
from enigma_infocom_probe import ordered


def audit(game, display, wire, rows):
    door = 'LoC-gwar' if game == 'gwar' else 'LoC-bre'
    lifecycle = [row['msg'] for row in rows if row.get('name') == door and
                 row.get('msg') in ('v86 emulator ready', 'v86 emulator stopped')]
    menus = '\n'.join(row['menuName'] for row in rows if row.get('menuName'))
    checks = dict(complete_worker_lifecycle=lifecycle == ['v86 emulator ready', 'v86 emulator stopped'],
        menu_route=ordered(menus, ['mainMenu', 'doorsMainMenu',
            'locGlobalWar' if game == 'gwar' else 'locBarrenRealms', 'doorsMainMenu', 'mainMenu']) is not None,
        no_worker_errors=not any('v86' in row.get('msg', '').lower() and
            any(word in row['msg'].lower() for word in ('error', 'non-zero')) for row in rows),
        normal_return_before_disconnect=not any('disconnected' in row.get('msg', '').lower() and
            'v86' in row['msg'].lower() for row in rows))
    if game == 'gwar':
        checks['game_instructions_pager_and_quit'] = ordered(display, ['Global War v2.7',
            'Selection?', 'ABOUT GLOBAL WAR', 'More? (Y/N)', 'Selection?',
            'Returning to LoSs oF CoNtRoL', 'D O S   D O O R S', 'Main Menu']) is not None
        checks['commands_emitted'] = ordered(wire, [b'D\r', b'1\r', b'\r', b'I\r', b'N\r', b'Q\r', b'Q\r']) is not None
    else:
        checks['realm_creation_and_quit'] = ordered(display, ['Barren Realms Elite',
            'Name your Realm:', 'LoC Lab', 'Name Your Empire', 'Instructions?',
            '[Barren Realms Elite]', 'Quit', 'D O S   D O O R S', 'Main Menu']) is not None
        checks['commands_emitted'] = ordered(wire, [b'D\r', b'2\r', b'LoC Lab\r', b'Y', b'N', b'0\r', b'Q\r']) is not None
    return checks


async def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    candidate = owned(args.candidate)
    log = verify_running(candidate)
    meta = json.loads((candidate / 'v86-door-instance.json').read_text())
    inputs = {f'candidate/{name}': candidate / name for name in meta['fixture_inputs']}
    inputs.update({f'source/{name}': args.server_root / name for name in meta['source_inputs']})
    inputs.update({f'dependency/{name}': candidate / 'node_modules' / name for name in meta['dependency_inputs']})
    for name, digest in meta['fixture_inputs'].items():
        assert sha(candidate / name) == digest
    for name, digest in meta['source_inputs'].items():
        assert sha(args.server_root / name) == digest
    for name, digest in meta['dependency_inputs'].items():
        assert sha(candidate / 'node_modules' / name) == digest
    assert all(state(args.server_root / name) == value for name, value in meta['source_images'].items())
    out = ROOT / 'build/bbs-lab/results/enigma' / args.label
    out.mkdir(parents=True, exist_ok=False)
    stage = out / 'program'
    stage.mkdir()
    for rel in ('terminal/TERMINAL.EXE', 'aspect-runner/ASPECT.EXE', 'aspect-compiler-dos/ASPCOMP.EXE'):
        path = ROOT / 'build' / rel
        shutil.copyfile(path, stage / path.name)
        inputs[rel] = path
        inputs['staged/' + path.name] = stage / path.name
    script = login_source()
    (stage / 'LOGON.ASP').write_bytes(script.replace('\n', '\r\n').encode('ascii'))
    inputs.update(runner=Path(__file__), harness=Path(test_dos.__file__), login=stage / 'LOGON.ASP',
        fixture=ROOT / 'lab/bbs/enigma_v86_fixture.py',
        keymap=ROOT / 'build/keyboard-profiles/NETWORK.KBD')
    before = {name: sha(path) for name, path in inputs.items()}
    images_before = {name: state(candidate / name) for name in meta['initial_images']}
    original_directory = test_dos.directory_image
    def directory(**kwargs):
        data = bytearray(original_directory(**kwargs))
        at = 250 + (kwargs['entry'] - 1) * 114
        data[at+52:at+61] = b'LOGON\0\0\0\0'
        return bytes(data)
    keys = 'p85000 c-y D enter p3000 '
    if args.game == 'gwar':
        keys += '1 enter p20000 enter p4000 I enter p4000 N enter p4000 Q enter p25000 enter p2000 enter p2000 Q enter p3000 '
    else:
        keys += '2 enter p20000 L o C space L a b enter p2500 Y p2500 N p3000 enter p5000 0 enter p5000 enter p15000 enter p2000 enter p2000 Q enter p3000 '
    assert len('ADDKEY p1000 ' + keys + ' p2000 a-x') < 500
    options = argparse.Namespace(name='enigma', label=args.label, port=PORT, com=2, baud=19200, flow='HARD',
        packet_delay_ms=0, dial_fixture=True, directory_fixture=True, directory_browser=False, entry=3,
        binary=stage / 'TERMINAL.EXE', config_fixture=False, keymap_fixture=inputs['keymap'],
        server_log=log, keys=keys, wait=2, timeout=280)
    count = messages(candidate)
    inode, offset = log.stat().st_ino, log.stat().st_size
    test_dos.directory_image = directory
    try:
        with (out / 'harness.log').open('w') as capture, contextlib.redirect_stdout(capture):
            code = await test_dos.run(options)
    finally:
        test_dos.directory_image = original_directory
    # Give an explicit disconnect shutdown/serialized disk flush time to settle.
    # Such a shutdown still fails the normal-return check.
    await asyncio.sleep(3)
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
    checks = audit(args.game, display, wire, own)
    sys.path.insert(0, str(ROOT / 'src/aspect'))
    from compiler import compile_source
    checks.update(DOS_harness=code == 0 and harness['passed'], unique_session=len(sessions) == 1,
        inputs_unchanged=before == {name: sha(path) for name, path in inputs.items()},
        original_images_unchanged=all(state(args.server_root / name) == value for name, value in meta['source_images'].items()),
        no_post_saved=count == messages(candidate),
        DOS_compiler_exact=(stage / 'LOGON.ASX').read_bytes() == compile_source(script),
        scripted_login=(stage / 'LOGIN.LOG').read_bytes() == b'STARTAUTHREADY')
    result = dict(passed=all(checks.values()), game=args.game, checks=checks, input_hashes=before,
        images_before=images_before, images_after={name: state(candidate / name) for name in meta['initial_images']},
        scope='Actual source-built DOS terminal and DOS-compiled login, owned v86 worker/menu and private writable game-image clones. Modeled COM2/19200/HARD; no live deployment, physical modem or complete game assertion.')
    (out / 'v86-door-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks), indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--game', choices=['gwar', 'bre'], required=True)
    raise SystemExit(asyncio.run(run(parser.parse_args())))
