#!/usr/bin/env python3
"""Isolate experimental ASPECT overlay startup using DOS CRT spawn, not ASIO."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
from build_path_session import ROOT,sha
from check_aspect_runner import HARNESS
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--child-dir',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();child=a.child_dir.resolve();out=a.output.resolve()
 assert child.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads((child/'manifest.json').read_text())
 assert manifest['original_inputs']==[] and sha(child/'ASPECT.EXE')==manifest['binary_sha256']
 out.mkdir();(out/'other').mkdir();shutil.copyfile(child/'ASPECT.EXE',out/'ASPECT.EXE')
 # Absolute executable path is intentional: repeat with a different current drive.
 c=HARNESS.replace('"ASPECT.EXE"','"C:\\ASPECT.EXE"')
 # C string literals require two backslashes in the emitted source.
 c=c.replace('C:\\ASPECT.EXE','C:\\\\ASPECT.EXE')
 (out/'HELLO.ASX').write_bytes(compile_source('proc main\nmessage "BOOT OK"\nendproc\n'))
 (out/'other'/'HELLO.ASX').write_bytes((out/'HELLO.ASX').read_bytes())
 c+=' run("HELP","/?",0,0,0);run("ARGS",0,0,64,0);run("HELLO","HELLO.ASX",0,0,0);\n'
 c+=' printf("BOOTSTRAP cases=%u checks=%u failures=%u\\n",cases,checks,failed);return failed?1:0;}\n'
 (out/'probe.c').write_text(c)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k4096','-fe=PROBE.EXE','probe.c'],cwd=out,check=True)
 results={}
 for drive in ('C','D'):
  wd=out if drive=='C' else out/'other'
  conf=out/('dosbox-'+drive+'.conf')
  conf.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\nfpu=false\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nmount d "'+str(out/'other')+'"\n'+drive+':\nC:\\PROBE.EXE >RESULT.TXT\nexit\n')
  with (out/('dosbox-'+drive+'.log')).open('w') as log:
   subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(conf)],cwd=out,
    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=40,check=True)
  results[drive]=dict(summary=(wd/'RESULT.TXT').read_text(),
   outputs={name:(wd/name).read_bytes().hex() for name in ('HELP.OUT','HELP.ERR','ARGS.OUT','ARGS.ERR','HELLO.OUT','HELLO.ERR')})
 help_text=b'ASPECT script.ASX [instruction-budget:1..65535] [/S1:0003:03:N]\r\nPCPLUS_TXWAIT=1..3600 sets transmit stall seconds (default30).\r\n'
 usage=b'Usage: ASPECT script.ASX [instruction-budget:1..65535] [/S1:0003:03:N]\r\n'
 expected={'HELP.OUT':help_text.hex(),'HELP.ERR':'','ARGS.OUT':'','ARGS.ERR':usage.hex(),'HELLO.OUT':b'BOOT OK\r\n'.hex(),'HELLO.ERR':''}
 passed=all(r['summary'].endswith('BOOTSTRAP cases=3 checks=15 failures=0\n') and r['outputs']==expected for r in results.values())
 result=dict(passed=bool(passed),child_sha256=sha(out/'ASPECT.EXE'),manifest_sha256=sha(child/'manifest.json'),
  checker_sha256=sha(Path(__file__)),harness_sha256=sha(out/'probe.c'),results=results,original_inputs=[],
  scope='8086 DOS CRT-spawn startup and redirected CLI output from two current drives. No terminal handoff, GET, Help overlay eviction or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
 return 0 if passed else 1


if __name__=='__main__':raise SystemExit(main())
