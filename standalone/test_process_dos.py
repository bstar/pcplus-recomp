#!/usr/bin/env python3
"""Execute only the source-owned parent/child, on private synthetic DOS media."""
import hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/process'
 for name in ('PASS.TXT','FAIL.TXT','CHILD.OUT','ENV.OUT','FCBS.OUT'):(out/name).unlink(missing_ok=True)
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{out}"
c:
set PCPLUS_EXEC_TEST=SYNTHETIC-ENV
PROCESS
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:
  run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
 tail=b' ALPHA.TXT BETA.DAT';fcbs=(out/'FCBS.OUT').read_bytes() if (out/'FCBS.OUT').exists() else b''
 checks={'actual_DOS_parent_checks':run.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),'child_exact_tail':(out/'CHILD.OUT').exists() and (out/'CHILD.OUT').read_bytes()==bytes([len(tail)])+tail+b'\r','child_environment_inherited':(out/'ENV.OUT').exists() and (out/'ENV.OUT').read_bytes()==b'SYNTHETIC-ENV','child_actual_FCB_parse':len(fcbs)==32 and fcbs[1:12]==b'ALPHA   TXT' and fcbs[17:28]==b'BETA    DAT'}
 proof={'passed':all(checks.values()),'checks':checks,'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'PROCESS.EXE',out/'CHILD.COM')},'scope':'Actual DOS8086 parent memory shrink/MCB, repeated successful EXEC with exit37, inherited synthetic environment, DOSFCBs/tails, missing child, invalid input, real resize error8 and subsequent recovery. No user program or live UART handoff.'}
 (out/'dos-results.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2));return 0 if proof['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
