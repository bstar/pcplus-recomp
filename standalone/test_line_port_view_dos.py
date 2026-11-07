#!/usr/bin/env python3
"""Run source-only Line/Port popup rendering in actual DOSBox-X."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/line-port-view';RUN=OUT/'dos';RUN.mkdir(exist_ok=True)
binary=(OUT/'VIEW.EXE').read_bytes();(RUN/'VIEW.EXE').write_bytes(binary)
(RUN/'CHECK.BAT').write_text('@echo off\nVIEW\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto end\n:bad\necho FAIL>RESULT.TXT\n:end\nexit\n')
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
for index in range(3):
 raw=(RUN/f'VIEW{index}.BIN').read_bytes()
 assert len(raw)==4000
 # All cells outside the declared popup/footer footprint retain the sentinel.
 for at in range(2000):
  row,column=divmod(at,80)
  if not (2<=row<=19 and 18<=column<=76) and row!=24:
   assert raw[at*2:at*2+2]==b'X\x5a',(index,row,column)
(OUT/'dos-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256(binary).hexdigest(),'frames':3,'cells_per_frame':2000,'scope':'Actual DOSBox-X8086 maintained renderer and invalid-input checks; no original or UART input.'},indent=2)+'\n')
print('DOSBox-X 8086: popup renderer produced three bounded frames; invalid inputs leave frame unchanged')
