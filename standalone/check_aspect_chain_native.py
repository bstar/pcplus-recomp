#!/usr/bin/env python3
"""Native EXECUTE/restart/reset proof; loader, allocator, operand and UI models explicit."""
import argparse,json,struct,subprocess,re
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from build_aspect_chain_native import ROOT,OUT,FIXTURE,sha
CODE,DATA=0x10000,0x30000
class Machine:
 def __init__(self,m):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000);self.u.mem_write(DATA,b'\xa5'*65536);self.ranges=[];self.visited=set();self.trace=[];self.abort=None;self.filename=b'NEXT.ASX';self.temporary=False;self.fill=False;self.reader_abort=False;self.load_result=1;self.allocate_abort=False;self.lifecycle=False;self.file=0;self.fail_second=False;self.closes=[];self.frees=[]
  for e in m['units']+m['helpers']:
   self.u.mem_write(CODE+e['start'],(OUT/e['file']).read_bytes());self.ranges.append((e['start'],e['end']))
  for r,v in [(UC_X86_REG_CS,CODE>>4),(UC_X86_REG_DS,DATA>>4),(UC_X86_REG_SS,DATA>>4)]:self.u.reg_write(r,v)
  for a,v in [(0xe106,0),(0xe104,0xdd88),(0xe378,0),(0xe382,0),(0x8e20,0)]:self.put(a,v)
  for a in range(0xe39e,0xe3aa,2):self.put(a,0)
  for a in range(0xe108,0xe114,2):self.put(a,0)
  self.u.hook_add(UC_HOOK_CODE,self.hook)
 def get(self,a):return struct.unpack('<H',self.u.mem_read(DATA+(a&65535),2))[0]
 def put(self,a,v):self.u.mem_write(DATA+(a&65535),struct.pack('<H',v&65535))
 def arg(self,n):return self.get(self.u.reg_read(UC_X86_REG_SP)+2+n*2)
 def text(self,a):return bytes(self.u.mem_read(DATA+a,256)).split(b'\0',1)[0]
 def string(self,a,b):self.u.mem_write(DATA+a,b+b'\0')
 def ret(self,v=0,n=0):
  sp=self.u.reg_read(UC_X86_REG_SP);self.u.reg_write(UC_X86_REG_AX,v&65535);self.u.reg_write(UC_X86_REG_IP,self.get(sp));self.u.reg_write(UC_X86_REG_SP,sp+2+n)
 def hook(self,u,address,size,user):
  ip=address-CODE
  if ip==0xf000:u.emu_stop();return
  if ip==0xe712 and self.fill:self.string(u.reg_read(UC_X86_REG_AX),self.filename);self.fill=False
  if any(a<=ip<b for a,b in self.ranges):self.visited.add(ip);return
  if ip==0xdf04:
   self.trace.append(('string',))
   if self.reader_abort:self.abort='reader';u.emu_stop();return
   if self.temporary:self.fill=True;u.reg_write(UC_X86_REG_IP,0xdfc7)
   else:self.string(0x1100,self.filename);self.ret(0x1100)
   return
  if ip==0xd4d0:
   owner,name=self.arg(0),self.arg(1);self.trace.append(('load',owner,name,self.text(name)))
   self.file+=1;value=0 if self.fail_second and self.file==2 else self.load_result
   if value:self.put(0x4b02,0x4000+self.file*16)
   self.ret(value,4);return
  if ip==0xd850:
   self.trace.append(('allocate',))
   if self.allocate_abort:self.abort='allocation';u.emu_stop()
   else:self.ret()
   return
  if ip==0x6dca:self.trace.append(('cursor',));self.ret();return
  if ip==0x8318:self.closes.append(self.arg(0));self.trace.append(('close',self.arg(0)));self.ret();return
  if ip==0x85fc:self.frees.append((self.arg(0),self.arg(1)));self.trace.append(('free',*self.frees[-1]));self.ret();return
  if ip==0x2fb8:self.trace.append(('status',));self.ret();return
  if self.lifecycle:
   if ip==0xc1d7:self.trace.append(('initialize',));self.ret();return
   if ip==0xc21f:u.reg_write(UC_X86_REG_IP,0xd770);return
   if ip==0xc273:u.reg_write(UC_X86_REG_IP,0xd804);return
   if ip==0x9048:self.trace.append(('probe',));self.ret();return
   if ip==0x4de9:self.ret();return
   if ip==0x4cb4:self.ret(0xcb if self.file==1 else 0x33);return
   if ip==0x8123:self.put(0xe378,1);self.ret();return
   if ip==0xc2eb:self.trace.append(('per_file_cleanup',self.file,self.get(0xe104),self.text(self.get(0xe104))));self.ret();return
   if ip==0x4bff:self.trace.append(('shutdown',));self.ret();return
  raise AssertionError(('unexpected native target',hex(ip)))
 def run(self,entry,args=(),cleanup=0):
  for r,v in [(UC_X86_REG_SP,0x9000),(UC_X86_REG_BP,0x9123),(UC_X86_REG_SI,0x4567),(UC_X86_REG_DI,0x6789),(UC_X86_REG_EFLAGS,0x202)]:self.u.reg_write(r,v)
  self.put(0x9000,0xf000)
  for i,v in enumerate(args):self.put(0x9002+i*2,v)
  self.u.emu_start(CODE+entry,CODE+65535,count=10000)
  if not self.abort:
   assert self.u.reg_read(UC_X86_REG_IP)==0xf000 and self.u.reg_read(UC_X86_REG_SP)==0x9002+cleanup
   assert self.u.reg_read(UC_X86_REG_BP)==0x9123 and self.u.reg_read(UC_X86_REG_SI)==0x4567 and self.u.reg_read(UC_X86_REG_DI)==0x6789
   assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DATA>>4
  return self.u.reg_read(UC_X86_REG_AX)
def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();m=json.loads((OUT/'manifest.json').read_text());count=0;coverage=set()
 for path,h in m['sources'].items():assert sha(ROOT/path)==h,path
 def done(x):
  nonlocal count
  count+=1;coverage.update(x.visited)
 for temporary in (False,True):
  for index in range(11):
   for length in (0,1,8,12,80):
    x=Machine(m);x.temporary=temporary;x.filename=b'N'*length;x.put(0xe106,index);x.run(0xe709)
    first=0xdd88+index*81;latest=0xdd88+((index+int(temporary))%11)*81
    assert x.text(first)==x.filename and x.text(x.get(0xe104))==x.filename and x.get(0xe104)==latest
    assert x.get(0xe378)==999 and x.get(0xe106)==(index+1+int(temporary))%11;done(x)
 x=Machine(m);x.reader_abort=True;x.put(0xe378,7);x.run(0xe709);assert x.abort=='reader' and x.get(0xe378)==7;done(x)
 cleared=[0xe390,0xe38c,0xe37a,0xe320,0xe2fa,0xe2f8,0xe378,0xdd86,0xe2fc,0xe308,0xe314,0xe1f4,0xe24a,0xe2a0]
 retained=[0xe392,0xe394,0xe396,0xe398,0xe37e,0xe380,0xe39a,0xe39c,0xe322,0xe374,0xe376,0x397a,0xcffa,0xd482,0xd582,0xe1a0,0xe1ca,0xe2a2,0xe37c,0x1d28]
 for owner in (0,1,65535):
  for gate in (0,1,2,65535):
   for success in (0,1):
    x=Machine(m);x.put(0xe382,gate);x.load_result=success;x.string(0x1000,b'NEXT.ASX');before={k:x.get(k) for k in retained};result=x.run(0xd770,(owner,0x1000),4)
    assert result==success and all(x.get(k)==0 for k in cleared)
    assert x.get(0xe13a)==x.get(0xe13c)==0xab7c and x.get(0xe382)==(gate+1+int(bool(owner)))%65536
    assert x.get(0xe106)==0 and x.get(0xe104)==0xdd88 and all(x.get(k)==v for k,v in before.items())
    assert [t[0] for t in x.trace]==['load']+(['allocate'] if success else [])+['cursor'];done(x)
 x=Machine(m);x.allocate_abort=True;x.put(0xe382,4);x.string(0x1000,b'NEXT');x.run(0xd770,(0,0x1000),4)
 assert x.abort=='allocation' and x.get(0xe382)==4 and x.get(0xe104)==0xdd88;done(x)
 for mask in range(64):
  x=Machine(m)
  for i in range(6):x.put(0xe39e+i*2,0x5000+i if mask&(1<<i) else 0)
  for i in range(3):x.put(0xe108+i*4,0x6000+i if mask&(1<<i) else 0);x.put(0xe10a+i*4,0x7000+i if mask&(1<<i) else 0)
  x.run(0xd804);assert x.closes==[0x5000+i for i in range(6) if mask&(1<<i)] and x.frees==[(0x6000+i,0x7000+i) for i in range(3) if mask&(1<<i)]
  assert x.get(0x4b02)==x.get(0x4b00)==0
  # Native finish does not clear the handle/pointer records: a second call repeats release.
  before=x.closes[:],x.frees[:];x.run(0xd804);assert x.closes==before[0]*2 and x.frees==before[1]*2;done(x)
 for owner in (0,1):
  for temporary in (False,True):
   for fail in (False,True):
    x=Machine(m);x.lifecycle=True;x.temporary=temporary;x.fail_second=fail;x.string(0x1000,b'FIRST.ASX');x.put(0x4b08+0xcb*2,0xe709);x.put(0x4b08+0x33*2,0x8123);x.run(0x4b1f,(owner,0x1000),4)
    loads=[t for t in x.trace if t[0]=='load'];assert len(loads)==2 and loads[0][1]==owner and loads[1][1]==0 and loads[1][3]==b'NEXT.ASX'
    assert len([t for t in x.trace if t[0]=='initialize'])==1 and len([t for t in x.trace if t[0]=='probe'])==2
    assert len([t for t in x.trace if t[0]=='per_file_cleanup'])==(1 if fail else 2)
    assert x.get(0xe378)==(0 if fail else 1);done(x)
 all_addresses=set()
 for e in m['units']:
  lines=subprocess.check_output(['ndisasm','-b16','-o',str(e['start']),str(OUT/e['file'])],text=True)
  all_addresses.update(int(line.split()[0],16) for line in lines.splitlines() if re.match(r'^[0-9A-F]{8} ',line))
 assert all_addresses<=coverage,sorted(all_addresses-coverage)
 original=None
 if a.original:
  b=a.original.read_bytes();assert sha(a.original)==json.loads(FIXTURE.read_text())['original_sha256']
  for e in m['units']:assert b[e['original_file_offset']:e['original_file_offset']+e['length']]==(OUT/e['file']).read_bytes()
  assert struct.unpack_from('<H',b,0x25950+0x4b08+0xcb*2)[0]==0xc13b
  assert b[0x1200+0xc13b:0x1200+0xc13b+12]==bytes.fromhex('9aec02ec0a1200ea09e70000')
  original=dict(exact_bytes=sum(e['length'] for e in m['units']),opcode=0xcb,overlay=18)
 report=dict(passed=True,cases=count,owner_native_instructions=len(all_addresses),visited_addresses=len(coverage),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),optional_original=original,scope='Actual248native command/open/final bytes plus actualscratch/strcpy/dispatcher instructions. Initializer, stringreader, fullfilename/compile/openloader, globalallocator/release, FILE andUI remain explicitmodels. No actualDOS/fullVM/nonlocalerror or safe malformedinputclaim.')
 (OUT/('checks-native.json' if a.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(count,'nativeCHAIN cases PASS;',len(all_addresses),'ownerinstructions')
if __name__=='__main__':main()
