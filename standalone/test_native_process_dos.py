#!/usr/bin/env python3
"""Execute owned native-process diagnostics under 8086 DOS; retain each attempt."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid

from build_native_process import ROOT,OUT,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',default='run-'+uuid.uuid4().hex)
    parser.add_argument('--namespace',action='store_true')
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    run=OUT/'runs'/args.label;run.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((OUT/'manifest.json').read_text())
    shutil.copyfile(OUT/'manifest.json',run/'manifest.json')
    # Preserve exact authored sources when a later correction needs another run.
    for p,h in manifest['sources'].items():
        assert sha(ROOT/p)==h,p
        target=run/'sources'/p;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/p,target)
    executable='NAMES.EXE' if args.namespace else 'NATIVE.EXE'
    for name in [executable,*manifest['children']]:shutil.copyfile(OUT/name,run/name)
    (run/'OWNED.BAT').write_bytes(b'@echo off\r\necho BATCHPASS>BATCH.OUT\r\n')
    (run/'PCPTEST.BAT').write_text('@echo off\n'+executable+' >CHECKS.TXT\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto done\n:bad\necho FAIL>RESULT.TXT\n:done\nexit\n')
    config=f'''[sdl]
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
PCPTEST.BAT
exit
'''
    (run/'dosbox.conf').write_text(config)
    timed_out=False
    with (run/'dosbox.log').open('w') as log:
        try:
            subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(run/'dosbox.conf')],
                env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),
                stdout=log,stderr=log,check=True,timeout=30)
        except subprocess.TimeoutExpired:
            timed_out=True
    text=(run/'CHECKS.TXT').read_text() if (run/'CHECKS.TXT').exists() else ''
    passed=not timed_out and (run/'RESULT.TXT').exists() and (run/'RESULT.TXT').read_text().strip()=='PASS'
    match=re.search(r'NATIVE PROCESS (\d+) checks (\d+) failures',text)
    passed=passed and bool(match) and int(match[2])==0
    record=dict(passed=passed,timed_out=timed_out,checks=int(match[1]) if match else 0,
        namespace=args.namespace,executable=executable,
        executable_sha256=sha(run/executable),manifest_sha256=sha(run/'manifest.json'),
        checker_sha256=sha(Path(__file__)),
        artifacts={p.name:sha(p) for p in run.iterdir() if p.is_file()},
        scope=manifest['scope']+' Actual DOSBox-X8086 and source-owned children; no physical UART or runtime publication.')
    (run/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    print(text.strip());print('PASS' if passed else 'FAIL')
    print(run)
    return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
