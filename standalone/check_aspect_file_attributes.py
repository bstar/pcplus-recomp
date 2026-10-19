#!/usr/bin/env python3
"""Native attribute command/helper replay with explicit DOS21/operand boundaries."""
import argparse,hashlib,json
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from check_aspect_enumeration import Machine as EnumerationMachine,DATA
from build_aspect_file_attributes import ROOT,OUT,sha
class Machine(EnumerationMachine):
 def __init__(self,original=None):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  self.units=json.loads((OUT/'manifest.json').read_text())['units']
  for unit in self.units:
   code=original[unit['file_start']:unit['file_start']+unit['bytes']] if original else (ROOT/unit['output']).read_bytes()
   assert hashlib.sha256(code).hexdigest()==unit['sha256'];self.u.mem_write(0x10000+unit['start'],code)
  self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_INTR,self.kernel)
 def kernel(self,u,n,data):
  assert n==0x21;function=u.reg_read(UC_X86_REG_AX)
  assert function==(0x4300 if self.kind in ('get','read') else 0x4301)
  assert self.string(u.reg_read(UC_X86_REG_DX))==b'OWNED.DAT'
  if function==0x4300:u.reg_write(UC_X86_REG_CX,self.attribute)
  else:assert u.reg_read(UC_X86_REG_CX)==self.mask
  self.kernel_calls.append((function,self.mask))
  u.reg_write(UC_X86_REG_AX,self.error or 0x8888)
  flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,(flags&~1)|bool(self.error))
 def run(self,kind,*,attribute=0,error=0,attrs=b'R',mask=0):
  self.kind,self.attribute,self.error=kind,attribute,error
  self.mask=mask if kind=='write' else sum(bit for letter,bit in ((b'R',1),(b'H',2),(b'S',4),(b'A',32)) if letter in attrs.upper())
  self.seen=set();self.warnings=[];self.kernel_calls=[];self.operands=[0x5000,0x5100];self.returned=False
  u=self.u;before=bytearray((i*37+11)&255 for i in range(65536))
  before[0x5000:0x500a]=b'OWNED.DAT\0'
  before[0x5100:0x5100+len(attrs)+1]=attrs+b'\0'
  before[0x7caf:0x7daf]=bytes(2 if 97<=i<=122 else 0 for i in range(256))
  u.mem_write(DATA,bytes(before));self.put(0xf000,0xf800)
  args=[0x5000] if kind=='read' else [0x5000,mask] if kind=='write' else []
  for i,v in enumerate(args):self.put(0xf002+i*2,v)
  for reg,val in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_ES,0x3000),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)):
   u.reg_write(reg,val)
  start={'get':0xed45,'set':0xed69,'read':0xf311,'write':0xf323}[kind]
  u.emu_start(0x10000+start,0,count=10000);assert self.returned
  expected=(65535 if error else attribute) if kind=='read' else error if kind in ('set','write') else int(bool(error) or attribute==65535)
  assert u.reg_read(UC_X86_REG_AX)==expected
  if kind in ('get','set'):before[0xd124:0xd126]=expected.to_bytes(2,'little')
  if kind=='get':
   bits=65535 if error else attribute
   value=b''.join(c for c,bit in ((b'R',1),(b'H',2),(b'S',4),(b'A',32),(b'D',16),(b'V',8)) if bits&bit)
   before[0x5100:0x5100+len(value)+1]=value+b'\0'
   assert not self.warnings and not self.operands
  elif kind=='set':
   assert self.warnings==[0 for c in attrs.upper() if c not in b'RHSA']
   assert not self.operands
  assert len(self.kernel_calls)==1
  after=bytes(u.mem_read(DATA,65536));assert after[:0xef00]==before[:0xef00] and after[0xf006:]==before[0xf006:]
  assert u.reg_read(UC_X86_REG_SP)==0xf002
  assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI)]==[0xbabe,0x1234,0x5678]
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x3000 and not u.reg_read(UC_X86_REG_EFLAGS)&0x400
  return after[:0xef00],self.kernel_calls,self.warnings

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);args=p.parse_args();raw=args.original.read_bytes() if args.original else None
 if raw:assert hashlib.sha256(raw).hexdigest()==json.loads((ROOT/'standalone/fixtures/aspect_file_attributes_native_units.json').read_text())['original_sha256']
 models=[Machine()]+([Machine(raw)] if raw else []);count=0;seen=set()
 def case(kind,**kwargs):
  nonlocal count
  results=[m.run(kind,**kwargs) for m in models];assert all(r==results[0] for r in results);count+=1;seen.update(models[0].seen)
 for attribute in (*range(256),0x100,0x8000,0xffff):
  case('get',attribute=attribute);case('read',attribute=attribute)
 for error in (*range(256),0x100,0x8001,0xffff):
  case('get',attribute=0x20,error=error);case('set',attrs=b'rhsa',error=error)
 for mask in range(16):
  attrs=bytes(c for i,c in enumerate(b'RHSA') if mask&(1<<i));case('set',attrs=attrs)
 for attrs in (b'RRHhSsAA',b'RH?SA',b'D',b'V',b'R'*80):case('set',attrs=attrs)
 for mask in (0,1,0x20,0x3f,0x1234,0xffff):
  for error in (0,2,5,0xffff):case('write',mask=mask,error=error)
 for unit in models[0].units:assert 0x10000+unit['start'] in seen
 report=dict(passed=True,cases=count,original_comparisons=count if raw else 0,checker_sha256=sha(Path(__file__)),manifest_sha256=sha(OUT/'manifest.json'),instruction_addresses=len(seen),reused_checker_sha256=sha(ROOT/'standalone/check_aspect_enumeration.py'),scope='Actual100 native command/DOS helper bytes and203 reused parser/formatter bytes; typed string and kernel return boundaries explicit. All8-bit attrs/errors,wide sentinel/error words,mask combinations,returning-warning behavior,complete nonstack data/stack/register/DS=SS/DF checks and optional actual-original replay. GET near destination fixture does not establish far global writeback; production adaptation and real DOS are separate.')
 (OUT/('native-checks.json' if raw else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print('Native file attributes:',count,'cases,',report['original_comparisons'],'original comparisons PASS')
if __name__=='__main__':main()
