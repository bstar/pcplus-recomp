#!/usr/bin/env python3
"""Actual DOS verifies assembly-owned startup and C configuration call/return ABI."""
from pathlib import Path
import fcntl,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
 out=ROOT/'build/config-abi'
 with (out/'.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for name in ['PASS.TXT','FAIL.TXT','ABI.PRM']:(out/name).unlink(missing_ok=True)
  config=f'''[sdl]
output=surface
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{out}"
c:
ABI
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
''';(out/'dosbox.conf').write_text(config)
  with (out/'dosbox.log').open('w') as log:
   p=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
  checks={'assembly_call_return_checks':p.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),'exact_synthetic_save_load':(out/'ABI.PRM').exists() and (out/'ABI.PRM').read_bytes()==b'\xa5'*1264}
  result={'passed':all(checks.values()),'checks':checks,'binary_sha256':hashlib.sha256((out/'ABI.EXE').read_bytes()).hexdigest(),'scope':'Assembly-owned DOS startup, actual near-C load/save/replacement validation, unsigned16 AX status, preservation/caller cleanup and synthetic file roundtrip. No original or user files.'}
  (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
