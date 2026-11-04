#!/usr/bin/env python3
"""Frozen release X/Y/ZMODEM round trips using independent peers and real DOS.

Uses explicit COM3/IRQ5,19200,8N1,HARD PRM and original-reference transfer keys.
Fixtures, sources and outputs stay on fresh owned media. No product callbacks,
registers or replies are replaced. Physical/SIP/modem carrier is not modeled here.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import socket
import struct
import subprocess
import time
from pathlib import Path
from modem_fixtures import fixture
from test_terminal import SAMPLER
from test_terminal_transfer_dos import Peer as ReceivePeer
from test_terminal_upload_dos import UploadPeer
from test_terminal_ymodem_dos import BatchPeer, file
from test_terminal_zmodem_dos import ZPeer

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def recipes():
    binary = bytes(range(256)) * 4 + b'\x00\x1a\xff\x11\x13'
    batch = [file('EMPTY.BIN', b''), file('ODD.BIN', b'A'), file('ALL.BIN', binary)]
    rows = [
        dict(name='x-rx-binary', protocol=0, direction='rx', blocks=[bytes(range(128)), bytes(range(256)) * 4, bytes(range(128, 256))]),
        dict(name='x-rx-badCRC-retry', protocol=0, direction='rx', blocks=[bytes(range(128))], bad_crc=True),
        dict(name='x-rx-local-Escape', protocol=0, direction='rx', blocks=[bytes(range(128))], cancel='escape'),
        dict(name='x-tx-binary', protocol=0, direction='tx', data=binary),
        dict(name='x-tx-NAK-retry', protocol=0, direction='tx', data=binary, nak=True),
        dict(name='x-tx-peer-CAN', protocol=0, direction='tx', data=binary, cancel='peer'),
        dict(name='y-rx-binary', protocol=1, direction='rx', files=batch),
        dict(name='y-tx-binary', protocol=1, direction='tx', files=batch),
        dict(name='y-rx-local-Escape', protocol=1, direction='rx', files=batch[2:], cancel='escape'),
        dict(name='y-rx-cancel-retry', protocol=1, direction='rx', files=batch, cancel='escape', retry_after_cancel=True),
        dict(name='y-rx-retained-first', protocol=1, direction='rx', files=batch[2:], partial_bad_header=True),
        dict(name='y-tx-NAK-retry', protocol=1, direction='tx', files=batch[2:], data_nak=True),
    ]
    for direction, flags, name in [('rx', [], 'default'), ('rx', ['-o'], 'crc16'), ('tx', [], 'default'), ('tx', ['-e'], 'escape')]:
        rows.append(dict(name='z-' + direction + '-' + name, protocol=2, direction=direction,
                         files=[(f['name'], f['data']) for f in batch], flags=flags,
                         transfer_timeout=65, resume_timeout=30, automatic=False, sender_helper=None, zedzap=False))
    return rows


class RetryBatchPeer(BatchPeer):
    """Independent remote peer accepts a second transfer on the same wire."""
    def __init__(self, recipe, destination):
        super().__init__(dict(recipe), destination)
        self.round = 0

    def resume(self):
        super().resume()
        if not self.round:
            assert self.checks.get('actual_CAN_pair') and not list(self.destination_dir.iterdir())
            self.checks['cancelled_and_resumed_before_retry'] = True
            self.round = 1
            self.pending.clear()  # Already observed application query/keyboard.
            self.checks.pop('posttransfer_DSR', None)
            self.checks.pop('posttransfer_keyboard', None)
            self.recipe.pop('cancel')
            self.log('waiting-for-real-second-transfer')
            self.rx()
        else:
            self.checks['retry_completed_same_connection'] = bool(self.checks.get('batch_end_ACK') and self.checks.get('exact_files_before_EOT_ACK'))


def run_case(r, binary, manifest, root):
    out = root / r['name']
    out.mkdir()
    for directory in ('RECV', 'SEND', 'PEER'):
        (out / directory).mkdir()
    raw = bytearray(fixture(timeout=5))
    struct.pack_into('<HH', raw, 0, 2, 5)
    struct.pack_into('<H', raw, 0x178, 0x3e8)
    struct.pack_into('<H', raw, 0x188, 5)
    struct.pack_into('<HH', raw, 0x4e4, 8, 4)
    struct.pack_into('<HH', raw, 0x1bc, 0, 0)
    struct.pack_into('<H', raw, 0x1e6, 0)
    (out / 'TEST.PRM').write_bytes(raw)
    sampler = SAMPLER
    for offset in (0, 1, 3, 4):
        sampler = sampler.replace(hex(0x3f8 + offset), hex(0x3e8 + offset))
    (out / 'sampler.asm').write_text(sampler)
    subprocess.run(['nasm', '-fbin', str(out / 'sampler.asm'), '-o', str(out / 'SNAP.COM')], check=True)
    incoming = r['direction'] == 'rx'
    if r['protocol'] == 0:
        source_files = {} if incoming else {'ONE.BIN': r['data']}
        expected_files = {'ONE.BIN': b''.join(r['blocks'])} if incoming else {}
        peer = ReceivePeer(r, destination=out / 'RECV/ONE.BIN') if incoming else UploadPeer(r)
        filename = 'D:\\RECV\\ONE.BIN' if incoming else 'D:\\SEND\\ONE.BIN'
    elif r['protocol'] == 1:
        source_files = {} if incoming else {f['name']: f['data'] for f in r['files']}
        expected_files = {f['name']: f['data'] for f in r['files']} if incoming else {}
        peer = (RetryBatchPeer if r.get('retry_after_cancel') else BatchPeer)(r, out / 'RECV')
        filename = 'D:\\RECV\\' if incoming else 'D:\\SEND\\*.BIN'
    else:
        source_files = dict(r['files'])
        expected_files = dict(r['files'])
        peer = ZPeer(r, out)
        filename = 'D:\\RECV\\' if incoming else 'D:\\SEND\\*.BIN'
    source = out / ('PEER' if r['protocol'] == 2 and incoming else 'SEND')
    for name, data in source_files.items():
        (source / name).write_bytes(data)
    source_before = {p.name: (p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns, sha(p)) for p in source.iterdir()}
    peer.resume_timeout = 30
    peer.thread.start()
    action = ['a-z', 'p150', 'pgdown' if incoming else 'pgup']
    if not manifest.get('experimental_original_reference'):
        action = ['a-r' if incoming else 'a-s']
    keys = (['p900', 'enter'] if manifest.get('special_edition') else []) + ['p1500'] + action + ['p300']
    for index in range(r['protocol']):
        keys += ['f2', 'p150']
    keys += list(filename) + ['enter']
    if r.get('cancel') == 'escape':
        keys += ['p1800', 'escape']
    if r.get('retry_after_cancel'):
        # The selected YMODEM protocol persists across the cancelled attempt.
        # First prove ordinary keyboard/query return, then use the real menu
        # again to start a fresh transfer in this same DOS process/connection.
        keys += ['p2000', 'r', 'e', 'a', 'd', 'y', 'p1000'] + action + ['p300'] + list(filename) + ['enter']
    # The receive peer's post-transfer query window is ten seconds. Small
    # XMODEM fixtures must type within it; batch/independent peers allow longer.
    keys += ['p6000' if r['protocol'] == 0 else 'p18000', 'r', 'e', 'a', 'd', 'y', 'p1800', 'a-x']
    serial = '\n'.join('serial' + str(i) + '=' + (f'nullmodem server:127.0.0.1 port:{peer.port} transparent:1 irq:5 rxdelay:200 txdelay:1' if i == 3 else 'disabled') for i in range(1, 5))
    config = f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
{serial}
[autoexec]
@echo off
mount c "{binary.parent}"
mount d "{out}"
d:
set PCPLUS=
D:\\SNAP B
ADDKEY {' '.join(keys)}
C:\\TERMINAL @D:\\TEST.PRM
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto capture
:failed
echo FAIL>D:\\FAIL.TXT
:capture
D:\\SNAP S
D:\\SNAP A
exit
'''
    (out / 'dosbox.conf').write_text(config)
    started = time.monotonic()
    try:
        with (out / 'dosbox.log').open('w') as log:
            try:
                code = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
                                      cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                                      stdout=log, stderr=log, timeout=80).returncode
            except subprocess.TimeoutExpired:
                code = -1
    finally:
        peer.stop.set()
        if peer.conn:
            try:
                peer.conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        peer.server.close()
        peer.thread.join(7)
        assert not peer.thread.is_alive(), 'Owned independent peer did not stop'
    read = lambda n: (out / n).read_bytes() if (out / n).exists() else b''
    checks = dict(peer.checks)
    checks.update(actual_ready=bool(checks.get('actual_terminal_ready')), normal_DOS_exit=code == 0 and bool(read('PASS.TXT')) and not read('FAIL.TXT'),
                  hardware_restored=len(read('BEFORE.BIN')) == 42 and read('BEFORE.BIN') == read('AFTER.BIN'),
                  no_peer_errors=not peer.errors, posttransfer_DSR=bool(checks.get('posttransfer_DSR')),
                  posttransfer_keyboard=bool(checks.get('posttransfer_keyboard')),
                  final_screen=read('SCREEN.BIN')[:28:2] == b'AFTER TRANSFER', PRM_unchanged=read('TEST.PRM') == raw,
                  source_unchanged=source_before == {p.name: (p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns, sha(p)) for p in source.iterdir()},
                  binary_unchanged=sha(binary) == manifest['binary_sha256'],
                  no_partial_stages=not any(p.name.upper().startswith(('PCRX.', 'PCZRX.', 'PCYM.')) for p in out.rglob('*')))
    if r.get('cancel') and not r.get('retry_after_cancel'):
        expected_files = {}
        if r['protocol'] == 0:
            checks['cancellation_seen'] = b'\x18\x18' in peer.wire if incoming else bool(checks.get('actual_cancel_CAN_pair'))
        else:
            checks['cancellation_seen'] = bool(checks.get('actual_CAN_pair'))
    elif r['protocol'] == 0:
        checks['complete_protocol'] = bool(checks.get('complete_EOT_handshake') if incoming else checks.get('EOT_NAK_then_ACK'))
        if not incoming:
            checks['exact_binary_and_padding'] = bool(checks.get('exact_source_and_padding'))
    elif r['protocol'] == 1 and not r.get('partial_bad_header'):
        checks['complete_protocol'] = bool(checks.get('batch_end_ACK'))
        checks['exact_protocol_files'] = bool(checks.get('exact_files_before_EOT_ACK') if incoming else checks.get('exact_all_source_files'))
        if r.get('retry_after_cancel'):
            checks['required_cancel_resume_retry'] = bool(checks.get('cancelled_and_resumed_before_retry') and checks.get('retry_completed_same_connection'))
    elif r['protocol'] == 2:
        checks['independent_lrzsz_success'] = peer.peer_exit == 0
    if incoming or r['protocol'] == 2:
        destination = out / ('RECV' if incoming else 'PEER')
        checks['exact_destination'] = {p.name: p.read_bytes() for p in destination.iterdir()} == expected_files
    result = dict(passed=all(checks.values()), case=r['name'], checks=checks, errors=peer.errors,
                  terminal_sha256=sha(binary), seconds=round(time.monotonic() - started, 3),
                  serial=dict(com=3, irq=5, baud=19200, framing='8N1', flow='HARD'), cpu='8086',
                  files={name: hashlib.sha256(data).hexdigest() for name, data in expected_files.items()},
                  peer_command=getattr(peer, 'command', None), scope=__doc__)
    (out / 'serial.bin').write_bytes(peer.wire)
    (out / 'peer.bin').write_bytes(peer.sent)
    (out / 'events.json').write_text(json.dumps(peer.events, indent=2) + '\n')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(r['name'], 'PASS' if result['passed'] else json.dumps({k: v for k, v in checks.items() if not v}) + ' ' + repr(peer.errors), flush=True)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal', type=Path, required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--case', action='append')
    p.add_argument('--jobs', type=int, choices=(1, 2, 3, 4), default=2)
    a = p.parse_args()
    assert re.fullmatch('[a-z0-9-]+', a.label)
    binary = a.terminal.resolve()
    assert binary.is_relative_to(ROOT / 'build') and binary.name == 'TERMINAL.EXE'
    manifest = json.loads((binary.parent / 'manifest.json').read_text())
    assert manifest['binary_sha256'] == sha(binary) and manifest['experimental_original_reference'] and manifest['experimental_custom_irq']
    sources = dict(manifest['sources'])
    for name in ('test_release_transfers_dos.py', 'test_terminal.py', 'modem_fixtures.py', 'terminal_config_fixtures.py',
                 'test_terminal_transfer_dos.py', 'test_terminal_upload_dos.py', 'test_terminal_ymodem_dos.py', 'test_terminal_zmodem_dos.py'):
        sources['standalone/' + name] = sha(ROOT / 'standalone' / name)
    assert all(sha(ROOT / n) == h for n, h in sources.items())
    root = ROOT / 'build/release-transfers-dos' / a.label
    root.mkdir(parents=True, exist_ok=False)
    selected = [r for r in recipes() if not a.case or r['name'] in a.case]
    assert selected and (not a.case or set(a.case) == {r['name'] for r in selected})
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:
        rows = list(pool.map(lambda r: run_case(r, binary, manifest, root), selected))
    report = dict(passed=all(r['passed'] for r in rows), terminal_sha256=sha(binary), cases=rows,
                  sources=sources, sources_unchanged=all(sha(ROOT / n) == h for n, h in sources.items()), original_inputs=[], scope=__doc__)
    report['passed'] &= report['sources_unchanged']
    (root / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    assert report['passed']


if __name__ == '__main__':
    main()
