#!/usr/bin/env python3
"""Native ALARM controller replay with explicit clock/keyboard/sound boundaries."""
import argparse,json,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from build_context_help import ROOT,sha
DATA=0x30000

class Alarm:
 def __init__(self,units):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  for r in units:self.u.mem_write(0x10000+r['start'],(ROOT/r['output']).read_bytes())
  for reg in (UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES):self.u.reg_write(reg,DATA>>4)
  self.u.reg_write(UC_X86_REG_CS,0x1000);self.u.hook_add(UC_HOOK_CODE,self.hook)
 def word(self,at):return int.from_bytes(self.u.mem_read(DATA+at,2),'little')
 def ret(self,value=0,cleanup=0):
  sp=self.u.reg_read(UC_X86_REG_SP);self.u.reg_write(UC_X86_REG_AX,value&65535);self.u.reg_write(UC_X86_REG_IP,self.word(sp));self.u.reg_write(UC_X86_REG_SP,sp+2+cleanup)
 def hook(self,u,at,size,_):
  self.seen.add(at)
  if at==0x1f800:u.emu_stop();return
  if 0x1e660<=at<0x1e67b or 0x13616<=at<0x13673:return
  if at==0x1e0e4:self.options+=1;self.ret(self.override is not None)
  elif at==0x1dd9c:self.operands+=1;self.ret(self.override)
  elif at==0x13323:
   self.ret((59+self.clock_reads*self.step)%60);self.clock_reads+=1
  elif at==0x1651a:
   self.peeks+=1;self.pending=self.cancel is not None and self.peeks>=self.cancel and not self.reads;self.ret(self.pending)
  elif at==0x164fe:assert self.pending;self.reads+=1;self.ret(0x011b)
  elif at==0x17722:
   sp=u.reg_read(UC_X86_REG_SP);self.tones.append((self.word(sp+4),self.word(sp+2)));self.ret(0,4)
  elif at==0x16b98:
   sp=u.reg_read(UC_X86_REG_SP);self.waits.append(self.word(sp+2));self.ret(0,2)
  else:raise AssertionError(hex(at))
 def run(self,default,override,enabled,cancel,step):
  self.override=override;self.cancel=cancel;self.step=step
  self.options=self.operands=self.clock_reads=self.peeks=self.reads=0;self.pending=False;self.tones=[];self.waits=[];self.seen=set()
  self.u.mem_write(DATA+0x1d3e,b'ZZ'+enabled.to_bytes(2,'little')+default.to_bytes(2,'little')+b'ZZ')
  self.u.mem_write(DATA+0xd000,b'\x00\xf8')
  for r,v in [(UC_X86_REG_SP,0xd000),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:self.u.reg_write(r,v)
  self.u.emu_start(0x1e660,0x20000,count=10000)
  assert self.u.reg_read(UC_X86_REG_IP)==0xf800 and self.u.reg_read(UC_X86_REG_SP)==0xd002
  for r,v in [(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_DS,DATA>>4),(UC_X86_REG_SS,DATA>>4)]:assert self.u.reg_read(r)==v
  assert bytes(self.u.mem_read(DATA+0x1d3e,8))==b'ZZ'+enabled.to_bytes(2,'little')+default.to_bytes(2,'little')+b'ZZ'
  duration=default if override is None else override
  cycles=min(duration,cancel-1) if step and cancel else duration if step else cancel-1 if duration else 0
  tones=cycles if enabled else 0
  assert self.options==1 and self.operands==int(override is not None)
  assert self.tones==[(880,15),(880,15)]*tones and self.waits==[1,6]*tones
  assert self.peeks==cycles+2 and self.reads==int(cancel is not None and cancel<=cycles+2)
  assert self.clock_reads==1+cycles*(2 if step else 1)
  return self.seen

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 fixture=ROOT/'standalone/fixtures/aspect_alarm_native_units.json';proof=json.loads(fixture.read_text());units=[]
 for r in proof['units']:
  dest=out/(r['name']+'.bin');subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/','-DASPECT_ALARM_FLAT','-DASPECT_ALARM_UNIT='+str(r['unit']),str(ROOT/'src/aspect/alarm_native.asm'),'-o',str(dest)],check=True)
  assert dest.stat().st_size==r['bytes'] and sha(dest)==r['sha256'];units.append(dict(**r,output=str(dest.relative_to(ROOT))))
 subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/'src/aspect/alarm_native.asm'),'-o',str(out/'alarm.obj')],check=True)
 alarm=Alarm(units);count=0;seen=set()
 for default in (0,1,3,65535):
  for override in (None,0,1,3):
   duration=default if override is None else override
   for enabled in (0,1,65535):
    for cancel in (None,1,3,8):
     for step in (0,1):
      if cancel is None and (duration>100 or (duration and not step)):continue
      seen|=alarm.run(default,override,enabled,cancel,step);count+=1
 names=['src/aspect/alarm_native.asm','standalone/check_aspect_alarm.py','standalone/fixtures/aspect_alarm_native_units.json','reconstruction/uart/encodings.inc']
 report=dict(passed=True,cases=count,native_bytes=120,units=units,instruction_addresses=len(seen),sources={n:sha(ROOT/n) for n in names},original_inputs=[],scope=__doc__+' Source instructions match fixed original-range digests. Native optional-duration restoration, paired880Hz/duration15 requests and1/6-tick waits, quiet timing, seconds wrap/freeze and late-key consumption checked on DS=SS. Operand, clock, keyboard and tone/wait services modeled. Not actual BIOS/UART/PIT/audio timing or a serviced production binding; no installed change.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('ALARM native',count,'cases PASS;120 exact bytes')
if __name__=='__main__':main()
