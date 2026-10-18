#!/usr/bin/env python3
"""Actual DOS read-only upload normal/error/fault checks with immutable sources."""
import hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 source=ROOT/'build/upload-file';out=ROOT/'build/upload-file-dos';out.mkdir(parents=True,exist_ok=True)
 originals={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in ['SAMPLE.BIN','EMPTY.BIN','UPLOAD.EXE','UPFAULT.EXE']}
 for n in ['PASS.TXT','FAIL.TXT']:(out/n).unlink(missing_ok=True)
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
mount c "{source}"
mount d "{out}"
c:
UPLOAD
if errorlevel 1 goto failed
UPFAULT
if errorlevel 1 goto failed
UPFAULT 9
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto done
:failed
echo FAIL>D:\\FAIL.TXT
:done
exit
''';(out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:
  result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),cwd=out,stdout=log,stderr=log,timeout=15)
 hashes={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in originals}
 checks={'DOS_normal_and_fault_programs_pass':result.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),'all_synthetic_source_files_and_binaries_unchanged':originals==hashes}
 proof={'passed':all(checks.values()),'checks':checks,'hashes':hashes,'scope':'ActualDOS8086 read-only physical open/seekEND/rewind/read70013binarybytes incl1Ah/EOF/close,emptyfile,missingpath/directory and immutable sources. Separate linked filesystem-fault driver tests open/seek/read/shortread/close errors, near bounds/alias and repeated ownership cleanup. No live sender/UART/wireEOT assertion.'}
 (out/'checks.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2));return 0 if proof['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
