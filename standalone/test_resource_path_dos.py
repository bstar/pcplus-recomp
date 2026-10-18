#!/usr/bin/env python3
"""Compile and execute generic resource-path argument/extent checks in DOS."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'build/resource-path'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = [ROOT/'src/config/resource_path.c', ROOT/'standalone/resource_path_host.c']
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-k8192',
                    '-i='+str(ROOT/'src/config'), '-fe=RESOURCE.EXE', *map(str, sources)], cwd=OUT, check=True)
    for name in ['PASS.TXT', 'FAIL.TXT', 'CHECKS.TXT']:
        (OUT/name).unlink(missing_ok=True)
    config = f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 10000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{OUT}"
c:
RESOURCE >CHECKS.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
'''
    (OUT/'dosbox.conf').write_text(config)
    with (OUT/'dosbox.log').open('w') as log:
        subprocess.run(['dosbox-x', '-fastlaunch', '-nogui', '-conf', str(OUT/'dosbox.conf')],
                       env=dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy'),
                       stdout=log, stderr=log, check=True, timeout=30)
    text = (OUT/'CHECKS.TXT').read_text().strip()
    assert (OUT/'PASS.TXT').exists() and text.startswith('RESOURCE PATH PASS'), text
    inputs = sources + [ROOT/'src/config/resource_path.h', Path(__file__).resolve()]
    result = dict(passed=True, binary_sha256=hashlib.sha256((OUT/'RESOURCE.EXE').read_bytes()).hexdigest(),
                  log=text, sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                  scope='Production generic resolver compiled unchanged for8086 and run in DOSBox-X. Synthetic PSP/environment in real DOS-allocated blocks. Directory concatenation, first duplicate, case, unterminated strings, exact63-byte limit, argument/wrap/alias guards and unchanged output on failure. Terminal-linked and inherited-environment tests remain separate.')
    (OUT/'checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print(text)


if __name__ == '__main__':
    main()
