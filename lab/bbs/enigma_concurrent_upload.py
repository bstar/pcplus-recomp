#!/usr/bin/env python3
"""Two real loopback ENiGMA sessions: cancel/retry A while upload B stays active.

The declared reference peers generate protocol/input bytes. This is server
concurrency acceptance, not an additional DOS or physical-modem assertion.
"""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time

from enigma_key_stream_fixture import ROOT, PORT, owned, pid, verify_running, sha
from enigma_upload_dos import metadata
from enigma_notes_dos import messages
import synchronet
from audit_zmodem import scan, audit_batch

sys.path.insert(0, str(ROOT / 'standalone'))
from check_zmodem_wire import header, packet

PEER_NAME = 'locpeer'
PEER_PASSWORD = 'LoC-Peer-2026!'


def setup(candidate):
    assert not pid(candidate)
    fixture = json.loads((candidate / 'search-instance.json').read_text())
    assert fixture['upload_fixture'] and fixture['transfer_owner_experiment']
    marker = candidate / 'concurrent-upload-instance.json'
    assert not marker.exists()
    code = r'''const c=require('./core/oputil/oputil_common');
c.initConfigAndDatabases(e=>{if(e)throw e;
const U=require('./core/user'),P=require('./core/user_property');
U.getUserIdAndName('locpeer',(e,id)=>{if(!e&&id)return process.exit(0);
const u=new U();u.username='locpeer';
u.properties[P.RealName]='Local Concurrent Test';u.properties[P.Location]='Loopback';
u.properties[P.ThemeId]='luciano_blocktronics';u.properties[P.TermWidth]=80;u.properties[P.TermHeight]=25;
u.create({password:'LoC-Peer-2026!',sessionId:'pcplus-concurrent-lab'},e=>{if(e)throw e;process.exit(0);});});});'''
    subprocess.run(['node', '-e', code], cwd=candidate, check=True)
    with sqlite3.connect(candidate / 'db/user.sqlite3') as db:
        users = list(db.execute('SELECT id,user_name FROM user ORDER BY id'))
    assert {name for _, name in users} == {'locadmin', 'loclab', PEER_NAME}
    marker.write_text(json.dumps(dict(synthetic_users=users, setup_sha256=sha(Path(__file__)),
        scope='Additional regular synthetic loopback peer; no live user copied.'), indent=2) + '\n')
    print('Prepared synthetic concurrent peer')


class Peer(synchronet.Peer):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.session = None
        self.scan_from = 0

    def plain(self, data):
        self.text.extend(data)
        self.history.extend(data)
        while b'\x1b[6n' in self.text[self.scan_from:]:
            at = self.text.find(b'\x1b[6n', self.scan_from)
            self.scan_from = at + 4
            self.send(b'\x1b[1;1R', 'declared reference CPR home')

    def application(self, data, label):
        self.send(data.replace(b'\xff', b'\xff\xff'), label)


class Lab:
    def __init__(self, candidate, output):
        self.candidate, self.output = candidate, output
        self.log = verify_running(candidate)
        self.inode, self.offset = self.log.stat().st_ino, self.log.stat().st_size
        self.peers = []
        self.keep = None
        self.checks = {}
        self.snapshots = []
        self.forms = []
        self.interrupts = []

    def rows(self, peer=None):
        assert self.log.stat().st_ino == self.inode
        with self.log.open('rb') as stream:
            stream.seek(self.offset)
            rows = [json.loads(line) for line in stream if line.strip()]
        return [row for row in rows if row.get('sessionId') == peer.session] if peer else rows

    def menu(self, peer):
        menus = [row['menuName'] for row in self.rows(peer) if row.get('menuName')]
        return menus[-1] if menus else None

    def check(self, name, condition):
        assert condition, name
        self.checks[name] = True
        print(name, flush=True)

    def tick(self):
        for peer in self.peers:
            assert peer.pump(.02), 'Reference peer disconnected: ' + peer.name
        if self.keep:
            self.keep()

    def wait(self, predicate, name, seconds=15):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            value = predicate()
            if value:
                return value
            self.tick()
        raise TimeoutError(name)

    def pause(self, seconds):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            self.tick()

    def login(self, peer, password):
        self.pause(3)
        for data, label in [(b'\r', 'login'), (peer.name.encode() + b'\r', 'synthetic username'),
                            (password.encode() + b'\r', 'synthetic password')]:
            peer.application(data, label)
            self.pause(1)
        auth = self.wait(lambda: [row for row in self.rows() if row.get('msg') == f'User "{peer.name}" successfully logged in'], 'authentication')
        assert len(auth) == 1
        peer.session = auth[0]['sessionId']
        for _ in range(25):
            menu = self.menu(peer)
            if menu == 'mainMenu':
                return
            peer.application(b'\x1b' if menu == 'fullLoginSequenceOnelinerz' else
                             b'N' if menu == 'fullLoginSequenceNewScanConfirm' else b'\r', 'advance login')
            self.pause(1)
        raise TimeoutError('login menu sequence: ' + str(self.menu(peer)))

    def go(self, peer, data, menu):
        peer.application(data, 'menu input')
        self.wait(lambda: self.menu(peer) == menu, menu)
        self.pause(.4)

    def upload(self, peer):
        self.go(peer, b'U\r', 'fileBaseUploadFiles')
        peer.application(b'\t\t\t\r', 'upload options continue')
        self.wait(lambda: self.menu(peer) == 'fileTransferProtocolSelection', 'protocol selector')
        self.pause(.5)
        start = len(peer.history)
        peer.application(b'\r', 'select ZMODEM')
        self.wait(lambda: self.menu(peer) == 'recvFilesFromUser', 'receiver process')
        self.wait_header(peer, 1, start)
        return start

    def wait_header(self, peer, kind, minimum, position=None):
        return self.wait(lambda: next((item for item in scan(peer.history, minimum)
            if item['type'] == kind and (position is None or item['position'] == position)), None),
            f'{peer.name}: receiver header {kind}/{position}')

    def send_header(self, peer, kind, position=0):
        peer.application(header(bytes([kind]) + position.to_bytes(4, 'little'), 66, 1), 'reference ZMODEM header')

    def offer(self, peer, name, data):
        start = len(peer.history)
        self.send_header(peer, 0)
        self.wait_header(peer, 1, start)
        self.send_header(peer, 4)
        peer.application(packet(name.encode() + b'\0' + str(len(data)).encode() + b' 0\0', 66, 107, 1), 'reference ZFILE')
        self.wait_header(peer, 9, start, 0)

    def chunk(self, peer, position, data):
        start = len(peer.history)
        self.send_header(peer, 10, position)
        # Data frames use CRC16 binary format, independently of hex headers.
        peer.application(packet(data, 65, 107, 1), 'reference source bytes')
        self.wait_header(peer, 3, start, position + len(data))

    def finish(self, peer, size):
        start = len(peer.history)
        self.send_header(peer, 11, size)
        self.wait_header(peer, 1, start)
        start = len(peer.history)
        self.send_header(peer, 8)
        self.wait_header(peer, 8, start)
        peer.application(b'OO', 'reference finish')
        self.wait(lambda: self.menu(peer) == 'fileBaseUploadFiles', 'upload processing')
        return start

    def details(self, peer, name, start):
        def clean():
            return re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', peer.history[start:])
        self.wait(lambda: b'>> smash your keyboard <<' in clean() or b'UPLOAD DETAILS - ' in clean(), 'scan pause', 40)
        if b'UPLOAD DETAILS - ' not in clean():
            peer.application(b'\r', 'acknowledge scan pause')
        self.wait(lambda: b'UPLOAD DETAILS - ' in clean() and name.encode() in clean() and
                  b'ontinue' in clean().lower(), 'details form')
        self.pause(.5)
        cursor = re.findall(rb'\x1b\[(\d+);(\d+)H', peer.history[start:])[-1]
        row, column = map(int, cursor)
        assert row in (6, 9, 14), ('Unexpected details focus', row, column)
        tabs = (2 if column >= 52 else 3) if row == 6 else 1 if row == 9 else 0
        self.forms.append(dict(peer=peer.name, file=name, row=row, column=column, tabs=tabs))
        menu_start = len(peer.history)
        peer.application(b'\t' * tabs + b'\r', 'details continue')
        self.wait(lambda: self.menu(peer) == 'fileBaseMainMenu', 'upload return')
        acknowledged = 0
        def ready():
            nonlocal acknowledged
            visible = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', peer.history[menu_start:])
            pause = b'>> smash your keyboard <<'
            if visible.rfind(b'...cmd:') > visible.rfind(pause):
                return True
            count = visible.count(pause)
            if count > acknowledged:
                assert b'ACHIEVEMENT' in visible, 'Unexpected post-upload interrupt'
                peer.application(b'\r', 'acknowledge achievement pause')
                self.interrupts.append(dict(peer=peer.name, pause=count))
                acknowledged = count
            return False
        self.wait(ready, 'visible File Base prompt after interrupts', 30)
        self.pause(.4)

    def nfo(self, peer):
        self.go(peer, b'S\r', 'fileBaseSearch')
        self.go(peer, b'PCPLUS PROBE 01\r', 'blackFlagZipResults')
        self.go(peer, b'\r', 'locGameDetails')
        start = len(peer.history)
        peer.application(b'n', 'NFO input')
        self.wait(lambda: b'NFO | lines 1-15/24' in peer.history[start:] and
                  b'PCPLUS NFO LINE 01 : synthetic game 01' in peer.history[start:], 'NFO response')

    def snapshot(self, label):
        root = self.candidate / 'runtime-tmp'
        files = {}
        for path in root.rglob('*'):
            if not path.is_file():
                continue
            for _ in range(3):
                before = path.stat()
                data = path.read_bytes()
                after = path.stat()
                if (before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns):
                    assert len(data) == after.st_size
                    files[str(path.relative_to(root))] = dict(bytes=len(data), inode=after.st_ino,
                        sha256=hashlib.sha256(data).hexdigest())
                    break
            else:
                raise RuntimeError('Temporary data changed during snapshot')
        snapshot = dict(label=label, temporary_files=files,
            installed=sorted(path.name for path in (self.candidate / 'file_base/pcplus_upload').iterdir()),
            catalog=metadata(self.candidate, ['CONCA.BIN', 'CONCB.BIN']))
        self.snapshots.append(snapshot)
        return files

    def save(self):
        for peer in self.peers:
            directory = self.output / peer.name
            directory.mkdir()
            for name, data in [('server-wire.bin', peer.rx), ('client-wire.bin', peer.tx),
                               ('display.bin', peer.history)]:
                (directory / name).write_bytes(data)
            (directory / 'events.json').write_text(json.dumps(peer.events, indent=2) + '\n')
        (self.output / 'snapshots.json').write_text(json.dumps(self.snapshots, indent=2) + '\n')
        (self.output / 'server-session.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in self.rows()))


def run(args):
    candidate = owned(args.candidate)
    if args.setup:
        return setup(candidate)
    assert args.label and args.label.replace('-', '').replace('_', '').isalnum()
    fixture = json.loads((candidate / 'search-instance.json').read_text())
    assert fixture['transfer_owner_experiment'] and (candidate / 'concurrent-upload-instance.json').is_file()
    inputs = {name: candidate / name for name in [*fixture['fixture_inputs'], *fixture['source_modules']]}
    inputs.update(runner=Path(__file__), peer=Path(synchronet.__file__), auditor=ROOT / 'lab/bbs/audit_zmodem.py',
                  encoder=ROOT / 'standalone/check_zmodem_wire.py', setup=candidate / 'concurrent-upload-instance.json')
    before = {name: sha(path) for name, path in inputs.items()}
    for name, digest in {**fixture['fixture_inputs'], **fixture['source_modules']}.items():
        assert before[name] == digest
    temporary = candidate / 'runtime-tmp'
    assert temporary.is_dir() and not any(path.is_file() for path in temporary.rglob('*')), 'Fresh private temporary data required'
    expected = {'CONCA.BIN': bytes((i * 79 + 23) & 255 for i in range(1501)),
                'CONCB.BIN': bytes((i * 73 + (i >> 8) * 11) & 255 for i in range(65539))}
    assert not any(row['entries'] for row in metadata(candidate, list(expected)))
    out = ROOT / 'build/bbs-lab/results/enigma' / args.label
    out.mkdir(parents=True, exist_ok=False)
    for name, data in expected.items():
        (out / name).write_bytes(data)
    synchronet.PORT = PORT
    lab = Lab(candidate, out)
    count = messages(candidate)
    try:
        with contextlib.ExitStack() as stack:
            a, b = [stack.enter_context(Peer(name)) for name in ('loclab', PEER_NAME)]
            lab.peers = [a, b]
            lab.login(a, 'LoC-Lab-2026!')
            lab.login(b, PEER_PASSWORD)
            lab.check('two_authenticated_distinct_sessions', a.session != b.session)
            for peer in (a, b):
                lab.go(peer, b'F\r', 'fileBaseMainMenu')
            lab.upload(b)
            lab.offer(b, 'CONCB.BIN', expected['CONCB.BIN'])
            position = 0
            # The receiver can acknowledge buffered data before stdio flushes.
            # Send enough for a real on-disk prefix before checking ownership.
            while position < 8192:
                lab.chunk(b, position, expected['CONCB.BIN'][position:position+1024])
                position += 1024
            last = time.monotonic()
            pending = None

            def keep_b():
                nonlocal position, last, pending
                if pending is not None:
                    if any(item['type'] == 3 and item['position'] == position for item in scan(b.history, pending)):
                        pending = None
                    return
                if time.monotonic() - last >= 2 and position + 1024 < len(expected['CONCB.BIN']):
                    pending = len(b.history)
                    lab.send_header(b, 10, position)
                    b.application(packet(expected['CONCB.BIN'][position:position+1024], 65, 107, 1), 'active peer source bytes')
                    position += 1024
                    last = time.monotonic()

            lab.keep = keep_b
            first = lab.snapshot('B active before A')
            b_path = next(path for path in first if path.endswith('/CONCB.BIN'))
            lab.check('peer_B_partial_is_real_and_owned', len(first) == 1 and first[b_path]['bytes'] > 0)
            def preserved(files):
                if set(files) != {b_path}:
                    return False
                entry = files[b_path]
                return (entry['inode'] == first[b_path]['inode'] and entry['bytes'] >= first[b_path]['bytes'] and
                    entry['sha256'] == hashlib.sha256(expected['CONCB.BIN'][:entry['bytes']]).hexdigest())
            lab.check('peer_B_partial_matches_source', preserved(first))
            lab.upload(a)
            lab.offer(a, 'CONCA.BIN', expected['CONCA.BIN'])
            lab.chunk(a, 0, expected['CONCA.BIN'][:1024])
            a.application(b'\x18' * 8 + b'\x08' * 10, 'cancel A')
            lab.wait(lambda: lab.menu(a) == 'fileTransferProtocolSelection', 'A canceled')
            lab.go(a, b'\x1b', 'fileBaseMainMenu')
            lab.nfo(a)
            after_cancel = lab.snapshot('A canceled; B active')
            lab.check('A_cancel_retires_only_A', preserved(after_cancel) and lab.menu(b) == 'recvFilesFromUser')
            lab.check('canceled_A_not_installed', not lab.snapshots[-1]['installed'] and
                all(not row['entries'] for row in lab.snapshots[-1]['catalog']))
            for menu in ('blackFlagZipResults', 'fileBaseSearch', 'fileBaseMainMenu'):
                lab.go(a, b'\x1b', menu)
            lab.upload(a)
            lab.offer(a, 'CONCA.BIN', expected['CONCA.BIN'])
            lab.chunk(a, 0, expected['CONCA.BIN'])
            processing = lab.finish(a, len(expected['CONCA.BIN']))
            lab.details(a, 'CONCA.BIN', processing)
            lab.nfo(a)
            after_success = lab.snapshot('A installed; B active')
            lab.check('A_success_preserves_active_B', preserved(after_success) and lab.menu(b) == 'recvFilesFromUser')
            lab.keep = None
            if pending is not None:
                lab.wait_header(b, 3, pending, position)
            while position < len(expected['CONCB.BIN']):
                part = expected['CONCB.BIN'][position:position+1024]
                lab.chunk(b, position, part)
                position += len(part)
            processing = lab.finish(b, position)
            lab.details(b, 'CONCB.BIN', processing)
            lab.nfo(b)
            lab.check('both_NFO_routes_remain_interactive', lab.menu(a) == lab.menu(b) == 'locGameDetails')
            lab.check('achievement_interrupts_dismissed', len([event for event in lab.interrupts if event['peer'] == PEER_NAME]) >= 2)
            lab.check('all_temporary_data_removed', not lab.snapshot('both installed'))
            rows = metadata(candidate, list(expected))
            (out / 'server-upload-metadata.json').write_text(json.dumps(rows, indent=2) + '\n')
            for row in rows:
                name = row['name']
                lab.check('exact_installed_' + name, len(row['entries']) == 1 and
                    Path(row['entries'][0]['filePath']).read_bytes() == expected[name] and
                    row['entries'][0]['fileSha256'] == hashlib.sha256(expected[name]).hexdigest())
                entry = row['entries'][0]
                lab.check('catalog_owner_' + name, entry['areaTag'] == entry['storageTag'] == 'pcplus_upload' and
                    entry['meta'].get('byte_size') == len(expected[name]) and
                    entry['meta'].get('upload_by_username') == ('loclab' if name == 'CONCA.BIN' else PEER_NAME))
            for peer, name in ((a, 'CONCA.BIN'), (b, 'CONCB.BIN')):
                # Decode Telnet application output independently of wire quoting.
                sent = bytes(peer.tx).replace(b'\xff\xff', b'\xff')
                transfer = audit_batch(sent, {name: expected[name]}, sent.index(b'\x18' * 8) + 8 if peer is a else 0)
                for file in transfer['files']:
                    file.pop('source')
                (out / (peer.name + '-protocol.json')).write_text(json.dumps(transfer, indent=2) + '\n')
                exits = [row['exitCode'] for row in lab.rows(peer) if row.get('msg') == 'Process exited']
                lab.check(peer.name + '_protocol_process_outcomes', exits == ([1, 0] if peer is a else [0]))
            lab.check('inputs_unchanged', before == {name: sha(path) for name, path in inputs.items()})
            lab.check('source_files_unchanged', all((out / name).read_bytes() == data for name, data in expected.items()))
            lab.check('no_post_saved', messages(candidate) == count)
            report = dict(passed=True, checks=lab.checks, input_hashes=before, forms=lab.forms, interrupts=lab.interrupts, expected={name: dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for name, data in expected.items()},
                scope='Two actual loopback ENiGMA sessions with declared reference Telnet/ZMODEM senders. A cancel/NFO/retry/details/NFO while B continues source-backed acknowledged data, then B completion/details/NFO. No DOS, physical modem or live-board assertion.')
            (out / 'concurrent-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    except Exception as error:
        (out / 'concurrent-checks.json').write_text(json.dumps(dict(passed=False, checks=lab.checks,
            error=type(error).__name__ + ': ' + str(error), input_hashes=before), indent=2) + '\n')
        raise
    finally:
        lab.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--setup', action='store_true')
    parser.add_argument('--label')
    run(parser.parse_args())
