#!/usr/bin/env python3
"""Run source-only classifier vectors and recovered emitter in actual DOSBox-X."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/keyboard-mapping';RUN=OUT/'dos';RUN.mkdir(exist_ok=True)
binary=(OUT/'MAPPING.EXE').read_bytes();(RUN/'MAPPING.EXE').write_bytes(binary)
(RUN/'CHECK.BAT').write_text('@echo off\nMAPPING\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto end\n:bad\necho FAIL>RESULT.TXT\n:end\nexit\n')
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
(OUT/'dos-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256(binary).hexdigest(),'classifier_vectors':83,'recovered_emitter':'A FF B stored produces A NUL B through explicitly declared recording UART fixture','scope':'Actual DOSBox-X8086 executable; original dispatcher local UI routines trap and are not exercised by diagnostic startup. No actual UART/BBS in this test.'},indent=2)+'\n')
print('DOSBox-X 8086: 83 raw classifier vectors (all79slots) and actual recovered FF-to-NUL emitter passed')
