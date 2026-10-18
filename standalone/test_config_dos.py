#!/usr/bin/env python3
"""Run real DOS-file and fault-injected backend tests on synthetic files only."""
import fcntl,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/config-dos';run=out/'run';run.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for name in ['NORMAL.OK','FAULT.OK','FAIL.TXT','NORMAL.TXT','FAULT.TXT','ROUND.PRM','READONLY.PRM']:
   p=run/name
   if p.exists():p.chmod(0o600);p.unlink()
  payload=bytes((i*17+3)%256 for i in range(1264))
  fixtures={'SHORT.PRM':payload[:17],'LONG.PRM':payload+b'X','EMPTY.PRM':b''}
  for name,data in fixtures.items():(run/name).write_bytes(data)
  for name in ['CONFIG.EXE','CFGFAULT.EXE']:shutil.copy2(out/name,run/name)
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
mount c "{run}"
c:
CONFIG > NORMAL.TXT
if errorlevel 1 goto failed
echo PASS>NORMAL.OK
CFGFAULT > FAULT.TXT
if errorlevel 1 goto failed
echo PASS>FAULT.OK
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
  (out/'dosbox.conf').write_text(config)
  with (out/'dosbox.log').open('w') as log:
   p=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
  logs={name:(run/name).read_text(errors='replace') if (run/name).exists() else '' for name in ['NORMAL.TXT','FAULT.TXT']}
  passed=p.returncode==0 and (run/'NORMAL.OK').exists() and (run/'FAULT.OK').exists() and not (run/'FAIL.TXT').exists()
  passed=passed and (run/'ROUND.PRM').read_bytes()==payload and all((run/name).read_bytes()==data for name,data in fixtures.items())
  result={'passed':passed,'returncode':p.returncode,'binary_sha256':hashlib.sha256((out/'CONFIG.EXE').read_bytes()).hexdigest(),'fault_binary_sha256':hashlib.sha256((out/'CFGFAULT.EXE').read_bytes()).hexdigest(),'normal_cases':logs['NORMAL.TXT'].splitlines(),'fault_cases':logs['FAULT.TXT'].splitlines(),'scope':'Source-owned DOS backend; real synthetic filesystem and separately injected DOS service errors. No user config or original executable used.'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
  return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
