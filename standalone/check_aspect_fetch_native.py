#!/usr/bin/env python3
"""Actual native FETCH and DD9C/DD68 CPU proof; operand/error/table callbacks explicit."""
import argparse,json,struct,subprocess,re
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from build_aspect_fetch_native import ROOT,OUT,FIXTURE,sha
CODE,DATA=0x10000,0x30000
class Machine:
 def __init__(self,m):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000);self.ranges=[];self.visited=set();self.trace=[];self.selector=0;self.value=0;self.abort=False;self.stopped=False
  for e in m['units']:
   self.u.mem_write(CODE+e['start'],(OUT/e['file']).read_bytes());self.ranges.append((e['start'],e['end']))
  for r,v in [(UC_X86_REG_CS,CODE>>4),(UC_X86_REG_DS,DATA>>4),(UC_X86_REG_SS,DATA>>4)]:self.u.reg_write(r,v)
  for a,v in [(0xe38e,0),(0xe37c,1),(0xe378,0)]:self.put(a,v)
  self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_INTR,self.interrupt)
 def interrupt(self,u,number,user):
  assert number==0x10 and u.reg_read(UC_X86_REG_AH)==3 and u.reg_read(UC_X86_REG_BH)==0
  self.trace.append(('bios_cursor',));u.reg_write(UC_X86_REG_DX,self.value);u.reg_write(UC_X86_REG_CX,0x2607)
 def get(self,a):return struct.unpack('<H',self.u.mem_read(DATA+(a&65535),2))[0]
 def put(self,a,v):self.u.mem_write(DATA+(a&65535),struct.pack('<H',v&65535))
 def ret(self,v=0,n=0):
  sp=self.u.reg_read(UC_X86_REG_SP);self.u.reg_write(UC_X86_REG_AX,v&65535);self.u.reg_write(UC_X86_REG_IP,self.get(sp));self.u.reg_write(UC_X86_REG_SP,sp+2+n)
 def hook(self,u,address,size,user):
  ip=address-CODE
  if ip==0xf000:u.emu_stop();return
  if any(a<=ip<b for a,b in self.ranges):self.visited.add(ip);return
  if ip==0x4cb4:self.trace.append(('selector',self.selector,self.get(0xe38e)));self.ret(self.selector);return
  if ip==0x8123:self.trace.append(('table',self.get(0xe38e)));self.ret(0x5678);return
  if ip==0xdc48:self.trace.append(('integer',self.value));self.ret(self.value);return
  if ip==0x4efb:
   self.trace.append(('error',self.get(u.reg_read(UC_X86_REG_SP)+2)))
   if self.abort:self.stopped=True;u.emu_stop()
   else:self.ret(n=2)
   return
  raise AssertionError(('unexpected native target',hex(ip)))
 def run(self,entry):
  for r,v in [(UC_X86_REG_SP,0x9000),(UC_X86_REG_BP,0x9123),(UC_X86_REG_SI,0x4567),(UC_X86_REG_DI,0x6789),(UC_X86_REG_EFLAGS,0x202)]:self.u.reg_write(r,v)
  self.put(0x9000,0xf000);self.u.emu_start(CODE+entry,CODE+65535,count=1000)
  if not self.stopped:
   assert self.u.reg_read(UC_X86_REG_IP)==0xf000 and self.u.reg_read(UC_X86_REG_SP)==0x9002
   assert self.u.reg_read(UC_X86_REG_BP)==0x9123 and self.u.reg_read(UC_X86_REG_SI)==0x4567 and self.u.reg_read(UC_X86_REG_DI)==0x6789
   assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DATA>>4
  return self.u.reg_read(UC_X86_REG_AX)
def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();m=json.loads((OUT/'manifest.json').read_text());coverage=set();count=0
 for path,h in m['sources'].items():assert sha(ROOT/path)==h,path
 def done(x):
  nonlocal count
  count+=1;coverage.update(x.visited)
 for selector in [*range(256),0x8000,0x7fff,0xffff]:
  x=Machine(m);x.selector=selector;x.put(0x4d24+selector*2,0x8123);result=x.run(0xe660)
  assert x.trace==[('selector',selector,1),('table',1)] and result==0x5678 and x.get(0xe38e)==1;done(x)
 values=[0,1,350,999,32766,32767,32768,32769,65534,65535]+list(range(0,65536,257))
 for value in values:
  for enabled in (0,1):
   for exitstate in (0,1):
    for abort in (False,True):
     x=Machine(m);x.value=value;x.abort=abort;x.put(0xe37c,enabled);x.put(0xe378,exitstate);result=x.run(0xdd9c);invalid=bool(enabled and value>=32768)
     assert x.trace==[('integer',value)]+([('error',1)] if invalid else [])
     assert x.stopped==bool(invalid and abort)
     if not x.stopped:assert result==(0 if invalid and exitstate else value)
     done(x)
 for bios in (0,1,65535):
  for value in (0,1,0x184f,65535):
   x=Machine(m);x.value=value;x.put(0x7a66,bios);x.u.mem_write(0x450,struct.pack('<H',value));result=x.run(0x798e)
   assert result==value and x.trace==([('bios_cursor',)] if bios else [])
   if not bios:assert x.u.reg_read(UC_X86_REG_ES)==0x40
   done(x)
 all_addresses=set()
 for e in m['units']:
  lines=subprocess.check_output(['ndisasm','-b16','-o',str(e['start']),str(OUT/e['file'])],text=True)
  all_addresses.update(int(line.split()[0],16) for line in lines.splitlines() if re.match(r'^[0-9A-F]{8} ',line))
 assert coverage==all_addresses,sorted(all_addresses-coverage)
 original=None
 if a.original:
  b=a.original.read_bytes();assert sha(a.original)==json.loads(FIXTURE.read_text())['original_sha256']
  for e in m['units']:assert b[e['original_file_offset']:e['original_file_offset']+e['length']]==(OUT/e['file']).read_bytes()
  assert struct.unpack_from('<H',b,0x25950+0x4b08+0x37*2)[0]==0xc237
  assert b[0x1200+0xc237:0x1200+0xc237+12]==bytes.fromhex('9aec02ec0a1300ea60e60000')
  original=dict(exact_bytes=sum(e['length'] for e in m['units']),opcode=0x37,overlay=19)
 report=dict(passed=True,cases=count,instruction_addresses=len(coverage),all_native_instructions=len(all_addresses),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),optional_original=original,scope='ActualFETCH18bytes and existingDD9C11/DD6852 source bytes plus26-byte798E cursor reader withactualINT10callback/BDAload. Uncheckedtable indices/EOF and persistentquery1 retained. Returningerror and stoppederror callback models distinguished; no actual productionlongjmp, DOS/UI or completeSETtable claim.')
 (OUT/('checks-native.json' if a.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(count,'FETCH/bounded component cases PASS;',len(coverage),'native instructions')
if __name__=='__main__':main()
