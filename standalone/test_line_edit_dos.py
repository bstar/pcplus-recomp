#!/usr/bin/env python3
"""Run source-only classifier vectors and recovered emitter in actual DOSBox-X."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/line-edit';RUN=OUT/'dos';RUN.mkdir(exist_ok=True)
binary=(OUT/'LINES.EXE').read_bytes();(RUN/'LINES.EXE').write_bytes(binary)
(RUN/'CHECK.BAT').write_text('@echo off\nLINES\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto end\n:bad\necho FAIL>RESULT.TXT\n:end\nexit\n')
(RUN/'RESULT.TXT').unlink(missing_ok=True)
conf=f'''[sdl]
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
(RUN/'dosbox.conf').write_text(conf)
with (RUN/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(RUN/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=20)
assert (RUN/'RESULT.TXT').read_text().strip()=='PASS'
(OUT/'dos-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256(binary).hexdigest(),'checks':['actual recovered insert-line shifts row5 down and clears it','actual recovered delete-line shifts row5 up and clears lastrow','outside rectangle unchanged','wait-control-N terminates using explicit UART14 fixture'],'scope':'Actual DOSBox-X8086 video; wait-loop UART/keyboard are declared controlled fixtures; protected attribute repair unresolved.'},indent=2)+'\n')
print('DOSBox-X8086 actual insert/delete-line video and controlled wait loop passed')
