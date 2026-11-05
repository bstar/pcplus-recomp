#!/usr/bin/env python3
"""Exercise private-DTA continuation against an independent foreign DOS search."""
import argparse,datetime,json,os,re,shutil,subprocess
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['program','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.program.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);drive=out/'drive';drive.mkdir();shutil.copyfile(binary,drive/'FIND.EXE')
 stamp=datetime.datetime(1993,7,9,14,32,10).timestamp()
 for folder in ['FILES','FOREIGN']:
  target=drive/folder;target.mkdir()
  for i in range(3):
   f=target/('F%02d.TXT'%i);f.write_bytes(b'X'*(i+1));os.utime(f,(stamp,stamp))
 (drive/'FILES/SUB').mkdir()
 config=out/'dosbox.conf';config.write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
fpu=false
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{drive}"
c:
FIND > RESULT.TXT
if errorlevel 1 echo FAIL>EXIT.TXT
if not errorlevel 1 echo PASS>EXIT.TXT
exit
''')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 text=(drive/'RESULT.TXT').read_text();match=re.search(r'FIND checks=(\d+) failures=0',text)
 assert match and 'FAIL' not in text and (drive/'EXIT.TXT').read_text().strip()=='PASS',text
 assert sha(drive/'FIND.EXE')==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 r=dict(passed=True,checks=int(match[1]),binary_sha256=sha(binary),cpu='8086',FPU=False,manifest_sha256=sha(binary.with_name('manifest.json')),
  sources={**manifest['sources'],'standalone/test_find_owner_dos.py':sha(Path(__file__))},original_inputs=[],
  artifacts={str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file()},
  scope=__doc__+' Actual DOS2F/1A/4E/4F, independent installed foreign DTA and continuation, exact names/attributes/size/time/date, failed-path/missing/invalid arguments, active-owner refusal, error-output preservation and100close/reopen cycles. Banked state stays outside DGROUP. No listing UI, UART, DOS6.22 or physical acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS private DTA:',r['checks'],'actual DOS checks')
if __name__=='__main__':main()
