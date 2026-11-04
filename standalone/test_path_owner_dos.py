#!/usr/bin/env python3
"""Exercise real DOS path/drive changes, native quirks and guarded rollback."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--program',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.program.resolve();out=a.output.resolve()
 assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);c=out/'c';d=out/'d';c.mkdir();d.mkdir()
 for path in [c/'ONE/SUB',d/'TWO/SUB']:path.mkdir(parents=True)
 shutil.copyfile(binary,c/'PATH.EXE')
 config=out/'dosbox.conf';config.write_text(f'''[sdl]
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
mount c "{c}"
mount d "{d}"
c:
C:\\PATH.EXE >C:\\REPORT.TXT
if errorlevel 1 goto failed
echo PASS>C:\\PASS.TXT
goto done
:failed
echo FAIL>C:\\FAIL.TXT
:done
cd>C:\\FINALCD.TXT
exit
''')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=out,
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 report=(c/'REPORT.TXT').read_text();match=re.fullmatch(r'PATHOWNER checks=(\d+) failures=0\s*',report)
 checks={'native_exit':(c/'PASS.TXT').exists() and not (c/'FAIL.TXT').exists(),
  'all_DOS_assertions':bool(match) and int(match[1])==61,
  'final_default_drive_and_directory':(c/'FINALCD.TXT').read_text().strip().upper()=='C:\\',
  'unchanged_program':sha(c/'PATH.EXE')==sha(binary),
  'sources_unchanged':all(sha(ROOT/n)==h for n,h in manifest['sources'].items())}
 r={'passed':all(checks.values()),'checks':checks,'assertions':int(match[1]) if match else 0,
  'program_sha256':sha(binary),'report':report,'sources':manifest['sources'],
  'observer_sha256':sha(Path(__file__)),'scope':__doc__+' CPU8086; test-owned C/D and unavailable Y. Two explicit test-only verification/rollback kernel-boundary faults. No original AltF7 UI, application ownership or physical acceptance.'}
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));return 0 if r['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
