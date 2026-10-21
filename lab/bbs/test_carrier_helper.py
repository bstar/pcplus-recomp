#!/usr/bin/env python3
"""Run the real i386 helper with a PTY and independent carrier/control sockets."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pty
import select
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import time
import tty

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'lab/bbs/patches/synthmodem-carrier'
HELLO, DOWN = b'\x01\x10', b'\x01\x11'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def frame(kind, body=b''):
    return struct.pack('<HB', len(body) + 1, kind) + body


class Lab:
    def __init__(self, executable, out, *, delayed_pty=False, occupied=False):
        self.temp = tempfile.TemporaryDirectory(prefix='pc-carrier-helper-')
        self.root = Path(self.temp.name)
        self.master, self.slave = pty.openpty()
        tty.setraw(self.slave)
        os.set_blocking(self.master, False)
        self.path = self.root / 'carrier.sock'
        if occupied: self.path.write_text('keep existing path')
        self.pty_path = self.root / 'modem.pty'
        if not delayed_pty: self.pty_path.symlink_to(os.ttyname(self.slave))
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(str(self.root / 'control.sock')); self.server.listen(1)
        self.server.settimeout(4)
        self.log = out.open('w')
        self.process = subprocess.Popen([str(executable)], stdout=self.log, stderr=self.log,
            env={**os.environ, 'SYNTHMODEM_CONTROL_PATH': str(self.root / 'control.sock'),
                 'SYNTHMODEM_PTY_PATH': str(self.pty_path), 'SYNTHMODEM_CARRIER_PATH': str(self.path)})
        self.control, _ = self.server.accept()
        self.control.settimeout(3)
        self.peer = None
        self.buffer = bytearray(); self.frames = []; self.data = bytearray(); self.eof = False
        self.reset = False

    def peer_connect(self, record=HELLO):
        self.peer = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.peer.settimeout(3)
        deadline = time.monotonic() + 3
        while True:
            try: self.peer.connect(str(self.path)); break
            except FileNotFoundError:
                assert time.monotonic() < deadline
                time.sleep(.01)
        if record is not None: self.peer.sendall(record)

    def observe(self, seconds=.1, until=None):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline and not self.eof:
            if until and until(): return
            if not select.select([self.control], [], [], max(0, deadline-time.monotonic()))[0]: break
            try: value = self.control.recv(65536)
            except ConnectionResetError:
                # A retired Unix peer can reset when closing unread stale
                # host input. The test still requires the complete status
                # frame before termination and zero partial output frames.
                self.reset = self.eof = True
                break
            if not value: self.eof = True; break
            self.buffer.extend(value)
            while len(self.buffer) >= 3:
                size, kind = struct.unpack_from('<HB', self.buffer)
                assert 1 <= size <= 4094
                if len(self.buffer) < size + 2: break
                body = bytes(self.buffer[3:size+2]); del self.buffer[:size+2]
                self.frames.append((kind, body))
                if kind == 0x15: self.data.extend(body)
        if until: assert until(), 'wire observation deadline'

    def online(self, tail=b''):
        self.observe(2, until=lambda: any(k == 0x10 for k, _ in self.frames))
        os.write(self.master, b'\r\nCONNECT 1200\r\n' + tail)
        self.observe(2, until=lambda: any(k == 0x13 and b'"connect"' in b for k, b in self.frames))
        statuses = [(i, b) for i, (k, b) in enumerate(self.frames) if k == 0x13]
        at_lines = [(i, b) for i, (k, b) in enumerate(self.frames) if k == 0x12 and b'CONNECT' in b]
        assert len(statuses) == len(at_lines) == 1 and at_lines[0][0] < statuses[0][0]

    def close(self):
        if self.process.poll() is None: self.process.kill(); self.process.wait()
        if self.peer: self.peer.close()
        self.control.close(); self.server.close(); self.log.close()
        os.close(self.master); os.close(self.slave); self.temp.cleanup()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--helper', type=Path, required=True)
    parser.add_argument('--client-probe', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    a = parser.parse_args()
    out = a.output.resolve(); assert out.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    helper = a.helper.resolve(); probe = a.client_probe.resolve()
    baseline = a.baseline.resolve()
    check_source = ROOT / 'lab/bbs/patches/synthmodem-control/check.py'
    spec = importlib.util.spec_from_file_location('previous_control', check_source)
    previous = importlib.util.module_from_spec(spec); spec.loader.exec_module(previous)
    assert sha(baseline / 'vm/ctrl/modemd-ctrl.c') == '779c516d2352e12e3dd6324b080757139e0f279f1cfeec442e470632aa106c60'
    source = out / 'candidate'; shutil.copytree(baseline, source)
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(HERE/'control.patch')], cwd=source, check=True)
    target = source / 'vm/ctrl'
    for name in ('carrier_protocol.h', 'carrier_server.h', 'carrier_server.inc'):
        shutil.copyfile(HERE/name, target/name)
    faults = out / 'faults'
    command = ['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-O2', '-DFIXED',
               '-I'+str(target), str(ROOT/'lab/bbs/patches/synthmodem-control/faults.c'), '-o', str(faults)]
    subprocess.run(command, check=True)
    result = subprocess.run([str(faults)], capture_output=True, text=True, check=True)
    (out/'faults.log').write_text(result.stdout + result.stderr)
    reports = {'legacy_faults': json.loads(result.stdout),
               'legacy_actual_PTY': previous.actual_pty(helper, out/'legacy-pty')}
    checks = {}; lab = None; client = None; writer = None; stop = threading.Event()
    try:
        lab = Lab(helper, out/'paired.log', delayed_pty=True)
        # The source modem client starts before a PTY path exists. Its HELLO
        # must complete without the helper waiting on PTY startup first.
        client = subprocess.Popen([str(probe), str(lab.master), '1'],
            env={**os.environ, 'SYNTHMODEM_CARRIER_PATH': str(lab.path)},
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            pass_fds=(lab.master,))
        assert select.select([client.stdout], [], [], 3)[0]
        assert client.stdout.readline() == b'READY\n'
        checks['paired_HELLO_before_PTY_exists'] = not lab.pty_path.exists()
        lab.pty_path.symlink_to(os.ttyname(lab.slave))
        tail = b'first banner\r\nNO CARRIER\r\n\x00\xff'
        lab.online(tail); checks['CONNECT_line_precedes_status'] = True
        lab.observe(.4, until=lambda: len(lab.data) >= len(tail))
        expected = bytearray(tail)
        checks['CONNECT_and_carrier_like_payload_in_same_read'] = lab.data == expected
        for token in (b'\x00\xff\x1b[0m' + bytes(range(256)), b'\r\nNO CARRIER\r\n',
                      b'NO CAR', b'RIER\r\n', b'N'):
            os.write(lab.master, token); expected.extend(token)
            lab.observe(.4, until=lambda: len(lab.data) >= len(expected))
            assert lab.data == expected
            if token == b'NO CAR': time.sleep(.1)
        checks['literal_fragmented_and_sparse_payload_exact'] = lab.data == expected
        checks['no_inband_carrier_status'] = not any(k == 0x13 and b'nocarrier' in b for k,b in lab.frames)
        errors = []
        def flood():
            try:
                for _ in range(1024):
                    if stop.is_set(): break
                    lab.control.sendall(frame(0x14, b'X'*4093))
            except (OSError, TimeoutError) as error: errors.append(type(error).__name__)
        writer = threading.Thread(target=flood, daemon=True); writer.start(); time.sleep(.2)
        checks['PTY_transmission_stalled_before_DOWN'] = writer.is_alive() and bool(select.select([lab.master], [], [], 0)[0])
        started = time.monotonic(); client.stdin.write(b'x'); client.stdin.flush()
        assert select.select([client.stdout], [], [], 3)[0]
        assert client.stdout.readline() == b'DOWN\n' and client.wait(timeout=2) == 0
        checks['paired_DOWN_clears_kernel_PTY_input'] = not select.select([lab.master], [], [], 0)[0]
        lab.observe(2); assert lab.process.wait(timeout=2) == 0
        checks['DOWN_status_once_and_clean_helper_exit'] = sum(k == 0x13 and b'nocarrier' in b for k,b in lab.frames) == 1 and lab.eof and not lab.buffer
        checks['DOWN_bounded_while_transmission_stalled'] = time.monotonic() - started < 2
        checks['retired_session_does_not_forward_result_text'] = lab.data == expected
        stop.set(); writer.join(4); assert not writer.is_alive()
        checks['owned_socket_path_removed'] = not lab.path.exists()
        reports['paired_control_reset_on_unread_stale_input'] = lab.reset
    finally:
        stop.set()
        if lab: lab.close()
        if writer: writer.join(4)
        if client:
            if client.poll() is None: client.kill(); client.wait()
            client.stdin.close(); client.stdout.close(); client.stderr.close()

    for stage, record in [('hello_short', b'\x01'), ('hello_version', b'\x02\x10'),
                          ('hello_oversize', HELLO+b'x'), ('hello_DOWN', DOWN),
                          ('online_short', b'\x01'), ('online_version', b'\x02\x11'),
                          ('online_oversize', DOWN+b'x'), ('online_duplicate_HELLO', HELLO),
                          ('online_closed', None), ('command_DOWN', DOWN)]:
        lab = Lab(helper, out/(stage+'.log'))
        try:
            if stage.startswith('hello'):
                lab.peer_connect(record)
            else:
                lab.peer_connect(); assert lab.peer.recv(3) == b'\x01\x90'
                if stage != 'command_DOWN': lab.online()
                else: lab.observe(2, until=lambda: any(k == 0x10 for k,_ in lab.frames))
                if record is None: lab.peer.close(); lab.peer = None
                else: lab.peer.sendall(record)
            if stage == 'command_DOWN':
                assert lab.peer.recv(3) == b'\x01\x91'
                lab.observe(2)
                assert lab.process.wait(timeout=2) == 0
                assert sum(k == 0x13 and b'nocarrier' in b for k,b in lab.frames) == 1
            else:
                assert lab.process.wait(timeout=3) == 1
            assert not lab.path.exists()
            checks[stage] = True
        finally: lab.close()

    for mode in ('occupied_path', 'missing_peer_timeout', 'HELLO_timeout', 'signal_during_accept', 'replaced_path'):
        lab = Lab(helper, out/(mode+'.log'), occupied=mode == 'occupied_path')
        try:
            if mode == 'occupied_path':
                assert lab.process.wait(timeout=2) == 1
                assert lab.path.read_text() == 'keep existing path'
            elif mode == 'missing_peer_timeout':
                assert lab.process.wait(timeout=7) == 1 and not lab.path.exists()
            elif mode == 'HELLO_timeout':
                lab.peer_connect(None)
                assert lab.process.wait(timeout=3) == 1 and not lab.path.exists()
            elif mode == 'signal_during_accept':
                deadline = time.monotonic() + 2
                while not lab.path.exists():
                    assert time.monotonic() < deadline; time.sleep(.01)
                lab.process.terminate()
                assert lab.process.wait(timeout=1) == 1 and not lab.path.exists()
            else:
                lab.peer_connect(); assert lab.peer.recv(3) == b'\x01\x90'
                lab.online()
                lab.path.unlink(); lab.path.write_text('replacement owned elsewhere')
                lab.peer.sendall(DOWN); assert lab.peer.recv(3) == b'\x01\x91'
                lab.observe(2); assert lab.process.wait(timeout=2) == 0
                assert lab.path.read_text() == 'replacement owned elsewhere'
            checks[mode] = True
        finally: lab.close()

    lab = Lab(helper, out/'blocked-output.log'); stop = threading.Event(); writer = None
    try:
        lab.peer_connect(); assert lab.peer.recv(3) == b'\x01\x90'; lab.online()
        written = [0]
        def fill_reverse():
            payload = bytes(range(256))*16384
            at = 0
            while not stop.is_set() and at < len(payload):
                try:
                    count = os.write(lab.master, payload[at:at+4096]); at += count; written[0] = at
                except BlockingIOError: select.select([], [lab.master], [], .02)
        writer = threading.Thread(target=fill_reverse, daemon=True); writer.start(); time.sleep(.4)
        before = written[0]; time.sleep(.15)
        assert writer.is_alive() and before > 4096 and written[0] == before, ('host output did not stall', before, written[0])
        started = time.monotonic(); lab.peer.sendall(DOWN)
        assert lab.peer.recv(3) == b'\x01\x91'
        assert lab.process.wait(timeout=2) == 1
        checks['blocked_host_status_drain_fails_within_budget'] = .8 <= time.monotonic()-started < 2
        lab.log.flush()
        checks['blocked_host_failure_is_explicit'] = 'Carrier status output drain timed out' in (out/'blocked-output.log').read_text()
        checks['blocked_host_cleans_owned_path'] = not lab.path.exists()
    finally:
        stop.set()
        if writer: writer.join(2); assert not writer.is_alive()
        lab.close()

    inputs = [HERE/n for n in ('control.patch','carrier_server.h','carrier_server.inc','carrier_protocol.h')]
    inputs += [Path(__file__), check_source, ROOT/'lab/bbs/patches/synthmodem-control/faults.c',
               ROOT/'nix/control-carrier.nix', ROOT/'tools/build-control-carrier',
               ROOT/'nix/flake.nix', ROOT/'nix/flake.lock', ROOT/'tools/bbs-dev']
    receipt = {'passed': all(checks.values()), 'checks': checks, 'reports': reports,
               'helper': str(helper), 'helper_sha256': sha(helper), 'client_probe_sha256': sha(probe),
               'candidate_source_sha256': sha(target/'modemd-ctrl.c'),
               'frozen_inputs': {str(p.relative_to(ROOT)):sha(p) for p in inputs},
               'scope': 'Actual static i386 helper, production modem carrier client, Linux PTY and Unix sockets. No real modem_stop callback, VM/SIP/DSP integration or physical hardware.'}
    assert receipt['passed'], checks
    (out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__': main()
