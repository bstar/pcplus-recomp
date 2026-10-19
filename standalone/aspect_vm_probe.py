#!/usr/bin/env python3
"""Private original-ASPECT startup/control-flow DOS runtime oracle.

Run with pinned tools/dev. Copies the original installation into a new ignored
sandbox, compiles source-owned PROFILE.ASP, and observes actual original PCPlus
serial output. No reconstructed VM or maintained application is substituted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
APP_SHA = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
COMPILER_SHA = '5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def script(case):
    prefix = '''proc main
 set port com1
 set baudrate 38400
 set databits 8
 set parity none
 set stopbits 1
 emulate ansi
 transmit "LOC-BEGIN^M"
'''
    if case == 'flow':
        body = ''' call helper
 if 1
  transmit "LOC-TRUE^M"
 else
  transmit "LOC-BAD-IF^M"
 endif
 while 0
  transmit "LOC-BAD-WHILE^M"
 endwhile
 transmit "LOC-END^M"
endproc
proc helper
 transmit "LOC-HELPER^M"
endproc
'''
        expected = b'LOC-BEGIN\rLOC-HELPER\rLOC-TRUE\rLOC-END\r'
    elif case == 'false':
        body = ''' if 0
  transmit "LOC-BAD-IF^M"
 else
  transmit "LOC-FALSE^M"
 endif
 transmit "LOC-END^M"
endproc
'''
        expected = b'LOC-BEGIN\rLOC-FALSE\rLOC-END\r'
    else:
        raise ValueError(case)
    return (prefix+body).replace('\n', '\r\n').encode('ascii'), expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=['flow', 'false'], default='flow')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.parent == ROOT/'analysis/aspect-vm-runtime'
    source_install = ROOT/'analysis/pcplus-install'
    source_hashes = {p.name: sha(p.read_bytes()) for p in source_install.iterdir() if p.is_file()}
    assert source_hashes['PCPLUS.EXE'] == APP_SHA and source_hashes['ASPCOMP.EXE'] == COMPILER_SHA
    assert not out.exists()
    out.mkdir(parents=True)
    drive = out/'drive'
    shutil.copytree(source_install, drive)
    text, expected = script(args.case)
    (drive/'PROFILE.ASP').write_bytes(text)
    assert not (drive/'PROFILE.ASX').exists()
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(1)
    server.settimeout(20)
    started = time.monotonic()
    stopping = threading.Event()
    events, checks, wire = [], {}, bytearray()
    def event(kind, **fields):
        events.append(dict(kind=kind, seconds=round(time.monotonic()-started, 4), **fields))
    def peer():
        try:
            conn, _ = server.accept()
            event('connected')
            with conn:
                conn.settimeout(.1)
                sent_query = False
                while not stopping.is_set():
                    try:
                        data = conn.recv(4096)
                        if not data:
                            break
                        wire.extend(data)
                        event('serial-rx', hex=data.hex())
                        if b'LOC-END\r' in wire and not sent_query:
                            query = b'\x1b[2J\x1b[H\x1b[5n'
                            conn.sendall(query)
                            event('serial-tx', hex=query.hex())
                            sent_query = True
                    except socket.timeout:
                        pass
        except OSError as error:
            event('peer-error', error=str(error))
    worker = threading.Thread(target=peer, daemon=True)
    worker.start()
    config = f'''[sdl]
output=surface
[dosbox]
machine=svga_s3
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
mount c "{drive}"
c:
ASPCOMP PROFILE.ASP > COMPILE.TXT
ADDKEY p750 enter p6000 k p1000 a-x p500 y enter
PCPLUS
echo RETURNED>RETURNED.TXT
exit
'''
    (out/'dosbox.conf').write_text(config)
    returncode, timeout = None, False
    with (out/'dosbox.log').open('w') as log:
        process = subprocess.Popen(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out/'dosbox.conf')],
            cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'), stdout=log, stderr=log)
        try:
            returncode = process.wait(timeout=25)
        except subprocess.TimeoutExpired:
            timeout = True
            event('deadline')
            process.terminate()
            try:
                returncode = process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                returncode = process.wait()
    stopping.set()
    server.close()
    worker.join(timeout=1)
    log = (drive/'COMPILE.TXT').read_bytes() if (drive/'COMPILE.TXT').exists() else b''
    asx = drive/'PROFILE.ASX'
    checks.update(compiled=b'Script file successfully compiled!' in log,
        expected_script_order=expected in wire,
        no_unselected_branch=b'LOC-BAD' not in wire,
        terminal_resumed=b'\x1b[0n' in wire,
        keyboard_after_script=b'k' in wire[wire.find(b'LOC-END\r')+8:] if b'LOC-END\r' in wire else False,
        original_app_unchanged=sha((drive/'PCPLUS.EXE').read_bytes()) == APP_SHA,
        returned_to_dos=returncode == 0 and not timeout and (drive/'RETURNED.TXT').exists(),
        source_install_unchanged=source_hashes == {p.name: sha(p.read_bytes()) for p in source_install.iterdir() if p.is_file()})
    (out/'serial.bin').write_bytes(wire)
    report = dict(passed=all(checks.values()), case=args.case, checks=checks,
        original_application_sha256=APP_SHA, original_compiler_sha256=COMPILER_SHA,
        harness_sha256=sha(Path(__file__).read_bytes()), source_sha256=sha(text),
        asx_sha256=sha(asx.read_bytes()) if asx.exists() else None,
        compile_log_sha256=sha(log), serial_sha256=sha(wire), returncode=returncode,
        timed_out=timeout, expected_script_hex=expected.hex(), serial_hex=wire.hex(),
        copied_install_input_sha256=source_hashes, events=events,
        scope='Original unmodified PCPlus and ASPCOMP in DOSBox-X; source-owned script compiled and run by original startup VM, loopback emulated UART and BIOS keyboard; no maintained VM, real modem, hardware, or public BBS.')
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('events', 'copied_install_input_sha256')}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
