#!/usr/bin/env python3
"""Terminal-linked setup transaction; only canonical/PRM file boundaries modeled."""
import hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *
from dos_image import DosImage
from check_setup_model import image
from check_startup_import import terminal_expected
from check_modem_import import expected as modem_expected
from check_directory_live import record,serial_expected,plan_expected,word,text
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/terminal';MAX_STACK=[0]
class Owner(DosImage):
 def __init__(self,directory=False):
  super().__init__(OUT/'TERMINAL.EXE',OUT/'terminal.map');self.directory=directory
  self.raw=image();self.record=record();self.canonical=b'D:\\WORK\\TEST.PRM';self.canonical_error=0;self.io_error=0;self.reads=[]
  pointer=self.offset('terminal_stack_top')-self.stack_bytes+16
  for name,size in [('path',64),('context',496),('source',44),('active',628),('target',64),('destination',628),('result',8)]:setattr(self,name,pointer);pointer+=size
  self.fixture_scratch_end=pointer
  self.uc.mem_write(self.data_base+self.path,b'TEST.PRM'.ljust(64,b'\0'))
  self.uc.mem_write(self.data_base+self.target,b'Local.Example:23'.ljust(64,b'\0'))
  context=struct.pack('<H',17)+bytes(250)+self.record+bytes(2)+b'TEST.PRM'.ljust(64,b'\0')+b'TEST.DIR'.ljust(64,b'\0')
  self.uc.mem_write(self.data_base+self.context,context)
  self.initial=(serial_expected(self.raw,self.record)+modem_expected(self.raw)+plan_expected(17,self.record,0,b'MiXeD.Host:23') if directory else terminal_expected(self.raw)+modem_expected(self.raw)+bytes(214))+bytes(2)
  self.uc.mem_write(self.data_base+self.source,self.initial[:44]);self.uc.mem_write(self.data_base+self.active,self.initial)
  self.uc.reg_write(UC_X86_REG_ES,self.ds)
  for name in ['capture_fs_canonical_','_prm_dos_load']:self.uc.mem_write(self.symbols[name],b'\xc3')
  self.uc.hook_add(UC_HOOK_CODE,self.boundary)
  self.uc.hook_add(UC_HOOK_INTR,self.forbid)
  for ins in [UC_X86_INS_IN,UC_X86_INS_OUT]:self.uc.hook_add(UC_HOOK_INSN,self.forbid,None,1,0,ins)
 def forbid(self,*args):raise AssertionError('Setup transaction attempted unmodeled interrupt or port I/O')
 def string(self,p):return bytes(self.uc.mem_read(self.data_base+p,128)).split(b'\0')[0]
 def boundary(self,u,address,size,_):
  used=self.offset('terminal_stack_top')-u.reg_read(UC_X86_REG_SP)
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds and 0<=used<8192
  MAX_STACK[0]=max(MAX_STACK[0],used)
  if address==self.symbols['capture_fs_canonical_']:
   path=u.reg_read(UC_X86_REG_AX);dest=u.reg_read(UC_X86_REG_DX)
   assert self.string(path).upper()==b'TEST.PRM'
   if not self.canonical_error:u.mem_write(self.data_base+dest,self.canonical.ljust(128,b'\0'))
   u.reg_write(UC_X86_REG_AX,self.canonical_error)
  if address==self.symbols['_prm_dos_load']:
   path,dest,result=struct.unpack('<3H',u.mem_read(self.data_base+u.reg_read(UC_X86_REG_SP)+2,6))
   assert self.string(path)==b'D:\\WORK\\TEST.PRM','PRM reread used a changed working namespace'
   self.reads.append((self.string(path),dest))
   if not self.io_error:u.mem_write(self.data_base+dest,self.raw)
   u.mem_write(self.data_base+result,struct.pack('<4H',self.io_error,5 if self.io_error else 0,0,0 if self.io_error else 1264))
   u.reg_write(UC_X86_REG_AX,self.io_error)
 def invoke(self,name,args):
  answer=self.call(name,args,limit=2500000)
  for r,w in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,self.ds)]:assert self.uc.reg_read(r)==w,(name,r)
  top=self.offset('terminal_stack_top');assert bytes(self.uc.mem_read(self.data_base+top-2*len(args),2*len(args)))==struct.pack('<'+'H'*len(args),*args)
  return answer
 def bind(self,args=None):return self.invoke('_live_setup_bind',args or [self.path,self.context if self.directory else 0,self.source])
 def begin(self,mask=0,args=None):return self.invoke('_live_setup_begin',args or [self.path,self.context if self.directory else 0,self.active,16|(64 if self.directory else 32)|mask,self.target])
 def finish(self,args=None):
  self.uc.mem_write(self.data_base+self.destination,b'\xcc'*628);self.uc.mem_write(self.data_base+self.result,b'\xdd'*8)
  status=self.invoke('_live_setup_finish',[self.destination,self.result] if args is None else args)
  if status:assert self.output()==b'\xcc'*628
  return status,struct.unpack('<4H',self.uc.mem_read(self.data_base+self.result,8))
 def output(self):return bytes(self.uc.mem_read(self.data_base+self.destination,628))
 def ready(self):assert self.bind()==0 and self.begin()==0;return self
def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 for directory in (False,True):
  m=Owner(directory).ready();assert m.finish()==(0,(0,0,0,0));assert m.output()[:626]==m.initial[:626]
 done('exact-initial-candidate-with-and-without-retained-selection',2)
 edits=[(0,1,0,1),(2,8,0,2),(4,1,0,4),(6,2,0,4),(8,7,0,4),(0x198,1,0,8),(0x19a,0,0,8),(0x194,6,0,16),
  (0x1ae,14,32,0),(0x1b0,14,32,0),(0x1b2,14,32,0),(0x1b4,14,32,0),(0x1b6,14,32,0),(0x19c,0,32,0),(0x19e,0,32,0),
  (0x1e4,31,64|128,0),(0xa,46,128,0),(0xc,3,128,0),(0xe,0,128,0),(0x10,0,128,0),(0x14,1,128,0),(0x16,4,128,0),(0x1a4,65535,512,0)]
 for at,value,applied,deferred in edits:
  m=Owner().ready();m.raw=word(m.raw,at,value);assert m.finish()==(0,(0,0,applied,deferred)),hex(at)
  assert m.output()[:18]==m.initial[:18] and m.output()[32:36]==m.initial[32:36]
 done('every-mapped-scalar-category-applied-or-deferred-with-valid-active-transport',len(edits))
 for mask in range(16):
  m=Owner();assert m.bind()==0 and m.begin(mask)==0
  for at,value in [(0,1),(2,8),(4,1),(6,2),(8,7),(0x198,1),(0x19a,0)]:m.raw=word(m.raw,at,value)
  assert m.finish()==(0,(0,0,0,15^mask));assert m.output()[:18]==m.initial[:18] and m.output()[32:36]==m.initial[32:36]
 done('all16-explicit-CLI-category-precedence-combinations',16)
 for changed,flag in [(False,0),(True,512)]:
  m=Owner();active=word(word(m.initial,2,38400),4,0);m.uc.mem_write(m.data_base+m.active,active)
  assert m.bind()==0 and m.begin()==0
  if changed:m.raw=word(m.raw,0x1a4,65535)
  assert m.finish()==(0,(0,0,flag,0));assert m.output()[2:6]==struct.pack('<HH',38400,0)
 m=Owner();m.uc.mem_write(m.data_base+m.active,word(m.initial,2,38400));assert m.bind()==0
 for _ in range(3):
  assert m.begin()==0;m.raw=word(m.raw,2,8);assert m.finish()==(0,(0,0,0,2));assert m.output()[2:6]==struct.pack('<HH',38400,0)
 done('unrelated-saves-preserve-autobaud-and-deliberate-pending-rate-persists',5)
 m=Owner().ready();m.canonical=b'D:\\OTHER\\TEST.PRM';assert m.finish()[0]==0 and len(m.reads)==1
 assert m.begin()==3 and len(m.reads)==1
 m=Owner();m.canonical_error=5;assert m.bind()==3 and m.begin()==2 and not m.reads
 m=Owner().ready();m.uc.mem_write(m.data_base+m.path,b'OTHER.PRM\0');assert m.finish()[0]==0 and m.reads[0][0]==b'D:\\WORK\\TEST.PRM'
 done('canonical-startup-binding-refuses-retarget-and-finish-reads-frozen-absolute-path',3)
 for status in range(1,7):
  m=Owner().ready();m.io_error=status;assert m.finish()==(4,(4,status,0,0));assert m.finish()[0]==7
 for at,value in [(0,4),(2,9),(0x194,5),(0x198,2)]:
  m=Owner().ready();m.raw=word(m.raw,at,value);assert m.finish()[0]==5
 m=Owner().ready();m.uc.mem_write(m.data_base+m.target,b'BAD^\0') # frozen begin target remains valid.
 assert m.finish()[0]==0
 m=Owner();m.uc.mem_write(m.data_base+m.target,b'BAD^\0');m.ready();assert m.finish()[0]==6
 done('read-decode-and-native-command-failures-preserve-caller-candidate',12)
 for delta in [0,250,367,432]:
  m=Owner(True);assert m.bind()==0;at=m.data_base+m.context+delta;old=bytes(m.uc.mem_read(at,1));m.uc.mem_write(at,bytes([old[0]^1]));assert m.begin()==3 and not m.reads
 m=Owner(True).ready();active=bytearray(m.initial);active[508+0x6b]^=1
 # Accounting changes the current record baseline, never the retained context.
 m.uc.mem_write(m.data_base+m.active,bytes(active));assert m.invoke('_live_setup_abort',[0])==0 and m.begin()==0
 assert m.finish()==(0,(0,0,0,0))
 done('retained-context-identity-and-separate-accounting-baseline',5)
 m=Owner();assert m.begin()==2 and m.finish()[0]==7
 m.ready();assert m.invoke('_live_setup_abort',[0])==0 and m.finish()[0]==7 and m.begin()==0
 assert m.begin()==7 and m.finish()[0]==0
 done('unbound-pending-abort-and-single-consumption-lifecycle',4)
 count=0
 for index,pointer in [(0,0),(0,0xff00),(1,0),(1,0xffff),(0,1)]:
  m=Owner().ready();args=[m.destination,m.result];args[index]=pointer
  if pointer==1:args[0]=m.result
  assert m.finish(args)[0]==1 and m.finish()[0]==0;count+=1
 m=Owner().ready();assert m.finish()[0]==0;owned=m.reads[-1][1]
 assert m.begin()==0 and m.finish([owned,m.result])[0]==1 and m.finish()[0]==0;count+=1
 done('null-wrap-overlap-and-internal-storage-guards-before-consumption',count)
 report=dict(passed=True,binary_sha256=hashlib.sha256((OUT/'TERMINAL.EXE').read_bytes()).hexdigest(),inputs=sum(c['inputs'] for c in cases),cases=cases,maximum_CPU_call_stack_bytes=MAX_STACK[0],scope='Actual terminal-linked far-C setup owner, real native command expansion, pure validators and near/far adapters. Only PRM read and DOS canonicalizer boundaries are modeled. No active globals, file writes, UART or video access; caller-owned output and pending lifecycle are checked. Separate live application and real DOS tests cover foreground commit.')
 (OUT/'live-setup-owner-checks.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
