#!/usr/bin/env python3
"""Run queued call logging in real 8086 DOS with near and far event storage."""
import argparse
import datetime as dt
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
START = dt.datetime(1999, 12, 31, 23, 59, 58)
END = dt.datetime(2000, 1, 1, 0, 0, 3)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def begin(name, number, stamp):
    date = f'{stamp.month:02}/{stamp.day:02}/{stamp.year % 100:02}'
    return b'\r\n' + name[:22].ljust(22) + b' ' + number.rjust(20) + f' {date} {stamp:%H:%M:%S} '.encode()


def finish(start, end):
    elapsed = int((end - start).total_seconds())
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f'{end:%H:%M:%S} {hours:02}:{minutes:02}:{seconds:02}'.encode()


def expected_file(case, folder):
    if case == 7:
        return None
    start, end = START, END
    names = [b'LoC LAB']
    number = b'5550100'
    if case == 2:
        names = [b'ONE', b'TWO', b'THREE']
    elif case == 4:
        names = [b'MAX', b'WRAP']
    elif case == 5:
        names, number = [bytes([219]) * 63], b'N' * 63
        start, end = dt.datetime(1980, 1, 1), dt.datetime(2099, 12, 31, 23, 59, 59)
    elif case == 6:
        names = [b'GUARDS']
    elif case == 8:
        start = end = dt.datetime(*struct.unpack('<6H', (folder / 'STAMP.BIN').read_bytes()))
        assert 1980 <= start.year <= 2099
        names = [b'CLOCK']
    return HEADING + b''.join(begin(name, number, start) + (b'' if case == 3 else finish(start, end)) for name in names)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=['near', 'far'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    build = ROOT / 'build/phone-log-queue'
    manifest = json.loads((build / 'manifest.json').read_text())
    binary = build / args.variant / 'QUEUE.EXE'
    assert not manifest['original_inputs']
    assert sha(binary) == manifest['outputs'][args.variant]['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    shutil.copyfile(binary, out / 'QUEUE.EXE')
    (out / 'sampler.asm').write_text(SAMPLER)
    subprocess.run(['nasm', '-fbin', str(out / 'sampler.asm'), '-o', str(out / 'SNAP.COM')], check=True)
    commands = []
    for case in range(9):
        name = f'T{case:03}'
        (out / name).mkdir()
        commands += [f'cd \\{name}', f'..\\QUEUE {case} >RESULT.TXT', 'if errorlevel 1 goto failed']
    commands += ['cd \\', 'echo PASS>PASS.TXT', 'goto capture', ':failed',
                 'cd \\', 'echo FAIL>FAIL.TXT', ':capture', 'SNAP A', 'exit']
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
''' + '\n'.join(commands) + '\n'
    (out / 'dosbox.conf').write_text(config)
    inputs = dict(manifest['sources'])
    inputs.update({str(path.relative_to(ROOT)): sha(path) for path in [Path(__file__),
        ROOT / 'standalone/test_terminal.py', build / 'manifest.json', binary,
        binary.with_suffix('.map'), out / 'QUEUE.EXE', out / 'SNAP.COM',
        out / 'sampler.asm', out / 'dosbox.conf']})
    with (out / 'dosbox.log').open('w') as log:
        code = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
            cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
            stdout=log, stderr=log, timeout=45).returncode
    cases = {}
    generations = [1, 10, 102, 9, 1, 50, 60, 0, 80]
    committed = [2, 2, 6, 0, 4, 2, 2, 0, 2]
    for case in range(9):
        folder = out / f'T{case:03}'
        read = lambda name: (folder / name).read_bytes() if (folder / name).exists() else b''
        result, state, context = read('RESULT.TXT'), read('STATE.BIN'), read('CONTEXT.BIN')
        expected_state = (int(case != 7), *([1, 1, 1, 1, 9] if case == 3 else [0] * 5),
                          generations[case], 0 if case == 3 else generations[case], committed[case])
        fields = struct.unpack('<8H', context) if len(context) == 16 else ()
        checks = dict(DOS_assertions=bool(re.fullmatch(rb'PASS \d+ queue assertions\r\n', result)),
                      exact_state=state == struct.pack('<6H3I', *expected_state), actual_context=bool(fields))
        try:
            expected = expected_file(case, folder)
            actual = read('CALLS.FON') if (folder / 'CALLS.FON').exists() else None
            checks['exact_file'] = actual == expected
        except (ValueError, OSError, struct.error, AssertionError):
            checks['exact_file'] = False
        if fields:
            checks.update(DS_equals_SS=fields[0] == fields[1] and fields[0] != 0,
                          storage_placement=(fields[2] != fields[0]) == (args.variant == 'far'),
                          native_sizes=fields[4:6] == (666, 24),
                          reentry_exercised=(fields[7] == 0) == (case == 7),
                          alias_guard=case != 6 or args.variant == 'far' or fields[6] == 1)
        cases[str(case)] = dict(passed=all(checks.values()), checks=checks,
            assertions=result.decode('ascii', errors='replace').strip(),
            state=list(struct.unpack('<6H3I', state)) if len(state) == 24 else [], context=list(fields))
    before = (out / 'BEFORE.BIN').read_bytes() if (out / 'BEFORE.BIN').exists() else b''
    after = (out / 'AFTER.BIN').read_bytes() if (out / 'AFTER.BIN').exists() else b''
    checks = dict(DOS_exit=code == 0 and (out / 'PASS.TXT').exists() and not (out / 'FAIL.TXT').exists(),
                  all_cases=all(case['passed'] for case in cases.values()),
                  hardware_restored=len(before) == 42 and before == after,
                  inputs_unchanged=inputs == {name: sha(ROOT / name) for name in inputs})
    report = dict(passed=all(checks.values()), checks=checks, cases=cases, inputs=inputs,
                  variant=args.variant, binary_sha256=sha(binary),
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in out.rglob('*') if path.is_file()},
                  scope='Actual8086 DOS event queue, calendar, PRM flag and checked append; near/far storage, independent exact file/state and DS=SS/JFT/kernel checks. Selected explicit faults, not terminal/modem scheduler or physical media failure.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], variant=args.variant, checks=checks,
                         failed={name: row for name, row in cases.items() if not row['passed']}), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
