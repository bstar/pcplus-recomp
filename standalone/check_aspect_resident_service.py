#!/usr/bin/env python3
"""Independent source-only CPU checks of far-service switch and nested callback.
DOS/BIOS return values are controlled here; actual EXEC/IRQs are separate DOS proof.
"""
import json,re,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_INTR,UC_HOOK_CODE
from unicorn.x86_const import *
from build_aspect_resident_service import ROOT,OUT,sha

def labels(path,names):
 lines=path.read_text().splitlines();found={}
 for name in names:
  for i,line in enumerate(lines):
   if re.search(r'\b'+name+r':',line):
    for follow in lines[i:]:
     m=re.match(r'\s*\d+\s+([0-9A-F]{8})\s',follow)
     if m:found[name]=int(m[1],16)+0x100;break
    break
  assert name in found,name
 return found

def scenario(flags,busy):
 p=labels(OUT/'PARENT.lst',['resident_service_entry','resident_service_parent_ds','resident_service_descriptor','resident_service_stack_low','resident_service_stack','resident_service_stack_top','resident_service_stack_high'])
 c=labels(OUT/'CHILD.lst',['parent_ds','descriptor','service','child_psp','irq60','irq1c','old1c','callback','callback_low','callback_high','injected','timer_parent'])
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,2*1024*1024)
 PS,CS,STOP=0x2000,0x4000,0x7000
 u.mem_write(PS*16+0x100,(OUT/'PARENT.COM').read_bytes());u.mem_write(CS*16+0x100,(OUT/'CHILD.COM').read_bytes())
 def put(seg,off,value):u.mem_write(seg*16+off,struct.pack('<H',value))
 def word(seg,off):return struct.unpack('<H',u.mem_read(seg*16+off,2))[0]
 put(PS,p['resident_service_parent_ds'],PS)
 d=p['resident_service_descriptor']
 for off,value in {0:0x5253,2:PS,4:PS,6:p['resident_service_entry'],8:PS,10:CS,12:CS,14:c['callback'],16:CS,18:busy,20:0xaaaa,22:0xbbbb}.items():put(PS,d+off,value)
 for name,value in [('parent_ds',PS),('descriptor',d),('child_psp',CS),('service',p['resident_service_entry'])]:put(CS,c[name],value)
 put(CS,c['service']+2,PS);put(CS,c['old1c'],0);put(CS,c['old1c']+2,0x6000);u.mem_write(0x60000,b'\xcf')
 values={UC_X86_REG_AX:0x1234,UC_X86_REG_BX:0x2345,UC_X86_REG_CX:0x3456,UC_X86_REG_DX:0x4567,UC_X86_REG_SI:0x5678,UC_X86_REG_DI:0x6789,UC_X86_REG_BP:0x789a,UC_X86_REG_DS:CS,UC_X86_REG_ES:0x1357,UC_X86_REG_SS:CS}
 for r,value in values.items():u.reg_write(r,value)
 sp=0xf000;put(CS,sp,0);put(CS,sp+2,STOP)
 u.reg_write(UC_X86_REG_SP,sp);u.reg_write(UC_X86_REG_CS,PS);u.reg_write(UC_X86_REG_IP,p['resident_service_entry']);u.reg_write(UC_X86_REG_EFLAGS,flags|2)
 baseline=u.reg_read(UC_X86_REG_EFLAGS)&0xffff
 steps=0;interrupts=0;min_parent=p['resident_service_stack_top'];min_callback=0xffff;unsafe=[];coverage=set();ticks=0
 def interrupt(number):
  nonlocal interrupts
  ss=u.reg_read(UC_X86_REG_SS);at=u.reg_read(UC_X86_REG_SP);fl=u.reg_read(UC_X86_REG_EFLAGS)&0xffff
  ip=u.reg_read(UC_X86_REG_IP);seg=u.reg_read(UC_X86_REG_CS)
  if ss!=u.reg_read(UC_X86_REG_DS):unsafe.append((number,seg,ip,ss,u.reg_read(UC_X86_REG_DS)))
  for value in [fl,seg,ip]:at=(at-2)&0xffff;put(ss,at,value)
  u.reg_write(UC_X86_REG_SP,at);u.reg_write(UC_X86_REG_EFLAGS,fl&~0x300)
  u.reg_write(UC_X86_REG_CS,CS);u.reg_write(UC_X86_REG_IP,c['irq60' if number==0x60 else 'irq1c']);interrupts+=1
 def intr(emu,number,_):
  nonlocal ticks
  if number in (0x60,0x1c):interrupt(number)
  elif number==0x21:
   assert (emu.reg_read(UC_X86_REG_AX)>>8)==0x62
   emu.reg_write(UC_X86_REG_BX,CS)
  elif number==0x1a:
   ticks+=1;emu.reg_write(UC_X86_REG_CX,0);emu.reg_write(UC_X86_REG_DX,ticks)
  else:raise AssertionError(number)
 def code(emu,address,size,_):
  nonlocal steps,min_parent,min_callback
  steps+=1
  assert steps<20000
  if emu.reg_read(UC_X86_REG_CS)==STOP:emu.emu_stop();return
  ss=emu.reg_read(UC_X86_REG_SS);sp=emu.reg_read(UC_X86_REG_SP)
  if ss==PS:min_parent=min(min_parent,sp)
  if ss==CS and c['callback_low']<=sp<=c['callback_high']:min_callback=min(min_callback,sp)
  coverage.add(address)
  # Hardware-style injection obeys IF, including the individual SS/SP/DS
  # instructions. CLI windows must never permit an IRQ during partial switch.
  if steps%23==0 and emu.reg_read(UC_X86_REG_EFLAGS)&0x200:interrupt(0x1c)
 u.hook_add(UC_HOOK_INTR,intr);u.hook_add(UC_HOOK_CODE,code)
 # Actual IN opcode in child callback gets a controlled UART LSR in CPU proof.
 from unicorn import UC_HOOK_INSN
 u.hook_add(UC_HOOK_INSN,lambda emu,port,size,data:0x60,None,1,0,UC_X86_INS_IN)
 u.emu_start(PS*16+p['resident_service_entry'],0,count=20000)
 assert u.reg_read(UC_X86_REG_CS)==STOP
 assert u.reg_read(UC_X86_REG_AX)==(0xfffe if busy else 0x3456)
 for r,value in values.items():
  if r!=UC_X86_REG_AX:assert u.reg_read(r)==value,(r,u.reg_read(r),value)
 assert u.reg_read(UC_X86_REG_SP)==sp+4
 assert u.reg_read(UC_X86_REG_EFLAGS)&0xffff==baseline
 assert not unsafe,unsafe
 assert word(PS,d+18)==busy
 if busy:
  assert word(PS,d+20)==0xaaaa and word(PS,d+22)==0xbbbb
  assert word(PS,d+26)==0 and word(PS,d+28)==1
 else:
  assert word(PS,d+26)==1 and word(PS,d+28)==1 and word(PS,d+30)==0
  assert word(PS,d+32)==1 and word(PS,d+34)==CS
  assert word(CS,c['injected'])==3
 for seg,low,high in [(PS,p['resident_service_stack_low'],p['resident_service_stack_high']),(CS,c['callback_low'],c['callback_high'])]:
  assert bytes(u.mem_read(seg*16+low,32))==b'\xa6'*32
  assert bytes(u.mem_read(seg*16+high,32))==b'\x5a'*32
 return dict(flags=baseline,busy=busy,steps=steps,interrupts=interrupts,observed_parent_bytes=p['resident_service_stack_top']-min_parent,observed_callback_low_SP=None if min_callback==0xffff else min_callback),coverage

def main():
 manifest=json.loads((OUT/'manifest.json').read_text())
 for n,d in manifest['binaries'].items():assert sha(OUT/n)==d
 records=[];coverage=set()
 for flags in [0x2,0x3,0x202,0x203,0x402,0x403,0x602,0x603]:
  for busy in [0,1]:
   result,visited=scenario(flags,busy);records.append(result);coverage.update(visited)
 report=dict(passed=True,cpu_scenarios=len(records),cases=records,visited_addresses=len(coverage),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),original_inputs=[],scope='Actual source instructions in controlled realmodeCPU: modeledDOS62,BIOSclock,UARTLSR, injectedchildinterrupts honoringIF; completeSS/SP/DS switch windows monitored. Actual EXEC/BIOS timer verified separately underDOS. Does not measure arbitrary renderer stack depth.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
