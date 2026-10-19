#!/usr/bin/env python3
"""Exercise an explicitly selected owned LAN ENiGMA with an existing probe account.

Run with tools/dev. Private credentials and wire captures stay in ignored build/.
The loopback relay changes only the destination; no buffering or ANSI replies.
Neither the server configuration nor its code is modified. Editor drafts close
unsaved; this runner never submits an editor action menu.
"""
import argparse
import asyncio
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import shutil

import test_dos

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def message_count(server):
    with sqlite3.connect(f"file:{server / 'db/message.sqlite3'}?mode=ro", uri=True) as db:
        return db.execute('SELECT COUNT(*) FROM message').fetchone()[0]


async def run(args):
    os.umask(0o077)
    assert ipaddress.ip_address(args.host).is_private, 'Explicit owned private endpoint required'
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    # Explicit wire fragment, since artwork may split the visible title with
    # SGR changes. Restrict it to literal ASPECT string characters.
    assert re.fullmatch(r'[A-Za-z0-9 \[\]_-]{1,40}', args.main_menu_text)
    server = args.server_root.resolve()
    account = json.loads(args.account_json.read_text())
    password = account['password']
    assert re.fullmatch(r'[A-Za-z0-9]+', password), 'ADDKEY fixture requires alphanumeric probe password'
    # Only the existing regular validation identity; never use a sysop account.
    username = 'PCPlusProbe'
    with sqlite3.connect(f"file:{server / 'db/user.sqlite3'}?mode=ro", uri=True) as db:
        assert db.execute('SELECT user_name FROM user WHERE id=?', (account['userId'],)).fetchone() == (username,), 'Missing or mismatched regular probe identity'
    out = ROOT / 'build/bbs-lab/results/enigma-owned' / args.label
    assert not out.exists(), 'Choose a fresh label to retain previous evidence'
    out.mkdir(parents=True)
    sources = [server / p for p in ('core/client.js', 'core/multi_line_edit_text_view.js',
                                  'config/config.hjson')]
    sources += list((server / 'config/menus').rglob('*.hjson'))
    sources += list((server / 'mods').rglob('*.js'))
    sources += list((server / 'mods').rglob('*.json'))
    binary = ROOT / 'build/terminal/TERMINAL.EXE'
    before = {str(p): sha(p) for p in sources + [binary, Path(__file__), Path(test_dos.__file__)]}
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=server, text=True).strip()
    count_before = message_count(server)
    log = server / 'logs/enigma-bbs.log'
    log_inode, log_offset = log.stat().st_ino, log.stat().st_size
    # Let real DOS ASPECT follow prompts; achievements and newscan make a
    # borrowed timed BIOS login unreliable on this board. Only the later game
    # and editor interactions are supplied as actual BIOS keyboard input.
    stage = out / 'program'
    stage.mkdir()
    for src, name in [('terminal/TERMINAL.EXE','TERMINAL.EXE'),
                      ('aspect-runner/ASPECT.EXE','ASPECT.EXE'),
                      ('aspect-compiler-dos/ASPCOMP.EXE','ASPCOMP.EXE')]:
        shutil.copyfile(ROOT / 'build' / src, stage / name)
    script = ('integer cancel_done, scan_done\r\nproc main\r\ninteger attempts\r\n'
              'cancel_done = 0\r\nscan_done = 0\r\nattempts = 0\r\n'
              'waitfor "lOGIN" 25\r\ntransmit "^M"\r\n'
              'waitfor "PASSW_" 10\r\nwaitquiet 1 10\r\n'
              f'transmit "{username}^M"\r\nwaitquiet 1 10\r\n'
              'when 0 "eyboard" call advance\r\n'
              'when 1 "nAH" call cancel\r\n'
              'when 2 "erform global newscan" call decline\r\n'
              f'transmit "{password}^M"\r\n'
              f'while attempts < 60\r\nwaitfor "{args.main_menu_text}" 1\r\n'
              'if waitfor\r\nexitwhile\r\nendif\r\nattempts += 1\r\nendwhile\r\n'
              'cwhen 0\r\ncwhen 1\r\ncwhen 2\r\nendproc\r\n'
              'proc advance\r\ncwhen 0\r\nwaitquiet 1 5\r\n'
              'when 0 "eyboard" call advance\r\ntransmit "^M"\r\nendproc\r\n'
              'proc cancel\r\nif cancel_done == 0\r\ncancel_done = 1\r\n'
              'cwhen 1\r\nwaitquiet 1 5\r\ntransmit "^["\r\nendif\r\nendproc\r\n'
              'proc decline\r\nif scan_done == 0\r\nscan_done = 1\r\n'
              'cwhen 2\r\nwaitquiet 1 5\r\ntransmit "N"\r\nendif\r\nendproc\r\n')
    (stage / 'LOGON.ASP').write_bytes(script.encode('ascii'))
    staged = {p.name:sha(p) for p in stage.iterdir()}
    directory = test_dos.directory_image
    def bound_directory(**options):
        data = bytearray(directory(**options))
        at = 250 + (options['entry']-1)*114
        data[at+52:at+61] = b'LOGON\0\0\0\0'
        return bytes(data)
    test_dos.directory_image = bound_directory
    login = 'p85000 c-y p300 '
    if args.mode == 'editor':
        canonical = json.loads((ROOT / 'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
        body = canonical[canonical.index('M enter'):].removesuffix(' a-x')
        # Programmatically created validation users have no current message
        # area. Select the conference through its real menu; ENiGMA then picks
        # its configured default writable area, rather than bypassing the UI.
        prefix = 'M enter p5000 P enter'
        assert body.startswith(prefix)
        body = body.replace(prefix, 'M enter p2500 J enter p2000 enter p2500 P enter', 1)
    else:
        body = ('F enter p1800 S enter p1800 B l a s t o c y s t enter p2500 '
                'enter p2000 i p1200 n p1200 down p500 pgdown p500')
    keys = login + body
    assert len('ADDKEY p1000 ' + keys + ' p2000 a-x') < 500
    keymap = ROOT / 'build/keyboard-profiles' / ('ENIGMA.KBD' if args.profile == 'enigma-editor' else 'NETWORK.KBD')
    assert keymap.is_file()
    # Preserve bytes in both directions. The modem's immediate path is unchanged.
    tasks = set()
    async def relay(reader, writer):
        task = asyncio.current_task()
        tasks.add(task)
        peer = None
        try:
            remote, peer = await asyncio.open_connection(args.host, args.port)
            async def pump(src, dst):
                try:
                    while data := await src.read(4096):
                        dst.write(data)
                        await dst.drain()
                finally:
                    dst.close()
            await asyncio.gather(pump(reader, peer), pump(remote, writer))
        except (ConnectionError, OSError):
            pass
        finally:
            writer.close()
            if peer:
                peer.close()
            tasks.discard(task)
    listener = await asyncio.start_server(relay, '127.0.0.1', 0)
    port = listener.sockets[0].getsockname()[1]
    options = argparse.Namespace(name='enigma-owned', label=args.label, port=port,
        com=2, baud=19200, flow='HARD', packet_delay_ms=0, dial_fixture=True,
        directory_fixture=True, directory_browser=False, entry=3, binary=stage/'TERMINAL.EXE',
        config_fixture=False, keymap_fixture=keymap, server_log=None,
        keys=keys, wait=2, timeout=190)
    try:
        # The maintained harness prints its private keyboard recipe. Keep that
        # output solely in this owner-readable ignored capture directory.
        import contextlib
        with (out / 'harness.log').open('w') as capture, contextlib.redirect_stdout(capture):
            code = await test_dos.run(options)
    finally:
        listener.close()
        await listener.wait_closed()
        for task in list(tasks):
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    result = json.loads((out / 'result.json').read_text())
    display = (out / 'display.bin').read_bytes()
    clean = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', display).decode('cp437', errors='replace')
    assert log.stat().st_ino == log_inode, 'Retain run; server log rotated'
    with log.open('rb') as f:
        f.seek(log_offset)
        rows = [json.loads(line) for line in f if line.strip()]
    sessions = {r['sessionId'] for r in rows if r.get('msg') == f'User "{username}" successfully logged in'}
    own = [r for r in rows if r.get('sessionId') in sessions]
    (out / 'server-session.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in own))
    checks = dict(DOS_harness=code == 0 and result['passed'],
        authenticated_probe=len(sessions) == 1,
        main_menu=args.main_menu_text in clean,
        inputs_unchanged=before == {str(p): sha(p) for p in sources + [binary, Path(__file__), Path(test_dos.__file__)]},
        no_post_saved=not any('posted message to' in r.get('msg', '') for r in own))
    checks['staged_products_unchanged'] = all(sha(stage/name)==digest for name,digest in staged.items())
    checks['DOS_source_compiled'] = (stage/'LOGON.ASX').is_file()
    if args.mode == 'files':
        pages = [tuple(map(int, p)) for p in re.findall(r'NFO \| lines (\d+)-(\d+)/(\d+)', clean)]
        checks.update(game_details='GAME DETAILS' in clean and 'Blastocyst' in clean,
                      diz_page=bool(re.search(r'FILE_ID[.]DIZ \| lines \d+-\d+/\d+', clean)),
                      nfo_page=bool(pages),
                      nfo_scrolled=len(pages)>1 and pages[-1][0]>pages[0][0]
                                   and pages[-1][1]==pages[-1][2])
    else:
        positions = [(int(r), int(c)) for r,c in re.findall(r'(?:INS|OVR) (\d+),(\d+)', clean[clean.find('KEYTEST'):])]
        checks.update(editor_entered='KEYTEST' in clean and bool(positions),
            home_moves_before_marker=positions[:7] == [(1,2),(1,3),(1,4),(1,5),(1,6),(1,1),(1,2)],
            insert_toggled_overtype='OVR ' in clean)
    report = dict(passed=all(checks.values()), checks=checks, mode=args.mode,
        endpoint=dict(address=args.host, port=args.port), server_revision=revision,
        server_root=str(server), binary_sha256=sha(binary), keymap_sha256=sha(keymap),
        keyboard_profile=args.profile, main_menu_text=args.main_menu_text,
        modem_packet_delay_ms=0, input_hashes=before,
        message_count_before=count_before, message_count_after=message_count(server),
        scope='Actual source-built DOS terminal through immediate modeled UART/modem and byte-transparent local relay to an explicitly owned LAN ENiGMA. Existing regular validation account. No code/config changes, no submitted messages, no physical modem claim.')
    (out / 'owned-server-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:report[k] for k in ('passed','checks','mode','server_revision','keyboard_profile')}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server-root', type=Path, required=True)
    parser.add_argument('--account-json', type=Path, required=True)
    parser.add_argument('--host', required=True)
    parser.add_argument('--port', type=int, default=2323)
    parser.add_argument('--label', required=True)
    parser.add_argument('--mode', choices=['files', 'editor'], required=True)
    parser.add_argument('--profile', choices=['network', 'enigma-editor'], default='network')
    parser.add_argument('--main-menu-text', default='Main Menu',
                        help='Literal contiguous wire fragment identifying the configured main menu')
    raise SystemExit(asyncio.run(run(parser.parse_args())))
