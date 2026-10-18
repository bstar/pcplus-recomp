#!/usr/bin/env python3
"""Run source-only classifier vectors and recovered emitter in actual DOSBox-X."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/program-exec';RUN=OUT/'dos';RUN.mkdir(exist_ok=True)
binary=(OUT/'EXECUTOR.EXE').read_bytes();(RUN/'EXECUTOR.EXE').write_bytes(binary)
(RUN/'CHILD.COM').write_bytes((OUT/'CHILD.COM').read_bytes());(RUN/'CHILD.OUT').unlink(missing_ok=True)
(RUN/'CHECK.BAT').write_text('@echo off\nEXECUTOR\nif errorlevel 1 goto bad\necho PASS>RESULT.TXT\ngoto end\n:bad\necho FAIL>RESULT.TXT\n:end\nexit\n')
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
assert (RUN/'CHILD.OUT').read_bytes()==bytes([9])+b' /Q SYNTH\r'
(OUT/'dos-results.json').write_text(json.dumps({'passed':True,'binary_sha256':hashlib.sha256(binary).hexdigest(),'checks':['Actual original6a22 4B00 DOSexec and4D childexit37','Child verifies its9byte commandtail+CR','Child verifies explicitLABVAR=OWNED environment','Child writes ownedCHILD.OUT proving it actually ran','Parent resumes with DS002e/0030 pair andexecactive restored','ActualDOS missingABSENT.COM reportsFFFF/errno2/DOSerror2 andreturns safely'],'scope':'Actual DOSBox-X8086 native recovered EXEC instructions; only source-owned synthetic CHILD.COM launched. Maintained diagnostic startup shrinks ownPSPblock. CRT heap/path/UI/serial gaps not exercised.'},indent=2)+'\n')
print('DOSBox-X8086 original EXEC core launched ownedCHILD.COM, tail/env/exit37 and parentresume passed')
