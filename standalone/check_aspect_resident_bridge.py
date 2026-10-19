#!/usr/bin/env python3
"""ControlledCPU replay of actual relocated OMF bridge and owned DOS fixtures."""
import json,re,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_INTR,UC_HOOK_CODE,UC_HOOK_INSN
from unicorn.x86_const import *
from build_aspect_resident_bridge import ROOT,OUT,sha
from check_aspect_resident_service import labels

def symbols():
 result={}
 for line in (OUT/'parent.map').read_text().splitlines():
  m=re.match(r'^\s*([0-9a-fA-F]{4}):([0-9a-fA-F]{4,8})[*+]?\s+(\w+)',line)
  if m:result[m[3]]=(int(m[1],16),int(m[2],16))
 return result

def scenario(request,flags):
 sy=symbols();LOAD,CHILD,STOP=0x2000,0x4000,0x7000
 # Map DGROUP from its explicit group line, distinct from code segment.
 group=re.search(r'DGROUP\s+([0-9A-Fa-f]{4}):', (OUT/'parent.map').read_text())
 DS=LOAD+int(group[1],16)
 c=labels(OUT/'child.lst',['parent_ds','descriptor','child_psp','service','callback','old1c','irq60','irq1c','callback_low','callback_high'])
 raw=(OUT/'PARENT.EXE').read_bytes();header=struct.unpack_from('<14H',raw);image=bytearray(raw[header[4]*16:])
 for i in range(header[3]):
  off,seg=struct.unpack_from('<HH',raw,header[12]+4*i);at=seg*16+off
  struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+LOAD)&0xffff)
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,2*1024*1024);u.mem_write(LOAD*16,bytes(image));u.mem_write(CHILD*16+0x100,(OUT/'CHILD.COM').read_bytes());u.mem_write(0x60000,b'\xcf')
 def addr(name):seg,off=sy[name];return (LOAD+seg)*16+off
 def offset(name):return addr(name)-DS*16
 def put(seg,off,value):u.mem_write(seg*16+off,struct.pack('<H',value))
 def word(seg,off):return struct.unpack('<H',u.mem_read(seg*16+off,2))[0]
 desc=offset('descriptor');low=offset('parent_stack_low');top=offset('parent_stack_top')
 for off,val in {2:LOAD-0x10,4:DS,10:CHILD,12:CHILD,14:c['callback'],16:CHILD}.items():put(DS,desc+off,val)
 for n,val in [('parent_ds',DS),('descriptor',desc),('child_psp',CHILD),('service',sy['resident_bridge_entry'][1])]:put(CHILD,c[n],val)
 put(CHILD,c['service']+2,LOAD);put(CHILD,c['old1c'],0);put(CHILD,c['old1c']+2,0x6000)
 u.mem_write(DS*16+low,b'\xcc'*(top-low))
 steps=0;coverage=set();ticks=0;unsafe=[];minsp=top
 def interrupt(number):
  ss=u.reg_read(UC_X86_REG_SS);sp=u.reg_read(UC_X86_REG_SP);fl=u.reg_read(UC_X86_REG_EFLAGS)&0xffff
  if ss!=u.reg_read(UC_X86_REG_DS):unsafe.append((number,u.reg_read(UC_X86_REG_CS),u.reg_read(UC_X86_REG_IP)))
  for v in [fl,u.reg_read(UC_X86_REG_CS),u.reg_read(UC_X86_REG_IP)]:sp-=2;put(ss,sp,v)
  u.reg_write(UC_X86_REG_SP,sp);u.reg_write(UC_X86_REG_EFLAGS,fl&~0x300);u.reg_write(UC_X86_REG_CS,CHILD);u.reg_write(UC_X86_REG_IP,c['irq60' if number==0x60 else 'irq1c'])
 def intr(emu,num,_):
  nonlocal ticks
  if num in (0x60,0x1c):interrupt(num)
  elif num==0x21:
   assert emu.reg_read(UC_X86_REG_AX)>>8==0x62,hex(emu.reg_read(UC_X86_REG_AX))
   emu.reg_write(UC_X86_REG_BX,CHILD)
  elif num==0x1a:ticks+=1;emu.reg_write(UC_X86_REG_CX,0);emu.reg_write(UC_X86_REG_DX,ticks)
  else:raise AssertionError(num)
 def code(emu,address,size,_):
  nonlocal steps,minsp
  steps+=1;assert steps<30000
  if emu.reg_read(UC_X86_REG_CS)==STOP or emu.reg_read(UC_X86_REG_IP)==0xf000:emu.emu_stop();return
  coverage.add(address)
  if emu.reg_read(UC_X86_REG_SS)==DS and emu.reg_read(UC_X86_REG_DS)==DS:minsp=min(minsp,emu.reg_read(UC_X86_REG_SP))
  if steps%29==0 and emu.reg_read(UC_X86_REG_EFLAGS)&0x200:interrupt(0x1c)
 u.hook_add(UC_HOOK_INTR,intr);u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_INSN,lambda emu,port,size,data:0x60,None,1,0,UC_X86_INS_IN)
 # Actual initialize instructions on parent's upper8192B stack.
 for r,v in [(UC_X86_REG_DS,DS),(UC_X86_REG_SS,DS),(UC_X86_REG_ES,DS),(UC_X86_REG_SP,0x2000),(UC_X86_REG_CS,LOAD),(UC_X86_REG_BX,low),(UC_X86_REG_CX,top),(UC_X86_REG_DX,sy['body'][1]),(UC_X86_REG_SI,LOAD),(UC_X86_REG_DI,sy['forward_callback'][1])]:u.reg_write(r,v)
 put(DS,0x2000,0xf000);u.reg_write(UC_X86_REG_EFLAGS,2)
 u.emu_start(addr('resident_bridge_initialize'),0,count=30000)
 assert u.reg_read(UC_X86_REG_AX)==0
 # Invalid initialization must not erase the previously installed lease.
 for r,v in [(UC_X86_REG_SP,0x2000),(UC_X86_REG_DX,0)]:u.reg_write(r,v)
 put(DS,0x2000,0xf000);u.emu_start(addr('resident_bridge_initialize'),0,count=30000)
 assert u.reg_read(UC_X86_REG_AX)==0xfffc
 if request==4:u.mem_write(DS*16+low-1,b'\0')
 values={UC_X86_REG_AX:request,UC_X86_REG_BX:0x2345,UC_X86_REG_CX:0x3456,UC_X86_REG_DX:0x4567,UC_X86_REG_SI:0x5678,UC_X86_REG_DI:0x6789,UC_X86_REG_BP:0x789a,UC_X86_REG_DS:CHILD,UC_X86_REG_SS:CHILD,UC_X86_REG_ES:0x1357}
 for r,v in values.items():u.reg_write(r,v)
 put(CHILD,0xf000,0);put(CHILD,0xf002,STOP)
 u.reg_write(UC_X86_REG_SP,0xf000);u.reg_write(UC_X86_REG_CS,LOAD);u.reg_write(UC_X86_REG_EFLAGS,flags|2)
 before=u.reg_read(UC_X86_REG_EFLAGS)&0xffff
 u.emu_start(addr('resident_bridge_entry'),0,count=30000)
 expected=[0x3456,0x4321,0xfffb,0xfffb,0xfffb][request]
 assert u.reg_read(UC_X86_REG_CS)==STOP
 assert u.reg_read(UC_X86_REG_AX)==expected,(request,hex(u.reg_read(UC_X86_REG_AX)))
 for r,v in values.items():
  if r!=UC_X86_REG_AX:assert u.reg_read(r)==v
 assert u.reg_read(UC_X86_REG_SP)==0xf004
 assert u.reg_read(UC_X86_REG_EFLAGS)&0xffff==before
 assert not unsafe,unsafe
 assert word(DS,desc+30)==0
 assert word(DS,desc+26)==int(request!=4)
 if request!=4:assert word(DS,desc+32)==1 and word(DS,desc+34)==CHILD
 # Repair deliberately corrupted sentinels only after testing typed result.
 u.mem_write(DS*16+low-1,b'\xa6');u.mem_write(DS*16+top,b'\x5a')
 assert bytes(u.mem_read(DS*16+low-16,16))==b'\xa6'*16
 assert bytes(u.mem_read(DS*16+top,16))==b'\x5a'*16
 for name,pattern in [('callback_low',0xa6),('callback_high',0x5a)]:assert bytes(u.mem_read(CHILD*16+c[name],32))==bytes([pattern])*32
 return dict(request=request,flags=before,result=expected,steps=steps,observed_parent_stack_bytes=top-minsp),coverage

def main():
 manifest=json.loads((OUT/'manifest.json').read_text())
 for n,d in manifest['binaries'].items():assert sha(OUT/n)==d
 for n,d in manifest['sources'].items():assert sha(ROOT/n)==d
 cases=[];coverage=set()
 for request in range(5):
  for flags in [2,3,0x202,0x203,0x402,0x403,0x602,0x603]:
   record,seen=scenario(request,flags);cases.append(record);coverage.update(seen)
 report=dict(passed=True,cpu_scenarios=len(cases),cases=cases,visited_addresses=len(coverage),checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),original_inputs=[],scope='Actual relocated OMF bridge/body and child callback instructions, controlled DOSPSP/BIOSclock/UART,IF-obeying child interrupt injection. Normal/deepabort/lowhighpreguard faults, invalidinit oldlease preserved, complete callerFLAGS/registers/DS=SS/redzones. Actual EXEC and realtimer separately DOS verified.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
