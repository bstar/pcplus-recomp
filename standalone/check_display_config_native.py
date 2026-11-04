#!/usr/bin/env python3
"""Recovered ASPECT display fields; operand, destination and error boundaries modeled.
No application key binding, actual PRM, DOS video, bridge or physical acceptance.
"""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
class Native:
 def __init__(self,units):
  self.u=u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
  for entry,data in units.items():u.mem_write(0x10000+entry,data)
  for entry,cleanup in [(0xdd68,4),(0xdc48,0),(0xde3a,2),(0x4efb,2)]:
   u.mem_write(0x10000+entry,b'\xc2'+struct.pack('<H',cleanup) if cleanup else b'\xc3')
  u.hook_add(UC_HOOK_CODE,self.observe)
 def put(self,at,value):self.u.mem_write(0x50000+at,struct.pack('<H',value))
 def word(self,at):return struct.unpack('<H',self.u.mem_read(0x50000+at,2))[0]
 def observe(self,u,at,size,_):
  sp=u.reg_read(UC_X86_REG_SP)
  if at==0x1dd68:
   self.events.append(('bounded',self.word(sp+2),self.word(sp+4)))
   u.reg_write(UC_X86_REG_AX,self.value)
  elif at==0x1dc48:self.events.append(('integer',));u.reg_write(UC_X86_REG_AX,self.value)
  elif at==0x1de3a:self.events.append(('destination',self.word(sp+2)))
  elif at==0x14efb:
   self.events.append(('error',self.word(sp+2)))
   if self.stop_error:self.stopped=True;u.emu_stop()
  elif at==0x1f000:self.returned=True;u.emu_stop()
 def execute(self,entry,value,query=0,error=0,stop_error=False):
  self.value=value;self.events=[];self.returned=self.stopped=False;self.stop_error=stop_error
  self.put(0xe38e,query);self.put(0xe378,error);self.put(0x2070,0xa55a);self.put(0x1d4e,0x5aa5)
  self.put(0xdffe,0xf000);self.u.mem_write(0x5df30,b'GUARD!')
  for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x5000),(UC_X86_REG_SS,0x5000),(UC_X86_REG_SP,0xdffe),
   (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0xcafe),(UC_X86_REG_DI,0xabcd),(UC_X86_REG_EFLAGS,0x202)]:self.u.reg_write(r,v)
  if query:self.put(0x2070,value);self.put(0x1d4e,value)
  self.u.emu_start(0x10000+entry,0,count=300)
  assert self.returned or self.stopped
  assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==0x5000
  if not self.stopped:
   assert self.u.reg_read(UC_X86_REG_SP)==0xe000
   for r,v in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0xcafe),(UC_X86_REG_DI,0xabcd)]:assert self.u.reg_read(r)==v
  assert bytes(self.u.mem_read(0x5df30,6))==b'GUARD!'

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 provenance=json.loads((ROOT/'reconstruction/display_config/provenance.json').read_text());code={}
 original=a.original.read_bytes() if a.original else None
 if original:assert hashlib.sha256(original).hexdigest()==EXPECTED
 for unit in provenance['units']:
  source=ROOT/unit['source'];target=out/(source.stem+'.bin');entry=int(unit['entry'],16)
  subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(target)],check=True)
  assert target.stat().st_size==unit['bytes'] and sha(target)==unit['sha256']
  if original:
   start=int(unit['file_offset'],16);assert target.read_bytes()==original[start:start+unit['bytes']]
  code[entry]=target.read_bytes()
  subprocess.run(['nasm','-fobj','-DDISPLAY_CONFIG_OMF','-I'+str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(out/(source.stem+'.obj'))],check=True)
 m=Native(code);cases=[]
 for error in (0,1):
  for value in range(65536):
   m.execute(0xede7,value,error=error);valid=value in (28,43,50)
   assert m.events==([('integer',)] if valid else [('integer',),('error',1)])
   assert m.word(0x1d4e)==(value if valid or not error else 43) and m.word(0x2070)==0xa55a
  cases.append(dict(case='row-word-sweep-returning-error-boundary',error_flag=error,inputs=65536));print('PASS row word sweep',error,flush=True)
 for value in range(128):
  m.execute(0xedd1,value);assert m.events==[('bounded',127,0)]
  assert m.word(0x2070)==value and m.word(0x1d4e)==0x5aa5
 cases.append(dict(case='video-mode-bounded-operand-contract',inputs=128))
 count=0
 for query in (1,2,0x8000,0xffff):
  for entry in (0xedd1,0xede7):
   for value in (0,1,25,28,43,50,127,128,0x7fff,0x8000,0xffff):
    m.execute(entry,value,query=query);assert m.events==[('destination',value)]
    assert m.word(0x2070)==m.word(0x1d4e)==value;count+=1
 cases.append(dict(case='nonzero-query-mode-preserves-raw-word-and-uses-integer-destination',inputs=count))
 count=0
 for error in (0,1,0x8000,0xffff):
  for value in (0,25,27,29,42,44,49,51,0x8000,0xffff):
   m.execute(0xede7,value,error=error,stop_error=True)
   assert m.stopped and not m.returned and m.word(0x1d4e)==0x5aa5;count+=1
 cases.append(dict(case='nonreturning-error-boundary-prevents-invalid-store',inputs=count))
 result=dict(passed=True,source_only=not bool(original),original_compared=bool(original),native_bytes=sum(len(v) for v in code.values()),cases=cases,
  sources={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'reconstruction/display_config/fields.asm',ROOT/'reconstruction/display_config/video_operand.asm',ROOT/'reconstruction/display_config/provenance.json',ROOT/'reconstruction/uart/encodings.inc']},
  scope=__doc__+' Actual recovered handlers and0..127 operand wrapper execute. Bounded/raw integer readers, integer destination and error services are explicit modeled boundaries. Returning-error and stop-on-error cases are distinct; no complete ASPECT parser or production application behavior claimed.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS display configuration',sum(x['inputs'] for x in cases),flush=True)
if __name__=='__main__':main()
