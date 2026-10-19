#!/usr/bin/env python3
"""Native instruction comparison with explicit operand/stdio/DOS boundaries."""
import argparse,hashlib,json
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from build_aspect_file_info import ROOT,OUT,sha
DATA=0x30000
class Machine:
 def __init__(self,original=None):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  self.units=json.loads((OUT/'manifest.json').read_text())['units']
  for unit in self.units:
   code=original[unit['file_start']:unit['file_start']+unit['bytes']] if original else (ROOT/unit['output']).read_bytes()
   assert hashlib.sha256(code).hexdigest()==unit['sha256']
   self.u.mem_write(0x10000+unit['start'],code)
  self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_INTR,self.kernel)
 def word(self,at):return int.from_bytes(self.u.mem_read(DATA+at,2),'little')
 def ret(self,value=0,high=None):
  sp=self.u.reg_read(UC_X86_REG_SP);ip=self.word(sp)
  self.u.reg_write(UC_X86_REG_AX,value&65535)
  if high is not None:self.u.reg_write(UC_X86_REG_DX,high&65535)
  self.u.reg_write(UC_X86_REG_SP,sp+2);self.u.reg_write(UC_X86_REG_IP,ip)
 def hook(self,u,at,size,data):
  self.seen.add(at);sp=u.reg_read(UC_X86_REG_SP)
  args=lambda n:self.word(sp+2*n)
  if at==0x1f800:self.returned=True;u.emu_stop();return
  if any(0x10000+x['start']<=at<0x10000+x['end'] for x in self.units):return
  fn=at-0x10000
  if fn==0xdf04:
   self.reads+=1;self.ret(0x5000 if self.reads==1 else 0x5100)
  elif fn==0x841a:
   assert args(1)==0x5000 and args(2)==(0x4726 if self.kind=='isfile' else 0x779e)
   self.calls.append('open');self.ret(0x6000 if self.opened else 0)
  elif fn==0x8318:
   assert args(1)==0x6000;self.calls.append('close');self.ret(self.closed)
  elif fn==0x853a:
   assert tuple(args(i) for i in range(1,5))==(0x6000,0,0,2)
   self.calls.append('seek');self.ret(self.seek)
  elif fn==0x8ed8:
   assert args(1)==0x6000;self.calls.append('tell');self.ret(self.size,high=self.size>>16)
  elif fn==0xde92:self.calls.append('destination');self.ret(0x5800)
  elif fn==0xdcc1:self.calls.append('discard-destination');self.ret(0xdead,high=0xbeef)
  else:raise AssertionError(('Unexpected boundary',hex(at)))
 def kernel(self,u,n,data):
  assert n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x56
  assert u.reg_read(UC_X86_REG_DX)==0x5000 and u.reg_read(UC_X86_REG_DI)==0x5100
  assert u.reg_read(UC_X86_REG_ES)==0x3000
  self.calls.append('rename');u.reg_write(UC_X86_REG_AX,self.error or 0x5678)
  flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,(flags&~1)|bool(self.error))
 def run(self,kind,opened=True,size=0,error=0,seek=0,closed=0):
  self.kind,self.opened,self.size,self.error,self.seek,self.closed=kind,opened,size,error,seek,closed
  self.seen=set();self.calls=[];self.reads=0;self.returned=False;u=self.u
  before=bytearray((i*37+11)&255 for i in range(65536))
  before[0x5000:0x5006]=b'FIRST\0';before[0x5100:0x5107]=b'SECOND\0'
  before[0x4726:0x4729]=before[0x779e:0x77a1]=b'rb\0'
  before[0x77c8:0x77ca]=(0x3000).to_bytes(2,'little')
  before[0xf000:0xf002]=(0xf800).to_bytes(2,'little')
  u.mem_write(DATA,bytes(before))
  for reg,val in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_ES,0x3000),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)):
   u.reg_write(reg,val)
  start={'isfile':0xe791,'size':0xecfa,'rename':0xe8ce}[kind]
  u.emu_start(0x10000+start,0,count=1000);assert self.returned
  result=(0 if opened else 1) if kind in ('isfile','size') else error
  before[0xd124:0xd126]=result.to_bytes(2,'little')
  if kind=='size' and opened:before[0x5800:0x5804]=(size&0xffffffff).to_bytes(4,'little')
  expected=['rename'] if kind=='rename' else ['open']+(['close'] if kind=='isfile' and opened else ['seek','destination','tell','close'] if kind=='size' and opened else ['discard-destination'] if kind=='size' else [])
  assert self.calls==expected,(kind,self.calls,expected)
  assert self.reads==(2 if kind=='rename' else 1)
  after=bytes(u.mem_read(DATA,65536));assert after[:0xef80]==before[:0xef80] and after[0xf002:]==before[0xf002:]
  assert u.reg_read(UC_X86_REG_SP)==0xf002
  assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI)]==[0xbabe,0x1234,0x5678]
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==u.reg_read(UC_X86_REG_ES)==0x3000
  assert u.reg_read(UC_X86_REG_EFLAGS)&0x400==0
  return result,after[:0xef80],self.calls

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args()
 raw=a.original.read_bytes() if a.original else None
 if raw:assert hashlib.sha256(raw).hexdigest()==json.loads((ROOT/'standalone/fixtures/aspect_file_info_native_units.json').read_text())['original_sha256']
 models=[Machine()]+([Machine(raw)] if raw else []);cases=0;seen=set()
 def case(*args,**kwargs):
  nonlocal cases
  results=[m.run(*args,**kwargs) for m in models];assert all(r==results[0] for r in results)
  seen.update(models[0].seen);cases+=1
 for opened in (False,True):
  for close in (0,1,65535):case('isfile',opened=opened,closed=close)
  for size in (0,1,65535,65536,0x7fffffff,0x80000000,0xffffffff):
   for seek in (0,65535):
    for close in (0,65535):case('size',opened=opened,size=size,seek=seek,closed=close)
 for error in (0,*range(1,256),256,0x7fff,0x8001,0xffff):case('rename',error=error)
 report=dict(passed=True,cases=cases,original_comparisons=cases if raw else 0,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),instruction_addresses=len(seen),scope='Actual recovered handlers/helpers; explicit string/numeric operands, stdio results and DOS21 rename boundary. Complete nonstack data, stack and BP/SI/DI/DS=SS/ES/DF checks. Does not establish real DOS filesystem or application lifetime.')
 (OUT/('native-checks.json' if raw else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n')
 print('ASPECT file info:',cases,'cases,',report['original_comparisons'],'original comparisons PASS')
if __name__=='__main__':main()
