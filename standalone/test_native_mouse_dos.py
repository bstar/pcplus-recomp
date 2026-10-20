#!/usr/bin/env python3
"""Exercise native mouse init and callback under DOSBox-X's real DOS driver."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid
from build_native_mouse import ROOT, OUT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default='mouse-' + uuid.uuid4().hex)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    folder = OUT / 'runs' / args.label
    folder.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((OUT / 'manifest.json').read_text())
    binary = OUT / 'MOUSE.EXE'
    assert sha(binary) == manifest['binary_sha256']
    assert all(sha(ROOT / name) == digest for name, digest in manifest['sources'].items())
    shutil.copyfile(binary, folder / 'MOUSE.EXE')
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
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
mount c "{folder}"
c:
MOUSE >CHECKS.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
    (folder / 'dosbox.conf').write_text(config)
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    with (folder / 'dosbox.log').open('w') as log:
        try:
            result = subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(folder / 'dosbox.conf')],
                                    cwd=folder, env=env, stdout=log, stderr=log, timeout=20)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = -1
    checks = dict(emulator_exit=code == 0, DOS_exit=(folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists(),
                  actual_self_check=(folder / 'CHECKS.TXT').is_file() and (folder / 'CHECKS.TXT').read_bytes() == b'PASS native mouse\r\n',
                  binary_unchanged=sha(folder / 'MOUSE.EXE') == manifest['binary_sha256'],
                  sources_unchanged=all(sha(ROOT / name) == digest for name, digest in manifest['sources'].items()))
    report = dict(passed=all(checks.values()), checks=checks, binary_sha256=manifest['binary_sha256'],
                  checker_sha256=sha(Path(__file__)),
                  artifacts={p.name: sha(p) for p in folder.iterdir() if p.is_file()},
                  scope='Actual8086 DOSBox DOS/INT33 init, callback registration and native far callback with foreign DS and a separate SS, pending-motion/buttons/disabled/reentry behavior, and callback retirement before exit. Motion events are direct source-owned callback calls, not physical input.')
    (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Native mouse DOS:', 'PASS' if report['passed'] else checks, folder)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
