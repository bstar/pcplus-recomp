#!/usr/bin/env python3
"""Check log startup paths/PRM/retained records in actual8086 DOS."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
from build_phone_log_queue import ROOT, sha
from test_terminal import SAMPLER

HEADING = b'\r\nNAME                                NUMBER    DATE    ONLINE  OFFLINE  ELAPSED'
RECORD = b'\r\n' + b'LoC LAB'.ljust(22) + b' ' + b'5550100'.rjust(20) + b' 12/31/99 23:59:58 00:00:03 00:00:05'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build, output = args.build.resolve(), args.output.resolve()
    assert build.is_relative_to(ROOT / 'build') and output.is_relative_to(ROOT / 'build') and not output.exists()
    manifest = json.loads((build / 'manifest.json').read_text())
    for name, digest in manifest['sources'].items():
        assert sha(ROOT / name) == digest, name
    output.mkdir(parents=True)
    variants = {}
    inputs = dict(manifest['sources'])
    inputs.update({str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), ROOT / 'standalone/test_terminal.py', build / 'manifest.json']})
    for variant in ['near', 'far']:
        folder = output / variant
        folder.mkdir()
        binary = build / variant / 'STARTUP.EXE'
        assert sha(binary) == manifest['outputs'][variant]['binary_sha256']
        shutil.copyfile(binary, folder / 'STARTUP.EXE')
        (folder / 'sampler.asm').write_text(SAMPLER)
        subprocess.run(['nasm', '-fbin', str(folder / 'sampler.asm'), '-o', str(folder / 'SNAP.COM')], check=True)
        commands = ['SNAP B']
        for mode in range(16):
            directory = f'T{mode:03}'
            (folder / directory).mkdir()
            env = ('BAD;DIR' if mode in (0, 1, 8, 13, 14) else
                f'D:\\{directory}\\ENV' if mode in (2, 3, 5, 6) else
                f'D:\\{directory}\\MISSING' if mode == 7 else
                'D:\\' + 'L'*60 if mode == 9 else '')
            commands += [f'SET PCPLUS={env}', f'cd \\{directory}',
                f'D:\\STARTUP {mode} >RESULT.TXT', f'if errorlevel 1 goto failed{mode}',
                f'goto next{mode}', f':failed{mode}', 'echo FAIL>D:\\FAIL.TXT',
                f':next{mode}', 'cd \\']
        commands += ['if exist FAIL.TXT goto finish', 'echo PASS>PASS.TXT', ':finish', 'SNAP A', 'exit']
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
mount d "{folder}"
d:
''' + '\n'.join(commands) + '\n'
        (folder / 'dosbox.conf').write_text(config)
        with (folder / 'dosbox.log').open('w') as log:
            code = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')],
                cwd=folder, stdout=log, stderr=log, timeout=45,
                env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')).returncode
        cases = {}
        for mode in range(16):
            directory = folder / f'T{mode:03}'
            text = (directory / 'RESULT.TXT').read_bytes()
            match = re.fullmatch(rb'STARTUP (\d+) checks 0 failures\r\n', text)
            state_path = directory / 'STATE.BIN'
            state = struct.unpack('<4H', state_path.read_bytes()) if state_path.exists() else ()
            expected_status = 4 if mode in (5, 6, 7) else 2 if mode in (8, 9, 14) else 1 if mode in (10, 12, 15) else 258 if mode in (11, 13) else 0
            checks = dict(native_assertions=bool(match), expected_status=bool(state) and state[0:3] == (mode, expected_status, int(mode in (1, 2, 3, 4, 11, 13, 14, 15))),
                assertion_count=bool(match) and bool(state) and int(match[1]) == state[3]+3)
            # DOSBox's host-side DOS attribute sidecar is not a DOS-visible log.
            # Retain its bytes in the complete artifact hashes below.
            paths = {str(p.relative_to(directory)): p.read_bytes() for p in directory.rglob('*.FON')
                if p.is_file() and not p.name.startswith('.DBLOCALFILE_ATR_')}
            expected = {'ENV/PCPLUS.FON': HEADING+RECORD} if mode == 2 else {'OTHER.FON': HEADING+RECORD} if mode in (11, 13, 14, 15) else {'PCPLUS.FON': HEADING+RECORD} if mode in (1, 3, 4) else {'PCPLUS.FON': b''} if mode == 5 else {}
            if mode == 3:
                expected['ENV/PCPLUS.FON'] = b'UNTOUCHED'
            checks['exact_files_and_paths'] = paths == expected
            cases[str(mode)] = dict(passed=all(checks.values()), checks=checks, stdout=text.decode('ascii', errors='replace'), state=state)
        before, after = (folder / 'BEFORE.BIN').read_bytes(), (folder / 'AFTER.BIN').read_bytes()
        checks = dict(DOS_exit=code == 0 and (folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists(),
            all_cases=all(c['passed'] for c in cases.values()), hardware_restored=len(before) == 42 and before == after,
            executable_unchanged=sha(folder / 'STARTUP.EXE') == sha(binary))
        variants[variant] = dict(passed=all(checks.values()), checks=checks, cases=cases, binary_sha256=sha(binary))
    checks = dict(all_variants=all(v['passed'] for v in variants.values()),
        inputs_unchanged=all(sha(ROOT / name) == digest for name, digest in inputs.items()))
    result = dict(passed=all(checks.values()), checks=checks, variants=variants, inputs=inputs,
        original_inputs=[], artifacts={str(p.relative_to(ROOT)): sha(p) for p in output.rglob('*') if p.is_file()},
        scope=__doc__ + ' Near/far queue storage, real inherited environment/metadata/canonical paths, deferred file creation, CWD changes, rejected retarget with a pending event, exact log bytes, DS=SS/JFT/kernel preservation. Not yet application startup, reservations, connection-event hooks or poll scheduling.')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks,
        failures={v:{m:c for m,c in r['cases'].items() if not c['passed']} for v,r in variants.items()}), indent=2))
    assert result['passed']


if __name__ == '__main__':
    main()
