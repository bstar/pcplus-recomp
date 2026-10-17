#!/usr/bin/env python3
"""Exercise the linked source-only driver through DOSBox-X UART interrupts."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


def run(mode):
    binary_sha256 = hashlib.sha256((ROOT / 'build/standalone/SERIAL.EXE').read_bytes()).hexdigest()
    output = ROOT / 'build/serial-tests' / mode
    output.mkdir(parents=True, exist_ok=True)
    for name in ('PASS.TXT', 'FAIL.TXT'):
        (output / name).unlink(missing_ok=True)
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(1)
    server.settimeout(25)
    checks, events = {}, []
    start = time.monotonic()
    stop = threading.Event()
    arguments = {'none': '', 'software': ' S', 'hardware': ' H'}[mode]
    payload = bytes(range(256)) * 17  # 4352 bytes: wrap the 4096-byte ring.
    if mode == 'software':
        payload = bytes(b for b in payload if b not in (0x11, 0x13))

    def peer():
        try:
            connection, _ = server.accept()
            with connection:
                connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                connection.settimeout(0.1)
                pending = bytearray()

                def receive(size, timeout=6):
                    deadline = time.monotonic() + timeout
                    while len(pending) < size and time.monotonic() < deadline and not stop.is_set():
                        try:
                            data = connection.recv(4096)
                            if not data:
                                break
                            pending.extend(data)
                        except socket.timeout:
                            pass
                    data = bytes(pending[:size])
                    del pending[:size]
                    return data

                checks['ready'] = receive(15) == b'LOC-UART-READY\r'
                # Marker is 15 bytes including CR.
                if not checks['ready']:
                    events.append({'unexpected_startup': pending.hex()})
                    return
                if mode == 'software':
                    connection.sendall(b'\x13')
                    time.sleep(0.1)
                    connection.sendall(b'Z')
                    checks['xon_xoff_pauses_transmit'] = receive(1, 0.3) == b''
                    connection.sendall(b'\x11')
                    checks['xon_resumes_transmit'] = receive(1) == b'Z'
                received = bytearray()
                for offset in range(0, len(payload), 128):
                    part = payload[offset:offset + 128]
                    connection.sendall(part)
                    echo = receive(len(part))
                    received.extend(echo)
                    if echo != part:
                        events.append({'mismatch_at': offset, 'expected': part.hex(), 'received': echo.hex()})
                        break
                checks['binary_echo_across_ring_wrap'] = bytes(received) == payload
                events.append({'payload_bytes': len(payload), 'received_bytes': len(received),
                               'sha256': hashlib.sha256(received).hexdigest()})
                # Keep carrier present until DOS cleanup completes.
                while not stop.wait(0.1):
                    pass
        except OSError as error:
            events.append({'error': str(error)})

    thread = threading.Thread(target=peer, daemon=True)
    thread.start()
    config = f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{ROOT / 'build/standalone'}"
mount d "{output}"
c:
ADDKEY p12000 escape
SERIAL{arguments}
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto done
:failed
echo FAIL>D:\\FAIL.TXT
:done
exit
'''
    (output / 'dosbox.conf').write_text(config)
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    with (output / 'dosbox.log').open('w') as log:
        process = subprocess.Popen(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(output / 'dosbox.conf')],
                                   cwd=output, env=env, stdout=log, stderr=log)
        try:
            code = process.wait(timeout=25)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            code = -1
    stop.set()
    server.close()
    thread.join(timeout=2)
    checks['dos_exit_and_irq_ring_checks'] = code == 0 and (output / 'PASS.TXT').exists() and not (output / 'FAIL.TXT').exists()
    required = ['ready', 'binary_echo_across_ring_wrap', 'dos_exit_and_irq_ring_checks']
    if mode == 'software':
        required += ['xon_xoff_pauses_transmit', 'xon_resumes_transmit']
    result = {'mode': mode, 'passed': all(checks.get(name, False) for name in required), 'checks': checks,
              'seconds': round(time.monotonic() - start, 3), 'events': events,
              'binary_sha256': binary_sha256,
              'scope': 'Source-only DOS executable, emulated UART/PIC/keyboard, loopback TCP; no original PCPlus binary.'}
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)
    return result['passed']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['none', 'software', 'hardware', 'all'], default='all')
    args = parser.parse_args()
    directory = ROOT / 'build/serial-tests'
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / '.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        modes = ['none', 'software', 'hardware'] if args.mode == 'all' else [args.mode]
        results = [run(mode) for mode in modes]
    return 0 if all(results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
