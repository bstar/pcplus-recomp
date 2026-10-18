#!/usr/bin/env python3
"""Verify real DOS replacement and injected failures on synthetic test media."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/config-replace';out.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  run=out/'run'
  if run.exists():shutil.rmtree(run)
  run.mkdir()
  for name in ['REPLACE.EXE','REPFAULT.EXE']:shutil.copy2(out/name,run/name)
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
REPLACE > NORMAL.TXT
if errorlevel 1 goto failed
echo PASS>NORMAL.OK
REPFAULT > FAULT.TXT
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
   process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
  payload=bytes((i*29+5)%256 for i in range(1264));checks={}
  logs={name:(run/name).read_text(errors='replace') if (run/name).exists() else '' for name in ['NORMAL.TXT','FAULT.TXT']}
  checks['normal_and_fault_DOS_exit']=process.returncode==0 and all((run/name).exists() for name in ['NORMAL.OK','FAULT.OK']) and not (run/'FAIL.TXT').exists()
  checks['reported_cases_pass']=all('FAIL ' not in log for log in logs.values()) and logs['NORMAL.TXT'].count('PASS ')>=15 and logs['FAULT.TXT'].count('PASS ')>=23
  checks['both_targets_exact']=all((run/name).exists() and (run/name).read_bytes()==payload for name in ['TARGET.PRM','NEW.PRM'])
  checks['existing_recovery_files_unchanged']=(run/'CAND.TMP').read_bytes()==b'keep stage' and (run/'CAND.BAK').read_bytes()==b'keep backup'
  checks['rename_destination_preserved']=(run/'TO.TMP').read_bytes()==b'destination'
  checks['owned_scratch_removed']=not any((run/name).exists() for name in ['STAGE.TMP','BACKUP.BAK','FROM.TMP'])
  result={'passed':all(checks.values()),'checks':checks,'normal_cases':logs['NORMAL.TXT'].splitlines(),'fault_cases':logs['FAULT.TXT'].splitlines(),'binaries':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ['REPLACE.EXE','REPFAULT.EXE']},'scope':'Maintained staged DOS configuration replacement. Real synthetic filesystem plus state-based injected DOS failures/concurrent destination appearance; not physical disk power-loss or complete application settings integration.'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
