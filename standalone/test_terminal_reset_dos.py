#!/usr/bin/env python3
"""Run source-only recovered character editing in actual DOSBox-X."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal-reset';RUN=OUT/'dos';RUN.mkdir(exist_ok=True)
binary=(OUT/'RESET.EXE').read_bytes();(RUN/'RESET.EXE').write_bytes(binary)
(RUN/'CHECK.BAT').write_text('@echo off\nRESET\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto end\n:bad\necho FAIL>RESULT.TXT\n:end\nexit\n')
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
(OUT/'dos-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256(binary).hexdigest(),'checks':['native terminal_reset(0) returns on stable80-column/status-hidden configuration','real video rectangle cleared and cursor homed','current attribute reset and default tabs generated'],'scope':'Actual DOSBox-X8086 soft-reset path only. Full profile reset still requires explicit KEY loader; no no-op dependency replacement.'},indent=2)+'\n')
print('DOSBox-X8086 native soft reset stable geometry/status-hidden passed')
