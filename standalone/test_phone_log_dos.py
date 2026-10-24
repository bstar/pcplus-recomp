#!/usr/bin/env python3
"""Actual8086 DOS append/create/failure checks on new synthetic media only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from test_terminal import SAMPLER

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    build = ROOT / 'build/phone-log'
    manifest = json.loads((build / 'manifest.json').read_text())
    assert not manifest['original_inputs'] and sha(build / 'PHONELOG.EXE') == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    shutil.copyfile(build / 'PHONELOG.EXE', out / 'PHONELOG.EXE')
    (out / 'sampler.asm').write_text(SAMPLER)
    subprocess.run(['nasm', '-fbin', str(out / 'sampler.asm'), '-o', str(out / 'SNAP.COM')], check=True)
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
c:
SNAP B
PHONELOG >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto capture
:failed
echo FAIL>FAIL.TXT
:capture
SNAP A
exit
'''
    (out / 'dosbox.conf').write_text(config)
    inputs = {str(path.relative_to(ROOT)): sha(path) for path in [
        Path(__file__), ROOT / 'standalone/test_terminal.py', build / 'manifest.json',
        build / 'PHONELOG.EXE', out / 'PHONELOG.EXE', out / 'SNAP.COM', out / 'sampler.asm', out / 'dosbox.conf']}
    with (out / 'dosbox.log').open('w') as log:
        code = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')], cwd=out,
            env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'), stdout=log, stderr=log, timeout=20).returncode
    def read(name):
        return (out / name).read_bytes() if (out / name).exists() else b''
    heading = b'\r\n' + b'NAME'.ljust(36) + b'NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
    start = b'\r\n' + b'LoC LAB'.ljust(22) + b' ' + b'5550100'.rjust(20) + b' 10/24/26 12:34:56 '
    finish = b'12:35:58 00:01:02'
    checks = dict(DOS_exit=code == 0 and (out / 'PASS.TXT').exists() and not (out / 'FAIL.TXT').exists(),
                  diagnostic=read('RESULT.TXT') == b'PASS 33 DOS phone-log checks\r\n',
                  exact_CRLF_two_records=read('NEW.FON') == heading + (start + finish) * 2,
                  skipped_events_create_no_files=not (out / 'MISSING.FON').exists() and not (out / 'NOEXIST').exists(),
                  hardware_restored=len(read('BEFORE.BIN')) == 42 and read('BEFORE.BIN') == read('AFTER.BIN'),
                  binary_unchanged=sha(out / 'PHONELOG.EXE') == manifest['binary_sha256'],
                  inputs_unchanged=inputs == {name: sha(ROOT / name) for name in inputs})
    report = dict(passed=all(checks.values()), checks=checks, binary_sha256=manifest['binary_sha256'],
                  inputs=inputs, sources=manifest['sources'],
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in out.rglob('*') if path.is_file()},
                  scope='Actual8086 DOS recovered controller plus declared synthetic clock/path callbacks, actual FILE append/CRLF/error and JFT restoration; no terminal/UART logging integration.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks, output=read('RESULT.TXT').decode('ascii', errors='replace')), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
