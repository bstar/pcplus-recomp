#!/usr/bin/env python3
"""Actual DOS canonical reservations plus explicitly modeled ambiguous closes."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

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
    inputs = [Path(__file__).resolve(), ROOT / 'standalone/capture_reservation_host.c',
              ROOT / 'src/capture/capture_file.c', ROOT / 'src/capture/capture_file.h',
              ROOT / 'src/capture/capture_fs.c', ROOT / 'src/capture/capture_fs.h',
              ROOT / 'src/capture/capture_reservation.c', ROOT / 'src/capture/capture_reservation.h']
    frozen = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    for path in inputs:
        copy = out / 'frozen-source' / path.relative_to(ROOT)
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy)
    base = ['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-k8192', '-i=' + str(ROOT / 'src/capture')]
    subprocess.run(base + ['-nt=RESERVATION_CODE', '-nc=FARCODE', '-c', '-fo=resbank.obj', str(inputs[6])], cwd=out, check=True)
    # A named OMF group prevents the DOS small-model linker from silently
    # merging the far-code class into AUTO at the resident CS. The map check
    # below requires genuinely different segment bases.
    (out / 'bank-group.asm').write_text('BITS 16\nCPU 8086\nSEGMENT RESERVATION_CODE public align=1 class=FARCODE use16\nGROUP RESERVATION_GROUP RESERVATION_CODE\n')
    subprocess.run(['nasm', '-fobj', str(out / 'bank-group.asm'), '-o', str(out / 'bank-group.obj')], check=True)
    for binary, flags, sources in [('RESERVE', [], [inputs[1], inputs[2], inputs[4], inputs[6]]),
                                    ('RESFAULT', ['-dRESERVATION_FAULT'], [inputs[1], inputs[2], inputs[6]]),
                                    ('RBANK', [], [inputs[1], inputs[2], inputs[4], out / 'resbank.obj', out / 'bank-group.obj']),
                                    ('FBANK', ['-dRESERVATION_FAULT'], [inputs[1], inputs[2], out / 'resbank.obj', out / 'bank-group.obj'])]:
        subprocess.run(base + flags + ['-fe=' + binary + '.EXE', '-fm=' + binary + '.map'] + list(map(str, sources)), cwd=out, check=True)
    logs = {}
    checks = {}
    for group, binaries, names in [('near', ('RESERVE', 'RESFAULT'), ('NORMAL', 'TARGET', 'SCRATCH')),
                                   ('bank', ('RBANK', 'FBANK'), ('BANK', 'BNKTARG', 'BNKSCR'))]:
        run = out / group
        run.mkdir()
        for binary in binaries:
            shutil.copy2(out / (binary + '.EXE'), run / (binary + '.EXE'))
        recipes = list(zip(names, [binaries[0], binaries[1], binaries[1] + ' S']))
        commands = '\n'.join(f'{command} >{name}.TXT\nif errorlevel 1 goto failed\necho PASS>{name}.OK' for name, command in recipes)
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
mount c "{run}"
c:
{commands}
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
        (run / 'dosbox.conf').write_text(config)
        with (run / 'dosbox.log').open('w') as log:
            process = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(run / 'dosbox.conf')],
                                     stdout=log, stderr=log, timeout=30,
                                     env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'))
        logs.update({name: (run / (name + '.TXT')).read_text() if (run / (name + '.TXT')).exists() else '' for name, _ in recipes})
        checks[group + '_DOS_normal_exit'] = process.returncode == 0 and not (run / 'FAIL.TXT').exists()
        checks[group + '_all_processes_passed'] = all((run / (name + '.OK')).exists() and ' 0 failures' in logs[name] and 'FAIL ' not in logs[name] for name, _ in recipes)
        for name, data in [('REC.ASP', b'KEEPA'), ('R000.TMP', b'S'), ('OTHER.LOG', b'O'), ('OTHER.BIN', b'M')]:
            checks[group + ':' + name] = (run / name).read_bytes() == data
        checks[group + '_reentrant_calls_never_created_file'] = not (run / 'REENTER.BIN').exists() and not (run / 'HIST.BIN').exists()
    listing = (out / 'RBANK.map').read_text()
    segment = lambda name: re.search(r'(?m)^([0-9a-fA-F]{4}):[0-9a-fA-F]{4}[*+ ]+\s+' + name + r'\s*$', listing)[1]
    checks['real_far_code_bank_and_resident_helper'] = 'RESERVATION_CODE' in listing and segment('_capture_file_reserve') != segment('_capture_file_probe_owners')
    for name, digest in frozen.items():
        assert sha(ROOT / name) == sha(out / 'frozen-source' / name) == digest, name
    result = dict(passed=all(checks.values()), checks=checks, logs=logs, inputs=frozen,
                  binaries={name: sha(out / name) for name in ('RESERVE.EXE', 'RESFAULT.EXE', 'RBANK.EXE', 'FBANK.EXE')},
                  captures_sha256={str(path.relative_to(out)): sha(path) for path in out.rglob('*')
                                  if path.is_file() and not path.is_relative_to(out / 'frozen-source')},
                  scope='Actual DOS canonical target/scratch alias exclusions across four96-byte sink owners, '
                        'registration against existing active owners, independent paths and far probe reentry guards, '
                        'repeated with an actual separate reservation code bank. '
                        'Ambiguous-close cases use an explicit compiled kernel model; no physical close-failure, '
                        'external process lock, host inode identity, recorder publisher/UI or whole-application acceptance.')
    with (out / 'result.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=result['passed'], checks=checks, summaries={name: text.splitlines()[-1:] for name, text in logs.items()})))
    assert result['passed']


if __name__ == '__main__':
    main()
