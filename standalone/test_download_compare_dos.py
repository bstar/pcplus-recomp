#!/usr/bin/env python3
"""Real8086 comparison/file-owner code with explicit deterministic FS faults."""
import argparse,hashlib,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 src=ROOT/'src/transfer';sources=[src/'download_file.c',src/'download_compare.c',ROOT/'standalone/download_compare_fault.c']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k8192','-i='+str(src),'-fe=CHECK.EXE',*map(str,sources)],cwd=out,check=True)
 cfg=f'''[sdl]
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
CHECK > RESULT.TXT
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
 (out/'dosbox.conf').write_text(cfg)
 with (out/'dosbox.log').open('w') as log:
  r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=45)
 text=(out/'RESULT.TXT').read_text();count=int(re.search(r'cases=(\d+) failures=0',text)[1])
 assert r.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists() and text.count('PASS ')==count and count>=60,text
 sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
 result=dict(passed=True,case_count=count,cases=text.splitlines(),binary_sha256=sha(out/'CHECK.EXE'),original_inputs=[],
  inputs={str(q.relative_to(ROOT)):sha(q) for q in [*sources,src/'download_compare.h',src/'download_file.h',src/'download_fs.h',Path(__file__).resolve()]},scope=__doc__,
  limitations=['DOS filesystem callbacks are fault fixtures; real DOS read/seek is covered separately by session workflows.','No UART/audio/BBS/physical acceptance.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,case_count=count)))
if __name__=='__main__':main()
