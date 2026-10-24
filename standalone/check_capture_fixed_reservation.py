#!/usr/bin/env python3
"""Actual8086 DOS fixed/dynamic canonical exclusions, near/far bank and close ambiguity."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from test_terminal import SAMPLER

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    names = ['src/capture/' + name for name in ['capture_file.c', 'capture_file.h', 'capture_fs.c',
             'capture_fs.h', 'capture_reservation.c', 'capture_reservation.h']]
    names += ['standalone/capture_fixed_reservation_host.c', 'standalone/check_capture_fixed_reservation.py',
              'standalone/test_terminal.py', 'src/terminal/far_bridge.inc']
    sources = {name: sha(ROOT / name) for name in names}
    for name in names:
        target = out / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    source = out / 'source'
    flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-dCAPTURE_FIXED_RESERVATION']
    aliases = dict(strcmp='fixed_strcmp_service', memcpy='fixed_memcpy_service',
                   memset='fixed_memset_service', capture_file_validate_path='fixed_validate_service')
    subprocess.run(['wcl', '-c', *flags, '-nt=FIXED_CODE', '-nc=FARCODE',
                    *['-d' + key + '=' + value for key, value in aliases.items()], '-fo=fixed.obj',
                    str(source / 'src/capture/capture_reservation.c')], cwd=out, check=True)
    (out / 'far.asm').write_text('''BITS 16
CPU 8086
SEGMENT FIXED_CODE public align=16 class=FARCODE use16
GROUP FIXED_GROUP FIXED_CODE
%include "far_bridge.inc"
%macro REGISTER 2
global %1
extern %1 %+ _resident
%1:
call far %1 %+ _resident
ret
%endmacro
REGISTER fixed_strcmp_service_,strcmp_
REGISTER fixed_memcpy_service_,memcpy_
REGISTER fixed_memset_service_,memset_
FAR_CDECL_SERVICE _fixed_validate,_capture_file_validate_path,2
SEGMENT _TEXT public class=CODE use16
NEAR_NAMED_SERVICE fixed_strcmp_service_,strcmp_
NEAR_NAMED_SERVICE fixed_memcpy_service_,memcpy_
NEAR_NAMED_SERVICE fixed_memset_service_,memset_
NEAR_CDECL_SERVICE _fixed_validate,_capture_file_validate_path,2
''')
    subprocess.run(['nasm', '-fobj', '-I' + str(source / 'src/terminal') + '/',
                    str(out / 'far.asm'), '-o', str(out / 'far.obj')], check=True)
    (out / 'sampler.asm').write_text(SAMPLER)
    subprocess.run(['nasm', '-fbin', str(out / 'sampler.asm'), '-o', str(out / 'SNAP.COM')], check=True)
    cases = {}
    for bank in [False, True]:
        for fault in [False, True]:
            name = ('bank' if bank else 'near') + ('-fault' if fault else '-dos')
            folder = out / name
            folder.mkdir()
            objects = [out / 'fixed.obj', out / 'far.obj'] if bank else [source / 'src/capture/capture_reservation.c']
            objects += [source / 'standalone/capture_fixed_reservation_host.c', source / 'src/capture/capture_file.c']
            if not fault:
                objects += [source / 'src/capture/capture_fs.c']
            subprocess.run(['wcl', *flags, *(['-dFIXED_FAULT'] if fault else []), '-k8192',
                            '-fe=FIXED.EXE', '-fm=FIXED.map', *map(str, objects)], cwd=folder, check=True)
            shutil.copyfile(out / 'SNAP.COM', folder / 'SNAP.COM')
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
mount c "{folder}"
mount d "{folder}"
c:
SNAP B
FIXED >RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto capture
:failed
echo FAIL>FAIL.TXT
:capture
SNAP A
exit
'''
            (folder / 'dosbox.conf').write_text(config)
            with (folder / 'dosbox.log').open('w') as log:
                process = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')],
                    stdout=log, stderr=log, timeout=30,
                    env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
            read = lambda name: (folder / name).read_bytes() if (folder / name).exists() else b''
            result = read('RESULT.TXT')
            match = re.fullmatch(rb'FIXED (\d+) checks 0 failures\r\n', result)
            checks = dict(actual_assertions=bool(match), DOS_exit=process.returncode == 0 and
                          (folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists(),
                          hardware_restored=len(read('BEFORE.BIN')) == 42 and read('BEFORE.BIN') == read('AFTER.BIN'),
                          no_reentry_files=not (folder / 'REENTER.BIN').exists() and not (folder / 'REENTER.FON').exists())
            if not fault:
                checks.update(log_bytes=read('CALLS.FON') == b'KEEPA', unrelated_bytes=read('OTHER.LOG') == b'OTHER',
                              no_recorder_files=not (folder / 'REC.ASP').exists() and not (folder / 'R000.TMP').exists())
            listing = (folder / 'FIXED.map').read_text()
            segment = lambda symbol: re.search(r'(?m)^([0-9a-fA-F]{4}):[0-9a-fA-F]{4}[*+ ]+\s+' + symbol + r'\s*$', listing)[1]
            checks['placement'] = (segment('_capture_file_claim') != segment('_capture_file_probe_owners')) == bank
            cases[name] = dict(passed=all(checks.values()), checks=checks, assertions=int(match[1]) if match else 0,
                               stdout=result.decode('ascii', errors='replace'), binary_sha256=sha(folder / 'FIXED.EXE'))
    checks = dict(all_cases=all(case['passed'] for case in cases.values()),
                  unchanged_sources=all(sha(ROOT / name) == sha(out / 'source' / name) == digest for name, digest in sources.items()))
    report = dict(passed=all(checks.values()), checks=checks, sources=sources, cases=cases, original_inputs=[],
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in out.rglob('*') if path.is_file()},
                  scope='Actual DOS fixed/dynamic claims and four capture owners with near/far reservation code. Close ambiguity explicitly modeled in two cases. Not logger claim lifetime or whole-application acceptance.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks, cases=cases), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
