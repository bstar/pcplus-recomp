#!/usr/bin/env python3
"""Actual DOS EXEC: child cannot write/close leased parent file descriptors."""
import argparse,hashlib,json,os,re,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
 for name,defines in [('isolated',[]),('two-handles',['TWO_HANDLES']),('failed-EXEC',['MISSING_CHILD']),('partial-recover',['RECOVER_PARTIAL']),('unisolated-control',['UNISOLATED'])]:
  drive=out/name;drive.mkdir()
  subprocess.run(['nasm','-fobj',*['-D'+d for d in defines],str(ROOT/'standalone/gateway_handles_host.asm'),'-o',str(drive/'host.obj')],check=True)
  subprocess.run(['nasm','-fobj',str(ROOT/'src/process/dos_exec.asm'),'-o',str(drive/'exec.obj')],check=True)
  subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-dPROCESS_HANDLES_BANKED','-nt=FILE_CODE','-nc=FARCODE','-fo='+str(drive/'handles.obj'),str(ROOT/'src/process/process_handles.c')],cwd=drive,check=True)
  subprocess.run(['wlink','system','dos','order','clname','CODE','clname','FARCODE','clname','DATA','clname','STACK','option','quiet','option','map='+str(drive/'host.map'),'name',str(drive/'HOST.EXE'),'file',','.join(str(drive/n) for n in ['host.obj','exec.obj','handles.obj'])],check=True)
  listing=(drive/'host.map').read_text();syms={n:int(s,16)*16+int(o,16) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
  end=syms['handles_probe_stack_top'];assert syms['_process_handles_storage']+36<=end
  assert all(syms[n]<end for n in ['_process_handles_begin','_process_handles_end','_process_handles_recover'])
  subprocess.run(['nasm','-fbin',str(ROOT/'standalone/gateway_handles_child.asm'),'-o',str(drive/'CHILD.COM')],check=True)
  cfg=drive/'dosbox.conf';cfg.write_text(f'''[sdl]
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
HOST
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
''')
  with (drive/'dosbox.log').open('w') as log:
   process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(cfg)],cwd=drive,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
  control=name=='unisolated-control';missing=name=='failed-EXEC'
  checks=dict(normal_exit=process.returncode==0,host_checks=(drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),
   parent_bytes=(drive/'PRIVATE.DAT').read_bytes()==(b'AX' if control else b'AB'),retained_state=syms['_process_handles_storage']+36<=end)
  if missing:checks['failed_EXEC_no_child']=not (drive/'CHILD.BIN').exists()
  else:
   report=struct.unpack('<5H',(drive/'CHILD.BIN').read_bytes());checks.update(child_cannot_write_close=report[:2]==((1,0) if control else (6,6)),child_reuses_private_slot=report[4]==5,child_own_bytes=(drive/'OWN.DAT').read_bytes()==b'Y')
   if name=='two-handles':checks.update(second_private_bytes=(drive/'SECOND.DAT').read_bytes()==b'AB',second_cannot_write_close=report[2:4]==(6,6))
  case=dict(case=name,passed=all(checks.values()),checks=checks,host_sha256=sha(drive/'HOST.EXE'),child_sha256=sha(drive/'CHILD.COM'));cases.append(case)
  print(name,{k:v for k,v in checks.items() if not v},flush=True);assert case['passed'],case
 sources=['standalone/test_gateway_handles_dos.py','standalone/gateway_handles_host.asm','standalone/gateway_handles_child.asm','src/process/process_handles.c','src/process/process_handles.h','src/process/dos_exec.asm']
 result=dict(passed=True,cases=cases,sources={n:sha(ROOT/n) for n in sources},original_inputs=[],scope=__doc__+' Standalone raw-EXEC diagnostic, 8086 with no FPU. Does not prove active application capture/printer/UART preservation.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
