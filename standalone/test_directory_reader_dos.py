#!/usr/bin/env python3
"""Fresh-process8086 tests with independent whole-page and file/handle audit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
from test_terminal import SAMPLER

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['first-page', 'last-full-page', 'last-single-record', 'short-reads17',
         'truncated', 'suffix-rejected', 'missing', 'read-error',
         'close-error-after-release', 'close-error-still-open', 'cancel-open',
         'cancel-read', 'cancel-before-probe', 'cancel-keeps-read-error',
         'invalid-aliases-and-extents', 'read-and-close-errors', 'short-reads511',
         'empty', 'early-zero-read', 'invalid-read-count', 'cancel-before-publish',
         'new-page-after-completion']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--build', type=Path, default=ROOT / 'build/directory-reader')
    args = parser.parse_args()
    out, build = args.output.resolve(), args.build.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    manifest = json.loads((build / 'manifest.json').read_text())
    assert not manifest['original_inputs'] and sha(build / 'READER.EXE') == manifest['binary_sha256']
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    out.mkdir(parents=True)
    shutil.copyfile(build / 'READER.EXE', out / 'READER.EXE')
    (out / 'sampler.asm').write_text(SAMPLER)
    subprocess.run(['nasm', '-fbin', str(out / 'sampler.asm'), '-o', str(out / 'SNAP.COM')], check=True)
    commands, fixtures = [], {}
    full = bytes((i * 37 + 11) & 255 for i in range(23051))
    for mode in range(len(NAMES)):
        leaf = f'T{mode:03}'
        case = out / leaf
        case.mkdir()
        data = b'' if mode == 17 else full[:23049 if mode == 4 else 23051 if mode == 5 else 23050]
        if mode != 6:
            (case / 'FILE.DIR').write_bytes(data)
        fixtures[mode] = data
        commands += [f'cd \\{leaf}', f'..\\READER {mode} >RESULT.TXT', 'if errorlevel 1 goto failed']
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
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
c:
SNAP B
''' + '\n'.join(commands) + '\n'
    (out / 'dosbox.conf').write_text(config)
    with (out / 'dosbox.log').open('w') as log:
        run = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(out / 'dosbox.conf')],
            cwd=out, env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
            stdout=log, stderr=log, timeout=180)
    assert run.returncode == 0 and (out / 'PASS.TXT').exists() and not (out / 'FAIL.TXT').exists(), \
        [(p.parent.name, p.read_text()) for p in out.glob('T*/RESULT.TXT')]
    before, after = (out / 'BEFORE.BIN').read_bytes(), (out / 'AFTER.BIN').read_bytes()
    assert len(before) == 42 and before == after
    cases = []
    successes = {0, 1, 2, 3, 16, 21}
    fields = 'mode status phase dos_error close_error bytes_processed steps opens reads closes max_read max_operations uncertain checks'.split()
    for mode, name in enumerate(NAMES):
        case = out / f'T{mode:03}'
        data = (case / 'RESULT.BIN').read_bytes()
        assert len(data) == 28
        state = dict(zip(fields, struct.unpack('<14H', data)))
        assert state['mode'] == mode and state['max_read'] <= 512 and state['max_operations'] <= 1
        page = (case / 'PAGE.BIN').read_bytes()
        if mode in successes:
            first = 191 if mode == 1 else 200 if mode in (2, 21) else 1
            count = min(10, 201 - first)
            start = 250 + (first - 1) * 114
            wanted = struct.pack('<2H', first, count) + full[:250] + full[start:start + count * 114] + bytes((10 - count) * 114)
            assert page == wanted and state['status'] == 0 and state['phase'] == 4 and not state['uncertain']
        else:
            assert page == bytes([0xa5]) * 1394
        expected = 2 if mode == 6 else 3 if mode in (7, 13, 15, 19) else 4 if mode in (4, 5, 17, 18) else 5 if mode in (8, 9) else 6 if mode in (10, 11, 12, 20) else 0
        assert state['status'] == expected, (name, state)
        if mode in (8, 9, 15):
            assert state['phase'] == 5 and state['close_error'] == 6 and state['uncertain']
        if mode == 14:
            assert state['phase'] == 0 and not state['opens'] and not state['reads'] and not state['closes']
        if mode != 6:
            assert (case / 'FILE.DIR').read_bytes() == fixtures[mode]
        else:
            assert not (case / 'FILE.DIR').exists()
        assert (case / 'RESULT.TXT').read_text().startswith(f'PASS mode{mode} ')
        cases.append(dict(case=name, passed=True, **state))
    artifacts = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
    result = dict(passed=True, cases=cases, case_count=len(cases), native_assertions=sum(c['checks'] for c in cases),
        binary_sha256=manifest['binary_sha256'], hardware_restored=True,
        inputs={**manifest['sources'], str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
                'standalone/test_terminal.py': sha(ROOT / 'standalone/test_terminal.py')},
        artifact_sha256=artifacts,
        scope='Actual8086 DOS read-only kernel files through production FS functions with selected failure/short-read returns injected above them. Independent complete1394-byte page, original files, process JFT and42-byte hardware restoration checked. At most512 input bytes and one DOS operation per reader step; no live parent/BBS or physical driver-time/serial acceptance.')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, cases=len(cases), assertions=result['native_assertions'], output=str(out))))


if __name__ == '__main__':
    main()
