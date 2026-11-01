#!/usr/bin/env python3
"""Source-only queue/fixed-claim/recorder composition in actual 8086 DOS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from test_terminal import SAMPLER

ROOT = Path(__file__).resolve().parents[1]
HEADING = b'\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
START = b'\r\n' + b'LoC LAB'.ljust(22) + b' ' + b'5550100'.rjust(20) + b' 12/31/99 23:59:58 '
END = b'00:00:03 00:00:05'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    c_sources = ['src/directory/' + name + '.c' for name in
                 ('phone_log_queue', 'phone_log_format', 'phone_log_clock', 'phone_log_file', 'phone_log_fs')]
    c_sources += ['src/capture/' + name + '.c' for name in
                  ('capture_file', 'capture_reservation', 'capture_fs')]
    names = c_sources + ['src/directory/' + name + '.h' for name in
                         ('phone_log_queue', 'phone_log_format', 'phone_log_clock', 'phone_log_file', 'phone_log_fs')]
    names += ['src/capture/' + name + '.h' for name in ('capture_file', 'capture_reservation', 'capture_fs')]
    names += ['src/terminal/' + name for name in ('phone_log_bank.asm', 'phone_log_resident.asm',
              'phone_log_storage.asm', 'phone_log_end.asm', 'phone_log_abi.inc', 'far_bridge.inc')]
    names += ['src/config/prm_dos.h', 'standalone/phone_log_reservation_diagnostic.c',
              'standalone/phone_log_bank_client.asm', 'standalone/build_phone_log_bank.py',
              'standalone/build_phone_log_file.py', 'standalone/omf_imports.py',
              'standalone/test_phone_log_reservation_dos.py', 'standalone/test_terminal.py']
    inputs = {name: sha(ROOT / name) for name in names}
    source = out / 'source'
    for name in names:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld',
             '-dCAPTURE_FIXED_RESERVATION', '-dPHONE_LOG_QUEUE_RESERVATION']
    variants = {}
    for variant in ('near', 'far', 'bank'):
        folder = out / variant
        folder.mkdir()
        if variant == 'bank':
            subprocess.run([sys.executable, str(source / 'standalone/build_phone_log_bank.py'),
                            '--reservations', '--output', str(folder)], cwd=source, check=True)
        else:
            variant_flags = flags + (['-dPHONE_LOG_QUEUE_FAR'] if variant == 'far' else [])
            objects = []
            for name in c_sources:
                obj = Path(name).stem + '.obj'
                aliases = ['-dcapture_fs_write=phone_real_write', '-dcapture_fs_close=phone_real_close'] if name.endswith('/capture_fs.c') else []
                subprocess.run(['wcl', '-c', *variant_flags, *aliases, '-fo=' + obj,
                                str(source / name)], cwd=folder, check=True)
                objects.append(obj)
            subprocess.run(['wcl', *variant_flags, '-k8192', '-fm=QUEUE.map', '-fe=QUEUE.EXE',
                            str(source / 'standalone/phone_log_reservation_diagnostic.c'), *objects],
                           cwd=folder, check=True)
        (folder / 'sampler.asm').write_text(SAMPLER)
        subprocess.run(['nasm', '-fbin', str(folder / 'sampler.asm'), '-o', str(folder / 'SNAP.COM')], check=True)
        commands = []
        for case in range(5):
            directory = folder / f'T{case:03}'
            directory.mkdir()
            commands += [f'cd \\T{case:03}', f'..\\QUEUE {case} >RESULT.TXT', 'if errorlevel 1 goto failed']
        commands += ['cd \\', 'echo PASS>PASS.TXT', 'goto capture', ':failed', 'cd \\',
                     'echo FAIL>FAIL.TXT', ':capture', 'SNAP A', 'exit']
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
''' + '\n'.join(commands) + '\n'
        (folder / 'dosbox.conf').write_text(config)
        with (folder / 'dosbox.log').open('w') as log:
            process = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')],
                                     stdout=log, stderr=log, timeout=45,
                                     env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
        cases = {}
        for case in range(5):
            directory = folder / f'T{case:03}'
            read = lambda name: (directory / name).read_bytes() if (directory / name).exists() else b''
            result = read('RESULT.TXT')
            match = re.fullmatch(rb'LOGCLAIM (\d+) checks 0 failures\r\n', result)
            checks = dict(DOS_assertions=bool(match),
                          exact_log=read('CALLS.FON') == HEADING + START + (b'' if case == 2 else END),
                          no_other_log=not (directory / 'OTHER.FON').exists())
            cases[str(case)] = dict(passed=all(checks.values()), checks=checks,
                                   assertions=int(match[1]) if match else 0,
                                   stdout=result.decode('ascii', errors='replace'))
        read = lambda name: (folder / name).read_bytes() if (folder / name).exists() else b''
        checks = dict(DOS_exit=process.returncode == 0 and (folder / 'PASS.TXT').exists()
                      and not (folder / 'FAIL.TXT').exists(), all_cases=all(c['passed'] for c in cases.values()),
                      hardware_restored=len(read('BEFORE.BIN')) == 42 and read('BEFORE.BIN') == read('AFTER.BIN'))
        variants[variant] = dict(passed=all(checks.values()), checks=checks, cases=cases,
                                 binary_sha256=sha(folder / 'QUEUE.EXE'))
    checks = dict(all_variants=all(v['passed'] for v in variants.values()),
                  sources_unchanged=all(sha(ROOT / name) == digest and sha(source / name) == digest
                                        for name, digest in inputs.items()))
    report = dict(passed=all(checks.values()), checks=checks, variants=variants, inputs=inputs,
                  original_inputs=[], limitations=[
                      'Actual DOS foreground queue/claims/recorder composition, not terminal startup/events/poll scheduling.',
                      'Mode2 models close ambiguity after a successful DOS close; mode4 deliberately removes the private claim.',
                      'No physical modem, changing drive namespace, external process exclusion or card deployment proof.'],
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in out.rglob('*') if path.is_file()})
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'artifacts'}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
