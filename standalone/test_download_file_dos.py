#!/usr/bin/env python3
"""Real DOS streaming install plus executable fault-boundary regressions."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/download-file';out.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  run=out/'run'
  if run.exists():shutil.rmtree(run)
  run.mkdir()
  for name in ['DOWNLOAD.EXE','DLFAULT.EXE']:shutil.copy2(out/name,run/name)
  config=f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=8086
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
DOWNLOAD > NORMAL.TXT
if errorlevel 1 goto failed
echo PASS>NORMAL.OK
DLFAULT > FAULT.TXT
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
   process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
  logs={name:(run/name).read_text(errors='replace') if (run/name).exists() else '' for name in ['NORMAL.TXT','FAULT.TXT']}
  block=bytes((i*37+19)%256 for i in range(32768))
  checks={'DOS_normal_and_fault_exit':process.returncode==0 and all((run/name).exists() for name in ['NORMAL.OK','FAULT.OK']) and not (run/'FAIL.TXT').exists(),
   'normal_cases':logs['NORMAL.TXT'].count('PASS ')>=15 and 'FAIL ' not in logs['NORMAL.TXT'],
   'fault_cases':logs['FAULT.TXT'].count('PASS ')>=30 and 'FAIL ' not in logs['FAULT.TXT'],
   'binary_output_cross64K_exact':(run/'RESULT.BIN').is_file() and (run/'RESULT.BIN').read_bytes()==block*2+block[:137],
   'nested_absolute_file_exact':(run/'DATA/NESTED.BIN').is_file() and (run/'DATA/NESTED.BIN').read_bytes()==block[:257],
   'drive_relative_file_exact':(run/'REL.BIN').is_file() and (run/'REL.BIN').read_bytes()==block[:3],
   'empty_file_exact':(run/'EMPTY.BIN').is_file() and (run/'EMPTY.BIN').read_bytes()==b'',
   'foreign_stage_preserved':(run/'KEEP.TMP').is_file() and (run/'KEEP.TMP').read_bytes()==b'preexisting stage',
   'concurrent_destination_preserved':(run/'RACE.BIN').is_file() and (run/'RACE.BIN').read_bytes()==b'competing target',
   'owned_partial_stage_names_removed':not any((run/name).exists() for name in ['STAGE.TMP','EMPTY.TMP','CANCEL.TMP','CANCEL.BIN','RACE.TMP','NEW.BIN'])}
  result={'passed':all(checks.values()),'checks':checks,'normal_cases':logs['NORMAL.TXT'].splitlines(),'fault_cases':logs['FAULT.TXT'].splitlines(),'binaries':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ['DOWNLOAD.EXE','DLFAULT.EXE']},'scope':'Actual DOSBox-X8086 compiled maintained storage boundary: binary files beyond64K, exclusive stage/rename, close-before-install, cancellation; deterministic compiled C fault filesystem for disk-full short writes, errors, ambiguousclose, races and recovery. No nativeCRT equivalence, liveUART/session, physicaldisk powerloss or protocol claim.'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
