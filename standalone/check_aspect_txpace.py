#!/usr/bin/env python3
"""Source-only TXPACE service model, native CPU and actual DOS clock checks."""
import ctypes,hashlib,json,os,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-txpace'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.loads((OUT/'manifest.json').read_text());assert m['original_inputs']==[]
 for p,h in m['sources'].items():assert sha(ROOT/p)==h,p
 for p,h in m['outputs'].items():assert sha(OUT/p)==h,p
 b=(OUT/'delay.bin').read_bytes();assert len(b)==38 and hashlib.sha256(b).hexdigest()=='a7149212d6d9857e43f3e86112c258c9e11c2aeae0d292ef964a908b43beb850'
 cpu=[]
 for count,floor,units,iflag in [(0,0,0,0),(1,0,1,0),(128,0,1,1),(8,0,999,1),(0,0,1,1),(1,65535,1,0)]:
  u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x16b72,b)
  for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_SP,0x8800),(UC_X86_REG_EFLAGS,2+512*iflag)]:u.reg_write(r,v)
  for o,v in [(0x8800,0xf000),(0x8802,units),(0x7ac4,count),(0x7a4e,floor)]:u.mem_write(0x30000+o,struct.pack('<H',v))
  loops=[0]
  def hook(m,a,n,d):
   if a==0x1f000:m.emu_stop()
   if a==0x16b87:loops[0]+=1
  u.hook_add(UC_HOOK_CODE,hook);u.hook_add(UC_HOOK_INTR,lambda *a:(_ for _ in ()).throw(AssertionError('UnexpectedIRQ')));u.emu_start(0x16b72,0x20000,count=400000)
  want=units*((count-floor)&65535 or 65536);assert loops[0]==want and u.reg_read(UC_X86_REG_IP)==0xf000 and u.reg_read(UC_X86_REG_SP)==0x8804 and bool(u.reg_read(UC_X86_REG_EFLAGS)&512)==bool(iflag)
  cpu.append(dict(count=count,floor=floor,units=units,inner_iterations=want,passed=True))
 # Compiled maintained state machine with explicit clock/native-step models.
 (OUT/'model.c').write_text('''unsigned model_flags=512,model_at,model_size,model_native_calls;unsigned long model_ticks[30000];unsigned aspect_txpace_flags(void){return model_flags;}void aspect_txpace_restore_if(unsigned f){model_flags=(model_flags&~512U)|(f&512U);}unsigned long aspect_txpace_ticks(void){return model_ticks[model_at<model_size?model_at++:model_size-1];}void aspect_txpace_native_one(void){++model_native_calls;}''')
 subprocess.run(['cc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',str(ROOT/'src/aspect/txpace.c'),str(OUT/'model.c'),'-o',str(OUT/'model.so')],check=True)
 lib=ctypes.CDLL(str(OUT/'model.so'));U=ctypes.c_uint;UL=ctypes.c_ulong;CB=ctypes.CFUNCTYPE(U,U)
 var=lambda name:U.in_dll(lib,name);ticks=(UL*30000).in_dll(lib,'model_ticks');prep=lib.aspect_txpace_prepare_bounded;prep.argtypes=[CB,U];prep.restype=U;delay=lib.aspect_txpace_delay;delay.argtypes=[U,CB];delay.restype=U
 cases=[]
 def run(name,clock,want,limit=100,flags=512,cancel=0,drop=0,expected_chunks=None):
  lib.aspect_txpace_reset();var('model_flags').value=flags;var('model_at').value=0;var('model_size').value=len(clock);var('model_native_calls').value=0
  for i,t in enumerate(clock):ticks[i]=t
  phases=[]
  def step(phase):
   phases.append(phase)
   if phase==drop:var('model_flags').value&=~512
   return 42 if phase==cancel else 0
  cb=CB(step);actual=prep(cb,limit);assert actual==want,(name,actual,want);assert var('model_flags').value&512==flags&512
  if want:assert not lib.aspect_txpace_ready()and not var('aspect_txpace_count').value
  result=dict(name=name,error=actual,native_calls=var('model_native_calls').value,passed=True)
  if not want:
   expected=((len(clock)-3)if expected_chunks is None else expected_chunks)*512//55;assert var('aspect_txpace_count').value==expected,(name,var('aspect_txpace_count').value,expected)
   before=var('model_native_calls').value;assert delay(0,cb)==0 and var('model_native_calls').value==before;assert delay(999,cb)==0 and var('model_native_calls').value==before+999
   result['count']=expected
  cases.append(result)
 run('normal',[0,0,1]+[1]*9+[2],0)
 run('midnight',[1573038,1573038,1573039]+[1573039]*9+[0],0)
 run('IF0',[0],3,flags=0)
 run('alignmentstall',[0],5,limit=3)
 run('measurementstall',[0,0,1],5,limit=4)
 run('twoticks',[0,0,1,3],4)
 run('invalidclock',[1573040],4)
 run('coarse',[0,0,1,2],7)
 run('cancelalign',[0],6,cancel=1)
 run('canceladmit',[0],6,cancel=2)
 run('cancelpost',[0,0,1]+[1]*9+[2],6,cancel=3)
 run('callbackIF',[0],3,drop=2)
 run('budgetrange',[0],1,limit=7040)
 run('alignment_budget_independent',[0,0]+[0]*8000+[1]+[1]*9+[2],0,limit=10,expected_chunks=10)
 run('maxcount',[0,0,1]+[1]*7038+[2],0,limit=7039)
 # Ready service cancellation remains typed and preserves calibration state.
 cb=CB(lambda phase:42);before=var('model_native_calls').value;assert delay(4,cb)==6 and var('model_native_calls').value==before and var('aspect_txpace_step_error').value==42
 assert delay(1000,cb)==1;lib.aspect_txpace_reset();assert delay(1,cb)==2
 # Actual DOS clock evidence; standard BIOS tick and no PIC modification.
 dos=[]
 for cycles in [6000,30000]:
  conf=OUT/f'dosbox-{cycles}.conf';conf.write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed {cycles}\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nTXPACE\nexit\n');(OUT/'RESULT.BIN').unlink(missing_ok=True)
  with(OUT/f'dosbox-{cycles}.log').open('w')as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(conf)],cwd=OUT,stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=30,check=True)
  data=(OUT/'RESULT.BIN').read_bytes();(OUT/f'RESULT-{cycles}.BIN').write_bytes(data);w=struct.unpack('<28H',data)
  assert w[0]==w[5]and w[1]&512==w[6]&512 and w[2]==0 and w[3]>0 and w[4]==1,(cycles,w)
  samples=[]
  for i,(low,high)in enumerate([(0,0),(0,3),(10,28)]):
   unit,elapsed,error=w[7+i*3:10+i*3];assert error==0 and low<=elapsed<=high,(cycles,unit,elapsed,error);samples.append(dict(units=unit,ticks=elapsed))
  assert w[16:24]==(3,0,6,42,0,3,512,0),(cycles,w[16:24])
  dos.append(dict(cycles=cycles,count=w[3],pic_before=w[0],pic_after=w[5],if_before=w[1]&512,if_after=w[6]&512,samples=samples,IF0_error=w[16],step_error=w[18],callback_IF_error=w[21],alignment_callbacks=w[24],passed=True))
 r=dict(passed=True,original_inputs=[],checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),diagnostic_sha256=m['outputs']['TXPACE.EXE'],cpu=cpu,service_model=cases,service_delay_error_assertions=3,actual_dos=dos,scope='Exact38Bnativebusyloop+maintainedboundedIRQlivebatchcalibration. Hostclocksareexplicitmodels;actualDOSusesrealvirtualBIOSandPIC. No physicaltiming/UARTintegrationproof.')
 (OUT/'checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(cpu=len(cpu),service=len(cases),dos=dos),indent=2))
if __name__=='__main__':main()
