#!/usr/bin/env python3
"""Execute the actual high mouse allocator, restoration and quarantine paths."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
class Allocation(DosImage):
 def __init__(self,binary,strategy=0,fault=None):
  super().__init__(binary,binary.parent/'terminal.map')
  self.strategy=strategy;self.original=strategy;self.fault=fault;self.calls=[];self.sets=0;self.blocks={};self.waiting=None
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt);self.uc.hook_add(UC_HOOK_CODE,self.stop)
 def stop(self,u,address,size,data):
  if self.waiting and u.reg_read(UC_X86_REG_CS)==self.waiting[0] and address==self.waiting[1]:u.emu_stop()
 def interrupt(self,u,n,data):
  assert n==0x21,n
  ax=u.reg_read(UC_X86_REG_AX);bx=u.reg_read(UC_X86_REG_BX);es=u.reg_read(UC_X86_REG_ES);error=0;answer=0
  self.calls.append((ax,bx,es))
  if ax==0x5800:
   if self.fault=='get':error=1
   else:answer=self.strategy
  elif ax==0x5801:
   self.sets+=1
   if self.fault=='set' and self.sets==1 or self.fault in ('restore','restore-and-free') and self.sets==2:error=1
   else:self.strategy=bx
  elif ax>>8==0x48:
   assert self.strategy==2 and 1<=bx<=4096
   if self.fault=='allocate':error=8
   else:answer=0x9000;assert answer not in self.blocks;self.blocks[answer]=bx
  elif ax>>8==0x49:
   assert es in self.blocks
   if self.fault=='restore-and-free':error=7
   else:del self.blocks[es]
  else:raise AssertionError(('Unexpected DOS call',hex(ax)))
  u.reg_write(UC_X86_REG_AX,error or answer)
  flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,flags|1 if error else flags&~1)
 def bank(self,name,args=()):
  u=self.uc;cs=self.symbols['terminal_mouse_code_start']//16;stop=0xfffe
  for r,v in [(UC_X86_REG_CS,cs),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_ES,0xb800),
   (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_BX,0x3456),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
  words=[stop,*args];sp=self.offset('terminal_stack_top')-2*len(words);u.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));u.reg_write(UC_X86_REG_SP,sp)
  self.waiting=(cs,cs*16+stop);u.emu_start(self.symbols[name],0,count=100000)
  assert u.reg_read(UC_X86_REG_SP)==sp+2 and u.reg_read(UC_X86_REG_IP)==stop
  for r,v in [(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_ES,0xb800),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_BX,0x3456)]:assert u.reg_read(r)==v,(name,r)
  self.waiting=None;return u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
 binary=args.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 assert manifest['experimental_directory_resource_owner'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
 for strategy in [0,1,2]:
  for size in [1,15,16,17,608,65535]:
   m=Allocation(binary,strategy);ax,seg=m.bank('_mouse_platform_allocate',[size]);assert ax==0 and seg==0x9000 and m.blocks[seg]==(size+15)//16
   assert m.strategy==strategy and not m.get('mouse_allocation_strategy_held')
   assert [a for a,b,e in m.calls]==[0x5800,0x5801,0x4801,0x5801] or [a>>8 for a,b,e in m.calls]==[0x58,0x58,0x48,0x58]
   assert m.bank('_mouse_platform_release',[0,seg])[0]==0 and not m.blocks
   cases.append(dict(case='allocate-and-release',strategy=strategy,bytes=size,passed=True))
 m=Allocation(binary);assert m.bank('_mouse_platform_allocate',[0])==(0,0) and not m.calls
 cases.append(dict(case='zero-rejected-before-DOS',passed=True))
 for fault in ['get','set','allocate']:
  m=Allocation(binary,1,fault);assert m.bank('_mouse_platform_allocate',[608])==(0,0)
  assert not m.blocks and m.strategy==1 and not m.get('mouse_allocation_strategy_held')
  cases.append(dict(case='failed-'+fault,passed=True,calls=m.calls))
 for fault in ['restore','restore-and-free']:
  m=Allocation(binary,0,fault);assert m.bank('_mouse_platform_allocate',[608])==(0,0)
  assert m.get('mouse_allocation_strategy_held')==1 and m.get('mouse_allocation_strategy_segment')==0x9000 and m.blocks
  before=len(m.calls);assert m.bank('_mouse_platform_allocate',[16])==(0,0) and len(m.calls)==before
  result=m.stage_near(b'CHILD.COM\0'+bytes(22)+b'\xa5'*8)
  assert m.call('process_run',[result,0,result+32])==4 and len(m.calls)==before
  assert bytes(m.uc.mem_read(m.data_base+result+32,8))==b'\xa5'*8
  status=m.bank('_mouse_platform_strategy_finish')[0]
  assert m.strategy==0
  if fault=='restore':assert status==0 and not m.blocks and not m.get('mouse_allocation_strategy_held')
  else:
   assert status==7 and m.blocks and m.get('mouse_allocation_strategy_held') and m.get('mouse_allocation_strategy_free_attempted')==1
   before=len(m.calls);assert m.bank('_mouse_platform_strategy_finish')[0]==9 and len(m.calls)==before
  cases.append(dict(case=fault+'-retains-identity-and-refuses-EXEC',passed=True,calls=m.calls))
 result=dict(passed=True,binary_sha256=sha(binary),cases=cases,inputs=len(cases),original_inputs=[],
  sources={n:sha(ROOT/n) for n in ['standalone/check_resource_mouse_allocation.py','standalone/dos_image.py','src/mouse/dos_memory.asm','src/mouse/terminal.asm','src/process/dos_exec.asm']},
  scope='Actual linked allocation/cleanup/EXEC guard instructions, modeled DOS5800/5801/48/49 only. Native package tests separately verify real DOS strategy restoration.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'high allocation/restore/quarantine inputs')
if __name__=='__main__':main()
