#!/usr/bin/env python3
"""Launch the partial PCPlus rebuild in a persistent, private DOS sandbox."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baud', type=int, choices=[9600, 19200, 38400, 57600, 115200], default=38400)
    parser.add_argument('--cycles', type=int, default=6000)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--smoke', action='store_true', help='bounded headless startup/exit check')
    args = parser.parse_args()
    if not 1000 <= args.cycles <= 30000:
        parser.error('--cycles must be between 1000 and 30000')
    output = ROOT / 'reconstruction/lab' / ('interactive-smoke' if args.smoke else 'interactive')
    output.mkdir(parents=True, exist_ok=True)
    with (output / '.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('This PCPlus sandbox is already running.')
        drive = output / 'drive'
        if not drive.exists():
            shutil.copytree(ROOT / 'analysis/pcplus-install', drive)
        with (output / 'build.log').open('w') as log:
            subprocess.run([sys.executable, str(ROOT / 'reconstruction/build_compat.py')],
                           cwd=ROOT, stdout=log, stderr=log, check=True)
        shutil.copy2(ROOT / 'reconstruction/dist/tech-net-candidate/PCPLUS.EXE', drive / 'PCPLUS.EXE')
        script = f'''proc main
   set port com1
   set baudrate {args.baud}
   set databits 8
   set parity none
   set stopbits 1
   emulate ansi
   transmit "ATNET1^M"
endproc
'''
        (drive / 'PROFILE.ASP').write_bytes(script.replace('\n', '\r\n').encode('ascii'))
        for filename in ('RETURNED.TXT', 'COMPILE.TXT', 'PROFILE.ASX'):
            (drive / filename).unlink(missing_ok=True)
        keys = 'p750 enter p4500 a-x p500 y enter' if args.smoke else 'p750 enter'
        config = f'''[sdl]
fullscreen=false
output=surface
autolock=false
[dosbox]
machine=svga_s3
memsize=8
[cpu]
core=normal
cputype=386
cycles=fixed {args.cycles}
[serial]
serial1=modem listenport:0
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{drive}"
c:
ASPCOMP PROFILE.ASP > COMPILE.TXT
ADDKEY {keys}
PCPLUS
echo RETURNED>RETURNED.TXT
exit
'''
        config_path = output / 'dosbox.conf'
        config_path.write_text(config)
        if args.prepare_only:
            print(config_path)
            return 0
        command = ['dosbox-x', '-fastlaunch', '-conf', str(config_path)]
        env = dict(os.environ)
        if args.smoke:
            command.append('-nogui')
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
        else:
            print('PCPlus COM1, ANSI, 8N1. Type ATDTbbs.example:23 to dial. Alt-X exits.', flush=True)
        with (output / 'dosbox.log').open('w') as log:
            process = subprocess.Popen(command, cwd=output, env=env, stdout=log, stderr=log)
            try:
                code = process.wait(timeout=20 if args.smoke else None)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                return 1
        compiled = 'Script file successfully compiled!' in (drive / 'COMPILE.TXT').read_text(encoding='cp437')
        passed = code == 0 and compiled and (drive / 'RETURNED.TXT').exists()
        if args.smoke:
            result = {'passed': passed, 'returncode': code, 'aspect_compiled': compiled,
                      'returned_to_dos': (drive / 'RETURNED.TXT').exists()}
            (output / 'smoke-result.json').write_text(json.dumps(result, indent=2) + '\n')
            print(json.dumps(result, indent=2))
        return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
