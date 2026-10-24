#!/usr/bin/env python3
"""Isolated ENiGMA width menu using unchanged source checkout and synthetic users.

Use tools/bbs-dev. No existing listener, board configuration or database is edited.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import sqlite3
import subprocess
import time

from enigma_key_stream_fixture import ROOT, STOCK, owned, pid

PORT = 23239


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup(candidate, decoder_candidate=None):
    candidate = owned(candidate)
    assert not candidate.exists(), 'Use a fresh fixture directory'
    with sqlite3.connect(f'file:{STOCK}/db/user.sqlite3?mode=ro', uri=True) as db:
        assert {r[0] for r in db.execute('SELECT user_name FROM user')} == {'locadmin', 'loclab'}
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=STOCK), 'Source checkout must be clean'
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=STOCK, text=True).strip()
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=STOCK).split(b'\0')
    candidate.mkdir(parents=True)
    inputs = {}
    for value in tracked:
        if not value:
            continue
        rel = Path(os.fsdecode(value))
        assert not rel.is_absolute() and '..' not in rel.parts
        source = STOCK / rel
        assert source.is_file() and not source.is_symlink(), str(rel)
        inputs[str(rel)] = sha(source)
        target = candidate / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    # Existing installed dependencies are shared read-only by convention; npm is
    # never invoked on the candidate. Mutable board state is copied separately.
    (candidate / 'node_modules').symlink_to(STOCK / 'node_modules', target_is_directory=True)
    shutil.copytree(STOCK / 'config', candidate / 'config', dirs_exist_ok=True)
    for source in sorted((STOCK / 'db').rglob('*.sqlite3')):
        target = candidate / 'db' / source.relative_to(STOCK / 'db')
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(f'file:{source}?mode=ro', uri=True) as original, sqlite3.connect(target) as copy:
            original.backup(copy)
            assert copy.execute('PRAGMA integrity_check').fetchone() == ('ok',)
    for directory in ['logs', 'drop', 'db/mods', 'file_base', 'helpers']:
        (candidate / directory).mkdir(parents=True, exist_ok=True)
    helper = STOCK.parent / 'helpers/sexyz'
    shutil.copy2(helper, candidate / 'helpers/sexyz')
    config_text = (STOCK / 'config/config.hjson').read_text()
    config_text = config_text.replace(str(STOCK.parent / 'helpers'), str(candidate / 'helpers'))
    config_text = config_text.replace(str(STOCK), str(candidate))
    config = json.loads(config_text)
    assert 'paths' not in config
    config['loginServers']['telnet'].update(address='127.0.0.1', port=PORT)
    assert not config['loginServers']['ssh']['enabled']
    assert not config['loginServers']['webSocket']['ws']['enabled']
    assert not config['loginServers']['webSocket']['wss']['enabled']
    config['general']['boardName'] = config['general']['prettyBoardName'] = 'LoC Width Lab'
    (candidate / 'config/config.hjson').write_text(json.dumps(config, indent=2) + '\n')
    menu = candidate / 'config/menus/loc-main.hjson'
    parse = "const fs=require('fs'),h=require(process.argv[1]+'/node_modules/hjson');process.stdout.write(JSON.stringify(h.parse(fs.readFileSync(process.argv[2],'utf8'))));"
    document = json.loads(subprocess.check_output(['node', '-e', parse, str(candidate), str(menu)], text=True))
    document['menus']['mainMenu']['submit'].insert(0, dict(value=dict(command='WIDTH'), action='@menu:pcplusWidthProbe'))
    document['menus']['pcplusWidthProbe'] = dict(desc='Synthetic width and arrows', module='@userModule:pcplus_width', config=dict(interrupt='never'))
    menu.write_text(json.dumps(document, indent=2) + '\n')
    module = candidate / 'mods/pcplus_width/pcplus_width.js'
    module.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / 'lab/bbs/peer_width_module.js', module)
    decoder_inputs = {}
    if decoder_candidate:
        decoder_candidate = owned(decoder_candidate)
        report_path = decoder_candidate.parent / 'report.json'
        report = json.loads(report_path.read_text())
        assert report['passed'] and report['stock_client_unchanged']
        assert report['upstream_revision'] == revision
        assert report['stock_client_sha256'] == sha(STOCK / 'core/client.js')
        for name, key in [('core/client.js', 'candidate_client_sha256'),
                          ('core/key_stream.js', 'candidate_key_stream_sha256')]:
            assert sha(decoder_candidate / name) == report[key]
            shutil.copyfile(decoder_candidate / name, candidate / name)
            decoder_inputs[name] = report[key]
    assert all(sha(STOCK / rel) == digest for rel, digest in inputs.items())
    metadata = dict(candidate=str(candidate), address='127.0.0.1', port=PORT, revision=revision,
                    source_inputs=inputs, decoder_inputs=decoder_inputs,
                    decoder_report_sha256=sha(report_path) if decoder_candidate else None,
                    module_sha256=sha(module), config_sha256=sha(candidate / 'config/config.hjson'),
                    menu_sha256=sha(menu), scope='Clean ENiGMA checkout plus explicit synthetic menu and optional checked decoder candidate; private runtime/database copies; installed dependencies shared; no live board changes')
    (candidate / 'peer-width-instance.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(dict(candidate=str(candidate), revision=revision, port=PORT, source_files=len(inputs))))


def verify(candidate):
    candidate = owned(candidate)
    data = json.loads((candidate / 'peer-width-instance.json').read_text())
    assert data['candidate'] == str(candidate) and data['address'] == '127.0.0.1' and data['port'] == PORT
    assert sha(candidate / 'config/config.hjson') == data['config_sha256']
    assert sha(candidate / 'config/menus/loc-main.hjson') == data['menu_sha256']
    assert sha(candidate / 'mods/pcplus_width/pcplus_width.js') == data['module_sha256']
    # Config/menu are explicitly changed; all remaining upstream source is exact.
    for rel, digest in data['source_inputs'].items():
        if rel in ('config/config.hjson', 'config/menus/loc-main.hjson'):
            continue
        assert sha(candidate / rel) == data.get('decoder_inputs', {}).get(rel, digest), rel
    for rel, digest in data.get('decoder_inputs', {}).items():
        assert sha(candidate / rel) == digest, rel
    return data


def start(candidate):
    verify(candidate)
    assert not pid(candidate)
    node = shutil.which('node')
    assert node and str(Path(node).resolve()).startswith('/nix/store/')
    with socket.socket() as check:
        check.bind(('127.0.0.1', PORT))
    with (candidate / 'instance.log').open('ab') as log:
        process = subprocess.Popen([node, str(candidate / 'main.js')], cwd=candidate,
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
    (candidate / 'instance.pid').write_text(str(process.pid) + '\n')
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        assert process.poll() is None, 'Inspect instance.log'
        try:
            with socket.create_connection(('127.0.0.1', PORT), timeout=.1):
                print(f'Owned width fixture pid {process.pid}, 127.0.0.1:{PORT}')
                return
        except OSError:
            time.sleep(.1)
    raise TimeoutError('Fixture did not listen')


def stop(candidate):
    value = pid(candidate)
    if value:
        os.kill(value, signal.SIGTERM)
        for _ in range(50):
            if not pid(candidate):
                break
            time.sleep(.1)
        if pid(candidate):
            os.kill(value, signal.SIGKILL)
    (candidate / 'instance.pid').unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['setup', 'start', 'stop', 'verify'])
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--decoder-candidate', type=Path,
                        help='Setup only: explicitly compose a previously checked incremental decoder')
    args = parser.parse_args()
    assert not args.decoder_candidate or args.action == 'setup'
    if args.action == 'setup':
        setup(owned(args.candidate), args.decoder_candidate)
    else:
        globals()[args.action](owned(args.candidate))
