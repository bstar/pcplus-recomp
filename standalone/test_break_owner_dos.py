#!/usr/bin/env python3
"""Exercise guarded Ctrl-Break ownership around real DOS child execution."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default='dos-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    out = ROOT / 'build/break-owner'
    run = out / args.label
    run.mkdir(exist_ok=False)
    manifest = json.loads((out / 'manifest.json').read_text())
    for name, expected in [('BRKOWN.EXE', manifest['binary_sha256']),
                           ('BRKCHLD.COM', manifest['child_sha256'])]:
        data = (out / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected
        (run / name).write_bytes(data)
    for name, expected in manifest['sources'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    (run / 'CHECK.BAT').write_text(
        '@echo off\nBRKOWN.EXE >OUTPUT.TXT\nif errorlevel 1 goto bad\n'
        'echo PASS>RESULT.TXT\ngoto done\n:bad\necho FAIL>RESULT.TXT\n:done\nexit\n')
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 3000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
mount c "{run}"
c:
CHECK.BAT
exit
'''
    (run / 'dosbox.conf').write_text(config)
    with (run / 'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(run / 'dosbox.conf')],
                       env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                       stdout=log, stderr=log, check=True, timeout=45)
    output = (run / 'OUTPUT.TXT').read_text()
    assert (run / 'RESULT.TXT').read_text().strip() == 'PASS', output
    match = re.fullmatch(r'BREAK OWNER checks=(\d+) failures=0 children=4\s*', output)
    assert match, output
    # Catch producer/source changes during execution before publishing acceptance.
    for name, expected in manifest['sources'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    receipt = dict(passed=True, label=args.label, checks=int(match[1]), children=4,
                   binary_sha256=manifest['binary_sha256'], child_sha256=manifest['child_sha256'],
                   sources=manifest['sources'], original_inputs=[],
                   scope='Separate source-linked owner diagnostic under DOSBox-X 8086 with real DOS EXEC. '
                         'Controlled foreign-PSP token and vector corruption; no physical modem, '
                         'asynchronous fault, full PROGRAM binding or BBS session proof.')
    (run / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(f"{match[1]} guarded break-owner checks and four real DOS children passed ({args.label})")

if __name__ == '__main__':
    main()
