#!/usr/bin/env python3
"""Actual DOS COMSPEC/PATH policy with only source-owned diagnostic children."""
import argparse,hashlib,json,os,shutil,subprocess,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BIN=ROOT/'build/process'
def main():
 global BIN
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--banked',action='store_true');args=parser.parse_args()
 if args.banked:BIN=ROOT/'build/process-bank'
 cases=[]
 for name,settings,expected in [
  ('COMSPEC',['set COMSPEC=Z:\\COMMAND.COM','set PATH=Z:\\'],0),
  ('missing-COMSPEC-PATH',['set COMSPEC=','set PATH=D:\\MISSING;;Z:\\'],0),
  ('invalid-COMSPEC-fallback',['set COMSPEC=Z:\\ABSENT.COM','set PATH=Z:\\'],0),
  ('drive-relative-PATH',['set COMSPEC=','set PATH=Z:'],0),
  ('DOSBox-internal-processor',['set COMSPEC=','set PATH='],0),
 ]:
  out=ROOT/('build/program-process-bank-dos' if args.banked else 'build/program-process-dos')/name;out.mkdir(parents=True,exist_ok=True)
  for filename in ('PASS.TXT','FAIL.TXT','CHILD.OUT','FCBS.OUT','ENV.OUT','RESULT.OUT'):(out/filename).unlink(missing_ok=True)
  shutil.copy2(BIN/'CHILD.COM',out/'CHILD.COM')
  branch='if errorlevel 2 goto failed\nif errorlevel 1 goto expected\ngoto failed' if expected else 'if errorlevel 1 goto failed\ngoto expected'
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
mount c "{BIN}"
mount d "{out}"
d:
set PCPLUS_EXEC_TEST=SYNTHETIC-ENV
'''+ '\n'.join(settings)+f'''
C:\\PROGRAM
{branch}
:expected
echo PASS>PASS.TXT
goto done
:failed
echo FAIL>FAIL.TXT
:done
exit
'''
  (out/'dosbox.conf').write_text(config)
  with (out/'dosbox.log').open('w') as log:
   run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20)
  wanted=b' /Q SYNTH'
  checks={'expected_DOS_exit':run.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists()}
  if not expected:
   checks.update(command_processor_delivered_exact_child_arguments=(out/'CHILD.OUT').exists() and (out/'CHILD.OUT').read_bytes()==bytes([len(wanted)])+wanted+b'\r',child_environment=(out/'ENV.OUT').exists() and (out/'ENV.OUT').read_bytes()==b'SYNTHETIC-ENV')
  else:checks['no_child']=not (out/'CHILD.OUT').exists()
  raw=(out/'RESULT.OUT').read_bytes() if (out/'RESULT.OUT').exists() else b''
  checks['raw_command_processor_result']=len(raw)==8 and struct.unpack('<4H',raw)[:3]==(0,0,0)
  proof={'case':name,'passed':all(checks.values()),'checks':checks,'raw_result':list(struct.unpack('<4H',raw)) if len(raw)==8 else None};cases.append(proof);print(json.dumps(proof),flush=True)
 proof={'passed':all(c['passed'] for c in cases),'banked_process':args.banked,'cases':cases,'outputs':{name:hashlib.sha256((BIN/name).read_bytes()).hexdigest() for name in ('PROGRAM.EXE','CHILD.COM')},'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Actual DOS8086 COMSPEC /c and fallback with isolated synthetic DOS media/source-owned nested child. DOSBox virtualCOMMAND.COM resolves even with emptyCOMSPEC/PATH; candidate search order and missing-processor are separately tested under explicit DOSkernel model. Its command processor returns0 although nestedCHILD returns37. No live UART or vendor UI.'}
 (ROOT/('build/program-process-bank-dos/checks.json' if args.banked else 'build/program-process-dos/checks.json')).write_text(json.dumps(proof,indent=2)+'\n');return 0 if proof['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
