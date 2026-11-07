#!/usr/bin/env python3
"""Run source-only Line/Port popup session transactions in actual DOSBox-X."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/line-port-session';RUN=OUT/'dos';RUN.mkdir(exist_ok=True)
binary=(OUT/'SESSION.EXE').read_bytes();(RUN/'SESSION.EXE').write_bytes(binary)
(RUN/'CHECK.BAT').write_text('@echo off\nSESSION >CHECK.LOG\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto end\n:bad\necho FAIL>RESULT.TXT\n:end\nexit\n')
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
report=(RUN/'CHECK.LOG').read_text()
assert 'PASS ' in report and 'FAIL' not in report,report
checks=int(report.split('PASS ')[1].split()[0])
assert checks==71
listing=(OUT/'SESSION.map').read_text()
import re
segment=int(re.search(r'^([0-9a-f]+):[0-9a-f]+\s+_line_port_session_begin$',listing,re.M|re.I)[1],16)
assert segment*16>=65536
raw=(RUN/'POPUP.BIN').read_bytes()
cells=[r*80+c for r in range(2,20)for c in range(18,77)]+list(range(24*80,25*80))
footprint=b''.join(raw[at*2:at*2+2]for at in cells)
assert hashlib.sha256(footprint).hexdigest()=='7ca6d68fb5c838c388fa92ae0d0f461519d2c9f7040c51e980fa473a64964391'
(OUT/'dos-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256(binary).hexdigest(),'checks':checks,'separate_bank_segment':segment,'popup_cells':len(cells),'popup_sha256':hashlib.sha256(footprint).hexdigest(),'report':report.strip(),'scope':'Actual DOSBox-X8086 separate far-bank selector/session/renderer. Save and apply results are authored inputs; no actual file-settings or UART operations.'},indent=2)+'\n')
print('DOSBox-X8086:',report.strip())
