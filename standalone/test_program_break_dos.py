#!/usr/bin/env python3
"""Run linked reconstructed INT1B/23 and break routines in actual8086 DOS."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import argparse
import datetime

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--label',default='dos-'+datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
args=parser.parse_args();assert args.label.replace('-','').replace('_','').isalnum()
OUT=ROOT/'build/program-break';RUN=OUT/args.label;RUN.mkdir(exist_ok=False)
binary=(OUT/'BRKVEC.EXE').read_bytes();(RUN/'BRKVEC.EXE').write_bytes(binary)
(RUN/'RESULT.TXT').unlink(missing_ok=True)
(RUN/'CHECK.BAT').write_text('@echo off\nBRKVEC.EXE >OUTPUT.TXT\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto done\n:bad\necho FAIL>RESULT.TXT\n:done\nexit\n')
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
mount c "{RUN}"
c:
CHECK.BAT
exit
'''
(RUN/'dosbox.conf').write_text(config)
with (RUN/'dosbox.log').open('w') as log:
    subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(RUN/'dosbox.conf')],
        env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
assert (RUN/'RESULT.TXT').read_text().strip()=='PASS'
assert b'BREAK component returned' in (RUN/'OUTPUT.TXT').read_bytes()
result=dict(passed=True,cases=16,label=args.label,binary_sha256=hashlib.sha256(binary).hexdigest(),
    checks=['Four flags crossed with real initial and child break0/1 settings',
        'Actual DOS21 gets/sets both vectors, installed offsets/CS verified',
        'Actual INT1B/INT23 IRET preserves CPU flags',
        'Saved vectors restored after simulated child vector replacement',
        'Original conditional break policy checked; native callee stack cleanup and DS=SS checked',
        'Independent original vectors and break state restored before exit'],
    scope='Source-linked recovered native code under DOSBox-X8086; software interrupts and simulated child changes, no child EXEC, physical keyboard or production owner binding.')
(OUT/'dos-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print('16 actual8086 DOS control-break/vector cases passed')
