#!/usr/bin/env python3
"""Exercise the actual carrier client with local seqpacket peers and a real PTY."""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import pty
import select
import socket
import subprocess
import tempfile
import time
import tty

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'lab/bbs/patches/synthmodem-carrier'
HELLO, DOWN = b'\x01\x10', b'\x01\x11'


def line(process):
    assert select.select([process.stdout], [], [], 7)[0], 'child output timeout'
    return process.stdout.readline().decode().strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--modem-executable', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    executable = out / 'client-probe'
    command = ['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-O2',
               str(SOURCE / 'carrier_client.c'), str(SOURCE / 'client_probe.c'),
               '-o', str(executable)]
    subprocess.run(command, check=True)
    checks = {}

    def run(name, *, hello_ack=b'\x01\x90', down_ack=b'\x01\x91',
            enabled=True, path_kind='normal', delay=False):
        with tempfile.TemporaryDirectory(prefix='pc-carrier-') as temp:
            path = str(Path(temp) / 'status.sock')
            master, slave = pty.openpty()
            tty.setraw(slave)
            os.set_blocking(master, False)
            listener = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            listener.settimeout(7)
            peer = None
            process = None
            try:
                env = dict(os.environ)
                env.pop('SYNTHMODEM_CARRIER_PATH', None)
                if enabled:
                    env['SYNTHMODEM_CARRIER_PATH'] = path if path_kind != 'long' else '/' + 'x' * 120
                if enabled and path_kind == 'normal' and not delay:
                    listener.bind(path); listener.listen(1)
                started = time.monotonic()
                process = subprocess.Popen([str(executable), str(master), str(int(enabled))],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, pass_fds=(master,), env=env)
                if enabled and path_kind != 'normal':
                    expected = errno.ENAMETOOLONG if path_kind == 'long' else errno.ETIMEDOUT
                    assert line(process) == f'START_ERROR {expected}'
                    assert process.wait(timeout=2) == 20
                    elapsed = time.monotonic() - started
                    if path_kind == 'missing': assert 4.5 <= elapsed < 7
                    checks[name] = {'passed': True, 'elapsed_seconds': elapsed}
                    return
                if enabled:
                    if delay:
                        time.sleep(0.1)
                        assert process.poll() is None
                        listener.bind(path); listener.listen(1)
                    peer, _ = listener.accept(); peer.settimeout(3)
                    assert peer.recv(3) == HELLO
                    if hello_ack is None:
                        peer.close(); peer = None
                    elif hello_ack != 'timeout': peer.sendall(hello_ack)
                    if hello_ack != b'\x01\x90':
                        expected = errno.EPIPE if hello_ack is None else errno.ETIMEDOUT if hello_ack == 'timeout' else errno.EPROTO
                        assert line(process) == f'START_ERROR {expected}'
                        assert process.wait(timeout=2) == 20
                        checks[name] = {'passed': True}
                        return
                assert line(process) == 'READY'
                # Queue real bytes from the helper side into the modem's PTY
                # input. They must remain pending while DOWN lacks an ACK.
                payload = b'stale-data\x00\xffNO CARRIER\r\n'
                assert os.write(slave, payload) == len(payload)
                assert select.select([master], [], [], 1)[0]
                process.stdin.write(b'x'); process.stdin.flush()
                if enabled:
                    assert peer.recv(3) == DOWN
                    assert select.select([master], [], [], 0)[0], 'input flushed before ACK'
                    if down_ack is None:
                        peer.close(); peer = None
                    elif down_ack != 'timeout': peer.sendall(down_ack)
                if enabled and down_ack != b'\x01\x91':
                    expected = errno.EPIPE if down_ack is None else errno.ETIMEDOUT if down_ack == 'timeout' else errno.EPROTO
                    assert line(process) == f'DOWN_ERROR {expected}'
                    assert process.wait(timeout=2) == 25
                    assert os.read(master, 4096) == payload, 'failure hid queued input'
                else:
                    assert line(process) == 'DOWN'
                    assert process.wait(timeout=2) == 0
                    if enabled:
                        assert not select.select([master], [], [], 0)[0], 'stale input survives ACK'
                    else:
                        assert os.read(master, 4096) == payload, 'legacy path changed PTY'
                checks[name] = {'passed': True}
            finally:
                if process:
                    if process.poll() is None: process.kill(); process.wait()
                    for stream in (process.stdin, process.stdout, process.stderr): stream.close()
                if peer: peer.close()
                listener.close()
                os.close(master); os.close(slave)

    run('acknowledged_DOWN_flushes_real_PTY_input_and_socket_is_cloexec')
    run('legacy_optout_preserves_PTY_input', enabled=False)
    run('delayed_listener_startup', delay=True)
    run('missing_listener_timeout', path_kind='missing')
    run('overlong_path_rejected', path_kind='long')
    for stage in ('hello', 'down'):
        for name, reply in [('wrong_version', b'\x02\x90'), ('wrong_type', b'\x01\x92'),
                            ('short_packet', b'\x01'), ('oversize_packet', b'\x01\x90\x00'),
                            ('peer_closed', None), ('no_ack_timeout', 'timeout')]:
            run(f'{stage}_{name}', **{f'{stage}_ack': reply})
    if args.modem_executable:
        # Execute the actual rebuilt daemon, not only the client probe. These
        # failures must return before device setup creates any modem children.
        with tempfile.TemporaryDirectory(prefix='pc-carrier-daemon-') as temp:
            path = str(Path(temp) / 'status.sock')
            daemon_command = [str(args.modem_executable), '-e', '/bin/false']
            for name, value in [('long_path', '/' + 'x' * 120), ('missing_helper', path)]:
                result = subprocess.run(daemon_command,
                                        env={**os.environ, 'SYNTHMODEM_CARRIER_PATH': value},
                                        capture_output=True, timeout=7)
                assert result.returncode == 1 and b'carrier status startup:' in result.stderr
                checks[f'actual_daemon_startup_{name}'] = {'passed': True}
            with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as listener:
                listener.bind(path); listener.listen(1); listener.settimeout(3)
                process = subprocess.Popen(daemon_command,
                                          env={**os.environ, 'SYNTHMODEM_CARRIER_PATH': path},
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                try:
                    peer, _ = listener.accept()
                    with peer:
                        peer.settimeout(3)
                        assert peer.recv(3) == HELLO
                        peer.sendall(b'\x01\x91')
                    stdout, stderr = process.communicate(timeout=3)
                    assert process.returncode == 1 and b'carrier status startup:' in stderr
                    checks['actual_daemon_startup_invalid_HELLO_ack'] = {'passed': True}
                finally:
                    if process.poll() is None: process.kill(); process.wait()
                    process.stdout.close(); process.stderr.close()
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    inputs = [SOURCE / n for n in ('carrier_client.c', 'carrier_client.h',
                                   'carrier_protocol.h', 'client_probe.c')]
    inputs += [Path(__file__), ROOT / 'nix/flake.nix', ROOT / 'nix/flake.lock', ROOT / 'tools/bbs-dev']
    result = {'passed': all(v['passed'] for v in checks.values()), 'checks': checks,
              'compiler': subprocess.check_output(['cc', '--version'], text=True).splitlines()[0],
              'command': command, 'executable_sha256': sha(executable),
              'frozen_inputs': {str(p.relative_to(ROOT)): sha(p) for p in inputs},
              'scope': 'Production carrier client, synthetic Unix seqpacket peer, real Linux PTY; optional actual daemon startup failure checks. No helper server, modem_stop execution, SIP/DSP or physical modem/ATA.'}
    if args.modem_executable:
        result['modem_executable'] = str(args.modem_executable)
        result['modem_executable_sha256'] = sha(args.modem_executable)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
