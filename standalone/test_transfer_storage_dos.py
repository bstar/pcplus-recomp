#!/usr/bin/env python3
"""One native receiver's11 binary blocks to actual staged DOS file storage."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/transfer-storage';out.mkdir(parents=True,exist_ok=True)
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  run=out/'run'
  if run.exists():shutil.rmtree(run)
  run.mkdir()
  expected=b''.join(bytes((i+17*block)%256 for i in range(1024)) for block in range(1,12))
  cases=[]
  for mode in ('N','M','W','C','X','T'):
   case=run/mode;case.mkdir();shutil.copy2(out/'TRANSFER.EXE',case/'TRANSFER.EXE')
   config=f'''[sdl]
output=surface
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
mount c "{case}"
c:
TRANSFER {mode} > RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
   (out/'dosbox.conf').write_text(config)
   with (out/('dosbox-'+mode+'.log')).open('w') as log:
    process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
   text=(case/'RESULT.TXT').read_text(errors='replace') if (case/'RESULT.TXT').exists() else ''
   checks={'DOS_expected_exit':process.returncode==0 and (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists(),'case_reported_pass':'PASS ' in text}
   if mode in ('N','M'):
    size=11136 if mode=='M' else 11264
    payload=(b''.join(bytes((i+17*block)%256 for i in range(128)) for block in range(1,80))+bytes((i+17*80)%256 for i in range(1024))) if mode=='M' else expected
    checks.update(native_owner_and_sealed_storage_success=f'OWNER 1 STATE 2 FIRST 0 BYTES {size}' in text,native_periodic_and_final_binary_file_exact=(case/'OUTPUT.BIN').is_file() and (case/'OUTPUT.BIN').read_bytes()==payload,stage_name_removed_only_after_install=not (case/'PART.TMP').exists())
   else:
    expected_state={'W':'OWNER 1 STATE 5 FIRST 7 BYTES 10257','C':'OWNER 1 STATE 6 FIRST 8 BYTES 11264','X':'OWNER 0 STATE 2 FIRST 0 BYTES 1024','T':'OWNER 0 STATE 1 FIRST 0 BYTES 0'}
    checks['native_return_and_storage_failure_state']=expected_state[mode] in text
    checks['failed_or_canceled_file_never_installed']=not (case/'OUTPUT.BIN').exists()
    if mode=='C':checks['uncertain_close_stage_preserved_exact']=(case/'PART.TMP').is_file() and (case/'PART.TMP').read_bytes()==expected
    else:checks['resolved_partial_stage_removed']=not (case/'PART.TMP').exists()
   cases.append({'mode':mode,'passed':all(checks.values()),'checks':checks,'transcript':text})
  checks={'all_native_owner_storage_cases':all(c['passed'] for c in cases)}
  result={'passed':all(checks.values()),'checks':checks,'binary_sha256':hashlib.sha256((out/'TRANSFER.EXE').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((run/'N/OUTPUT.BIN').read_bytes()).hexdigest() if (run/'N/OUTPUT.BIN').exists() else None,'cases':cases,'scope':'One actual native session owner with realDOS append/seal/install:11x1024 and79x128+1024 binary cases; injected finalshortwrite/closeerror, doubleCAN and timeout cleanup. Native10240-byte periodicflush and finaltail execute; independentfirsterror gate prevents failed installation. Controlled memory UART/time/UI; no live UART/BBS/terminal UI/physicalmodem or ACK-after-commit claim.'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
