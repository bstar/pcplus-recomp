#!/usr/bin/env python3
"""18 fresh-process8086 DOS checked-append cases with independent file/state audit."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    out.mkdir(parents=True)
    build = ROOT / 'build/phone-log-file'
    manifest = json.loads((build / 'manifest.json').read_text())
    assert not manifest['original_inputs'] and sha(build / 'PHONEAPP.EXE') == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    shutil.copyfile(build / 'PHONEAPP.EXE', out / 'PHONEAPP.EXE')
    (out / 'sampler.asm').write_text(SAMPLER)
    subprocess.run(['nasm', '-fbin', str(out / 'sampler.asm'), '-o', str(out / 'SNAP.COM')], check=True)
    commands = []
    for case in range(18):
        name = f'T{case:03}'
        (out / name).mkdir()
        commands += [f'cd \\{name}', f'..\\PHONEAPP {case} >RESULT.TXT',
                     'if errorlevel 1 goto failed']
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
        ROOT / 'standalone/test_terminal.py', build / 'manifest.json', build / 'PHONEAPP.EXE',
        out / 'PHONEAPP.EXE', out / 'SNAP.COM', out / 'sampler.asm', out / 'dosbox.conf']})
    with (out / 'dosbox.log').open('w') as log:
        code = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
            cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
            stdout=log, stderr=log, timeout=45).returncode
    cases = {}
    complete = {0, 1, 2, 3, 10, 11, 15, 16, 17}
    for case in range(18):
        folder = out / f'T{case:03}'
        result = (folder / 'RESULT.TXT').read_bytes() if (folder / 'RESULT.TXT').exists() else b''
        state = (folder / 'STATE.BIN').read_bytes() if (folder / 'STATE.BIN').exists() else b''
        fields = struct.unpack('<15H2I128s', state) if len(state) == 166 else ()
        initial = 70001 if case in (10, 16) else 0 if case in (11, 15) else 8
        prefix = bytes((i * 37 + 11) & 255 for i in range(initial))
        expected = prefix
        if case in complete:
            expected += bytes(range(256)) if case == 17 else (b'HEADING\r\n' if not initial else b'') + b'EVENT\r\n'
        elif case in (4, 5):
            expected += b'EVE'
        elif case in (8, 9):
            expected += b'EVENT\r\n'
        data = (folder / 'CALLS.FON').read_bytes() if (folder / 'CALLS.FON').exists() else None
        checks = dict(DOS_assertions=bool(re.fullmatch(rb'PASS \d+ checked-append assertions\r\n', result)),
                      actual_snapshot=len(state) == 166, exact_file=data == expected,
                      no_foreign_parent=not (folder / 'NOEXIST').exists())
        if fields:
            if case in complete:
                checks['owner_state'] = fields[:2] == (1, 0) and fields[5:9] == (0, 0, 0, 1)
                checks['geometry'] = fields[15:17] == (initial, len(expected))
                checks['heading_once'] = fields[10] == (9 if not initial else 0)
            elif case in (4, 5, 6, 7, 8, 9):
                checks['owner_state'] = fields[:2] == (3, 9 if case in (8, 9) else 7) and fields[5] == 0 and fields[7:9] == (1, 0)
                checks['failure_retained'] = (fields[4] == 6 and fields[6] == 1) if case in (7, 8, 9) else fields[3] == 5
                checks['close_once'] = fields[14] == 1
                checks['observed_EOF'] = fields[15:17] == (initial, len(expected))
            elif case in (12, 14):
                checks['owner_state'] = fields[:2] == (2, 5 if case == 14 else 4) and fields[5:9] == (0, 0, 0, 0)
                checks['actual_DOS_error'] = fields[2] == (3 if case == 14 else 5)
            else:
                checks['owner_state'] = fields[:15] == (0,) * 15
        cases[str(case)] = dict(passed=all(checks.values()), checks=checks,
            assertions=result.decode('ascii', errors='replace').strip(),
            state=list(fields[:17]) if fields else [], path=fields[17].split(b'\0', 1)[0].decode('ascii') if fields else None)
    before = (out / 'BEFORE.BIN').read_bytes() if (out / 'BEFORE.BIN').exists() else b''
    after = (out / 'AFTER.BIN').read_bytes() if (out / 'AFTER.BIN').exists() else b''
    checks = dict(DOS_exit=code == 0 and (out / 'PASS.TXT').exists() and not (out / 'FAIL.TXT').exists(),
                  all_cases=all(case['passed'] for case in cases.values()),
                  hardware_restored=len(before) == 42 and before == after,
                  inputs_unchanged=inputs == {name: sha(ROOT / name) for name in inputs})
    report = dict(passed=all(checks.values()), checks=checks, cases=cases, inputs=inputs,
                  binary_sha256=manifest['binary_sha256'],
                  artifacts={str(path.relative_to(ROOT)): sha(path) for path in out.rglob('*') if path.is_file()},
                  scope='Actual8086 DOS checked append, explicit failure-result injection around real prefix writes/seek/truncate/commit/close; independent byte/state/JFT/kernel-snapshot checks. Not actual media failure/power loss, terminal/UART event integration or external concurrency.')
    (out / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], checks=checks,
                         failed={name: row for name, row in cases.items() if not row['passed']}), indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
