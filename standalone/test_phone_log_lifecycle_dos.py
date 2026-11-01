#!/usr/bin/env python3
"""Build and run source-only call-event retention in actual 8086 DOS."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
from test_terminal import SAMPLER

ROOT = Path(__file__).resolve().parents[1]
HEADING = b'\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
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
    sources = ['src/directory/' + n + '.c' for n in ('phone_log_lifecycle',
        'phone_log_queue', 'phone_log_format', 'phone_log_clock', 'phone_log_file', 'phone_log_fs')]
    sources += ['src/capture/capture_fs.c']
    names = sources + [n.replace('.c', '.h') for n in sources] + [
        'src/config/prm_dos.h', 'standalone/phone_log_lifecycle_diagnostic.c',
        'standalone/test_phone_log_lifecycle_dos.py', 'standalone/test_terminal.py']
    inputs = {name: sha(ROOT / name) for name in names}
    source = out / 'source'
    for name in names:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    variants = {}
    for variant in ('near', 'far'):
        folder = out / variant
        folder.mkdir()
        flags = ['-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-zld']
        if variant == 'far':
            flags += ['-dPHONE_LOG_QUEUE_FAR']
        objects = []
        for name in sources:
            obj = Path(name).stem + '.obj'
            aliases = []
            if name.endswith('/phone_log_queue.c'):
                aliases = ['-dphone_log_queue_end=lifecycle_real_queue_end']
            if name.endswith('/capture_fs.c'):
                aliases = ['-dcapture_fs_write=phone_real_write', '-dcapture_fs_close=phone_real_close']
            subprocess.run(['wcl', '-c', *flags, *aliases, '-fo=' + obj,
                            str(source / name)], cwd=folder, check=True)
            objects.append(obj)
        subprocess.run(['wcl', *flags, '-k8192', '-fm=LIFE.map', '-fe=LIFE.EXE',
                        str(source / 'standalone/phone_log_lifecycle_diagnostic.c'), *objects],
                       cwd=folder, check=True)
        (folder / 'sampler.asm').write_text(SAMPLER)
        subprocess.run(['nasm', '-fbin', str(folder / 'sampler.asm'), '-o', str(folder / 'SNAP.COM')], check=True)
        commands = []
        for case in range(6):
            (folder / f'T{case:03}').mkdir()
            commands += [f'cd \\T{case:03}', f'..\\LIFE {case} >RESULT.TXT', 'if errorlevel 1 goto failed']
        commands += ['cd \\', 'echo PASS>PASS.TXT', 'goto capture', ':failed', 'cd \\',
                     'echo FAIL>FAIL.TXT', ':capture', 'SNAP A', 'exit']
        config = f'''[sdl]
output=surface
[dosbox]
quit warning=false
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
        for case in range(6):
            location = folder / f'T{case:03}'
            read = lambda n: (location / n).read_bytes() if (location / n).exists() else b''
            stdout = read('RESULT.TXT')
            match = re.fullmatch(rb'LIFECYCLE (\d+) checks 0 failures\r\n', stdout)
            names_expected = [b'LoC LAB', b'TWO', b'THREE'] if case == 1 else [b'LoC LAB']
            expected = HEADING + b''.join(b'\r\n' + name.ljust(22) + b' ' + b'5550100'.rjust(20)
                + b' 12/31/99 23:59:58 ' + (b'' if case == 4 else END) for name in names_expected)
            context = read('CONTEXT.BIN')
            checks = dict(DOS_assertions=bool(match) and int(match[1]) >= 30,
                exact_log=not (location / 'CALLS.FON').exists() if case == 5 else read('CALLS.FON') == expected,
                DS_equals_SS=len(context) == 4 and struct.unpack('<2H', context)[0] == struct.unpack('<2H', context)[1])
            cases[str(case)] = dict(passed=all(checks.values()), checks=checks,
                assertions=int(match[1]) if match else 0, stdout=stdout.decode('ascii', errors='replace'))
        read = lambda n: (folder / n).read_bytes() if (folder / n).exists() else b''
        checks = dict(DOS_exit=process.returncode == 0 and (folder / 'PASS.TXT').exists()
            and not (folder / 'FAIL.TXT').exists(), all_cases=all(c['passed'] for c in cases.values()),
            hardware_restored=len(read('BEFORE.BIN')) == 42 and read('BEFORE.BIN') == read('AFTER.BIN'))
        variants[variant] = dict(passed=all(checks.values()), checks=checks, cases=cases,
            binary_sha256=sha(folder / 'LIFE.EXE'))
    checks = dict(all_variants=all(v['passed'] for v in variants.values()),
        sources_unchanged=all(sha(ROOT / n) == d and sha(source / n) == d for n, d in inputs.items()))
    report = dict(passed=all(checks.values()), checks=checks, variants=variants, inputs=inputs,
        original_inputs=[], limitations=['Component producer; not yet banked or hooked into the terminal.',
        'END refusal is an explicit wrapper fault; actual queue saturation tests exercise admission.',
        'Ambiguous close is modeled after actual DOS close. Generation wrap, child clock/handoff and physical transport are not covered.'],
        artifacts={str(p.relative_to(ROOT)): sha(p) for p in out.rglob('*') if p.is_file()})
    (out / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'artifacts'}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
