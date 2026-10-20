#!/usr/bin/env python3
"""Actual DOS keyboard/mouse composition, child handoff and driver restoration."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid
from build_mouse_keyboard import ROOT, OUT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default='owner-' + uuid.uuid4().hex)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    folder = OUT / 'runs' / args.label
    folder.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((OUT / 'manifest.json').read_text())
    assert all(sha(ROOT / name) == digest for name, digest in manifest['sources'].items())
    for name, digest in {'MOUSEKEY.EXE': manifest['binary_sha256'], **manifest['children']}.items():
        assert sha(OUT / name) == digest
        shutil.copyfile(OUT / name, folder / name)
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
MOUSEKEY >CHECKS.TXT
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
                                    cwd=folder, env=env, stdout=log, stderr=log, timeout=25)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = -1
    text = (folder / 'CHECKS.TXT').read_text(errors='replace') if (folder / 'CHECKS.TXT').exists() else ''
    summary = re.search(r'^MOUSEKEY checks=(\d+) failures=(\d+) driver_bytes=(\d+)$', text, re.M)
    checks = dict(emulator_exit=code == 0, DOS_exit=(folder / 'PASS.TXT').exists() and not (folder / 'FAIL.TXT').exists(),
                  actual_self_check=bool(summary) and int(summary[1]) >= 40 and int(summary[2]) == 0 and 0 < int(summary[3]) < 65504 and 'FAIL ' not in text,
                  actual_child_marker=(folder / 'CHILD.OK').is_file() and (folder / 'CHILD.OK').read_bytes() == b'MOUSE CHILD\r\n',
                  products_unchanged=all(sha(folder / name) == digest for name, digest in
                      {'MOUSEKEY.EXE': manifest['binary_sha256'], **manifest['children']}.items()),
                  sources_unchanged=all(sha(ROOT / name) == digest for name, digest in manifest['sources'].items()))
    report = dict(passed=all(checks.values()), checks=checks, actual_DOS_assertions=int(summary[1]) if summary else 0,
                  actual_driver_state_bytes=int(summary[3]) if summary else 0,
                  binary_sha256=manifest['binary_sha256'], checker_sha256=sha(Path(__file__)),
                  artifacts={p.name: sha(p) for p in folder.iterdir() if p.is_file()},
                  scope='Actual8086 DOS native mouse-to-keyboard consumption and BIOS priority/fallback, typed PRM admission, opaque INT33 storage and real CRT DOS children, changed-vector quarantine and repaired close with exact driver/native-state restoration. Direct source-owned mouse events; no physical-input or production ASPECT publication claim.')
    (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Mouse/keyboard DOS:', 'PASS' if report['passed'] else checks, folder)
    if not report['passed']:
        print(text)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
