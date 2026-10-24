#!/usr/bin/env python3
"""Own a separate loopback Synchronet instance with a synthetic width shell."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
STOCK = ROOT / 'build/bbs-lab/synchronet/runtime'
PORT = 23240
RUNTIME_STATE = {'ctrl/node.dab', 'ctrl/sbbs.pid', 'ctrl/recycle', 'ctrl/dsts.ini', 'ctrl/csts.tab'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def owned(candidate):
    candidate = candidate.resolve()
    assert candidate.is_relative_to(ROOT / 'build') and candidate != STOCK
    return candidate


def pid(candidate):
    try:
        value = int((candidate / 'instance.pid').read_text())
        command = Path(f'/proc/{value}/cmdline').read_bytes()
        if str(candidate / 'ctrl').encode() in command:
            return value
    except (FileNotFoundError, ValueError, ProcessLookupError):
        pass
    return None


def setup(candidate):
    assert not candidate.exists(), 'Use a fresh fixture directory'
    # Only copy the known synthetic lab; never accept a user-supplied board root.
    provenance = json.loads((STOCK.parent / 'provenance.json').read_text())
    assert provenance['account']['name'] == 'LABUSER' and provenance['account']['synthetic']
    immutable = {str(p.relative_to(STOCK)): sha(p) for folder in ['ctrl', 'exec', 'mods']
                 for p in (STOCK / folder).rglob('*') if p.is_file() and str(p.relative_to(STOCK)) not in RUNTIME_STATE}
    # The official archive has three self-referential GTK resource links.
    # Preserve those inert links and reject any link into external runtime data.
    links = {str(p.relative_to(STOCK)): str(p.readlink()) for p in STOCK.rglob('*') if p.is_symlink()}
    assert links == {f'exec/{name}.glade': f'{name}.glade'
                     for name in ['gtkmonitor', 'gtkuseredit', 'gtkuserlist']}, links
    def ignore_runtime_endpoints(directory, names):
        return [name for name in names if not any((check(Path(directory) / name)
                for check in (Path.is_file, Path.is_dir, Path.is_symlink)))]
    shutil.copytree(STOCK, candidate, symlinks=True, ignore=ignore_runtime_endpoints)
    assert immutable == {rel: sha(STOCK / rel) for rel in immutable}, 'Lab source changed during copy'
    environment = dict(os.environ, SBBSCTRL=str(candidate / 'ctrl'))
    query = candidate / 'width-users.js'
    query.write_text("var a=[];for(var i=1;i<=system.lastuser;i++){var u=new User(i);if(u.alias)a.push(u.alias);}print('WIDTH_USERS='+JSON.stringify(a));\n")
    output = subprocess.check_output([str(candidate / 'exec/jsexec'), '-n', str(query)],
                                     env=environment, cwd=candidate, text=True, stderr=subprocess.STDOUT)
    users = [json.loads(line.split('=', 1)[1]) for line in output.splitlines() if line.startswith('WIDTH_USERS=')]
    assert users == [['LABUSER']], 'Only the synthetic LABUSER may enter this fixture'
    # The shell wrapper is selected by the standard mods-before-exec lookup.
    wrapper = candidate / 'mods/default.js'
    assert not wrapper.exists(), 'Unexpected pre-existing shell override'
    shutil.copyfile(ROOT / 'lab/bbs/synchronet_peer_width_module.js', wrapper)
    config = candidate / 'ctrl/sbbs.ini'
    text = config.read_text().replace(str(STOCK), str(candidate))
    assert text.count('TelnetPort=23231') == 1
    text = text.replace('TelnetPort=23231', f'TelnetPort={PORT}')
    assert 'Interface=127.0.0.1' in text and 'TelnetInterface=127.0.0.1' in text
    assert all(f'[{name}]\nAutoStart=false' in text for name in ['FTP', 'Mail', 'Web', 'Services'])
    config.write_text(text)
    # All remaining paths are relative to the private runtime. Reject escaped
    # source paths rather than sharing mutable DB/node/temp state.
    for p in (candidate / 'ctrl').glob('*.ini'):
        assert str(STOCK) not in p.read_text(errors='replace'), str(p)
    inputs = {str(p.relative_to(candidate)): sha(p) for folder in ['ctrl', 'exec', 'mods']
              for p in (candidate / folder).rglob('*') if p.is_file() and str(p.relative_to(candidate)) not in RUNTIME_STATE}
    metadata = dict(candidate=str(candidate), address='127.0.0.1', port=PORT,
                    upstream_provenance_sha256=sha(STOCK.parent / 'provenance.json'),
                    source_inputs=immutable, fixture_inputs=inputs, synthetic_users=users[0],
                    mutable_control_state=sorted(RUNTIME_STATE),
                    scope='Private copy of official Synchronet lab runtime; explicit synthetic command shell; normal stock shell on return; no live-board changes')
    (candidate / 'peer-width-instance.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(dict(candidate=str(candidate), port=PORT, synthetic_users=users[0])))


def verify(candidate):
    metadata = json.loads((candidate / 'peer-width-instance.json').read_text())
    assert metadata['candidate'] == str(candidate) and metadata['address'] == '127.0.0.1' and metadata['port'] == PORT
    for rel, digest in metadata['fixture_inputs'].items():
        assert sha(candidate / rel) == digest, rel


def start(candidate):
    verify(candidate)
    assert not pid(candidate)
    with socket.socket() as check:
        check.bind(('127.0.0.1', PORT))
    environment = dict(os.environ, SBBSCTRL=str(candidate / 'ctrl'))
    with (candidate / 'instance.log').open('ab') as log:
        process = subprocess.Popen([str(candidate / 'exec/sbbs'), 'nd', 't!', 'ne', 'nh', str(candidate / 'ctrl')],
                                   cwd=candidate, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=log, start_new_session=True)
    (candidate / 'instance.pid').write_text(str(process.pid) + '\n')
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        assert process.poll() is None, 'Inspect instance.log'
        try:
            with socket.create_connection(('127.0.0.1', PORT), timeout=.1):
                print(f'Owned Synchronet width fixture pid {process.pid}, 127.0.0.1:{PORT}')
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
    args = parser.parse_args()
    globals()[args.action](owned(args.candidate))
