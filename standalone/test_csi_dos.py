#!/usr/bin/env python3
"""Run the combined source-only CSI executable's self-checks under actual DOSBox-X DOS."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    output=ROOT/'build/csi-dos'
    output.mkdir(parents=True,exist_ok=True)
    with (output/'.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name in ['PASS.TXT','FAIL.TXT']:
            (output/name).unlink(missing_ok=True)
        binary=ROOT/'build/csi/CSI.EXE'
        digest=hashlib.sha256(binary.read_bytes()).hexdigest()
        config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
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
mount c "{binary.parent}"
mount d "{output}"
c:
CSI
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto done
:failed
echo FAIL>D:\\FAIL.TXT
:done
exit
'''
        (output/'dosbox.conf').write_text(config)
        env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
        with (output/'dosbox.log').open('w') as log:
            try:
                process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(output/'dosbox.conf')],
                    cwd=output,env=env,stdout=log,stderr=log,timeout=15)
                code=process.returncode
            except subprocess.TimeoutExpired:
                code=-1
        passed=code==0 and (output/'PASS.TXT').exists() and not (output/'FAIL.TXT').exists()
        result={'passed':passed,'returncode':code,'binary_sha256':digest,
                'scope':'Combined recovered escape/parser/dispatcher/attributes/cursor self-test plus parser-driven CSI2J BIOS erase of all 2000 text cells in DOSBox-X; memory input and no modem or ordinary text renderer.'}
        (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2),flush=True)
        return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())
