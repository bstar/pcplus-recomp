#!/usr/bin/env python3
"""Actual native end-drain and mapped receive composition with device callbacks."""
import argparse,json,struct,subprocess,re
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from build_aspect_end_wait_native import ROOT,OUT,FIXTURE,sha
CODE,DATA=0x10000,0x30000
class Machine:
 def __init__(self,m):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000);self.ranges=[];self.visited=set();self.trace=[];self.queue=[];self.delays=[];self.reads=0;self.key_after=65535;self.bursts={};self.emitted=[];self.stop_emit=False;self.stopped=False
  for e in [m['unit'],*m['helpers']]:
   self.u.mem_write(CODE+e['start'],(OUT/e['file']).read_bytes());self.ranges.append((e['start'],e['end']))
  for r,v in [(UC_X86_REG_CS,CODE>>4),(UC_X86_REG_DS,DATA>>4),(UC_X86_REG_SS,DATA>>4)]:self.u.reg_write(r,v)
  self.u.mem_write(DATA+0xd00a,bytes((i+1)%256 for i in range(256)))
  for a,v in [(0x8e20,0),(0xe2f8,3),(0xe37e,0),(0xe2fa,1),(0xe382,7),(0xe39a,0x1234)]:self.put(a,v)
  self.u.hook_add(UC_HOOK_CODE,self.hook)
 def get(self,a):return struct.unpack('<H',self.u.mem_read(DATA+a,2))[0]
 def put(self,a,v):self.u.mem_write(DATA+a,struct.pack('<H',v&65535))
 def arg(self,n):return self.get(self.u.reg_read(UC_X86_REG_SP)+2+n*2)
 def ret(self,v=0,n=0):
  sp=self.u.reg_read(UC_X86_REG_SP);self.u.reg_write(UC_X86_REG_AX,v&65535);self.u.reg_write(UC_X86_REG_IP,self.get(sp));self.u.reg_write(UC_X86_REG_SP,sp+2+n)
 def hook(self,u,address,size,user):
  ip=address-CODE
  if ip==0xf000:u.emu_stop();return
  if any(a<=ip<b for a,b in self.ranges):self.visited.add(ip);return
  if ip==0x6b72:
   amount=self.arg(0);self.delays.append(amount);self.trace.append(('delay',amount));self.queue.extend(self.bursts.pop(len(self.delays),[]));self.put(0x8e20,len(self.queue));self.ret(n=2);return
  if ip==0xaa65:
   assert self.queue;v=self.queue.pop(0);self.reads+=1;self.put(0x8e20,len(self.queue));self.trace.append(('raw',v));self.ret(v);return
  if ip==0x0610:
   self.emitted.append(self.arg(0));self.trace.append(('emit',self.arg(0)))
   if self.stop_emit:self.stopped=True;u.emu_stop()
   else:self.ret()
   return
  if ip==0x651a:self.trace.append(('key',));self.ret(0x1e61 if self.reads>=self.key_after else 0);return
  raise AssertionError(('unexpected native service',hex(ip)))
 def run(self):
  self.put(0x8e20,len(self.queue));self.put(0x9000,0xf000)
  for r,v in [(UC_X86_REG_SP,0x9000),(UC_X86_REG_BP,0x9123),(UC_X86_REG_SI,0x4567),(UC_X86_REG_DI,0x6789),(UC_X86_REG_EFLAGS,0x202)]:self.u.reg_write(r,v)
  self.u.emu_start(CODE+0x4bff,CODE+65535,count=10000)
  if not self.stopped:
   assert self.u.reg_read(UC_X86_REG_IP)==0xf000 and self.u.reg_read(UC_X86_REG_SP)==0x9002
   assert self.u.reg_read(UC_X86_REG_BP)==0x9123 and self.u.reg_read(UC_X86_REG_SI)==0x4567 and self.u.reg_read(UC_X86_REG_DI)==0x6789
   assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DATA>>4
  assert self.get(0xe2fa)==1 and self.get(0xe382)==7 and self.get(0xe39a)==0x1234

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();m=json.loads((OUT/'manifest.json').read_text());count=0;coverage=set()
 for path,h in m['sources'].items():assert sha(ROOT/path)==h,path
 def done(x):
  nonlocal count
  count+=1;coverage.update(x.visited)
 for n in range(9):
  for display in (0,1,65535):
   for patterns in (0,3):
    for key in (0,1,2,65535):
     x=Machine(m);x.queue=list(range(n));x.key_after=key;x.put(0xe37e,display);x.put(0xe2f8,patterns);x.run()
     expected=0 if not n else min(n,max(1,key))
     assert x.reads==expected and x.emitted==list(range(1,expected+1))
     assert x.delays==[50]+([15] if n and expected==n else [])
     assert x.get(0xe37e)==(1 if n else display) and x.get(0xe2f8)==(0 if n else patterns)
     assert len([t for t in x.trace if t[0]=='key'])==(max(0,expected-1)+(1 if expected<n else 0));done(x)
 for bursts in ({1:[65]},{2:[66]},{1:[65],2:[66],3:[67]}):
  x=Machine(m);x.queue=[] if 1 in bursts else [65];x.bursts=dict(bursts);x.run();assert x.emitted==[66]+([67] if 2 in bursts else [])+([68] if 3 in bursts else []);assert x.delays[0]==50 and all(t==15 for t in x.delays[1:]);done(x)
 x=Machine(m);x.queue=[255,0xffff,65];x.run();assert x.emitted==[0,66] and x.reads==3;done(x)
 x=Machine(m);x.queue=[65,66];x.stop_emit=True;x.run();assert x.stopped and x.emitted==[66] and x.queue==[66] and x.get(0xe2f8)==0 and x.get(0xe37e)==1;done(x)
 owner=m['unit'];listing=subprocess.check_output(['ndisasm','-b16','-o',str(owner['start']),str(OUT/owner['file'])],text=True);native=set(int(line.split()[0],16) for line in listing.splitlines() if re.match(r'^[0-9A-F]{8} ',line));assert native<=coverage,sorted(native-coverage)
 original=None
 if a.original:
  b=a.original.read_bytes();assert sha(a.original)==json.loads(FIXTURE.read_text())['original_sha256'];assert b[owner['original_file_offset']:owner['original_file_offset']+owner['length']]==(OUT/owner['file']).read_bytes()
  for e in m['helpers']:assert b[0x1200+e['start']:0x1200+e['end']]==(OUT/e['file']).read_bytes()
  original=dict(owner_bytes=owner['length'],composed_bytes=owner['length']+sum(e['end']-e['start'] for e in m['helpers']))
 report=dict(passed=True,cases=count,owner_instructions=len(native),visited_addresses=len(coverage),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),optional_original=original,scope='Actual61nativeendwaitbytes +actual4C3C/4C74mappedreceive; controlledrawUART,calibrateddelayarrival,keyboardpeekandrendereremitcallbacks. No fullrenderer,physicaltiming,DOSexecution,cancellationunwindorboundedschedulingclaim.')
 (OUT/('checks-native.json' if a.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(count,'nativeendwaitcases PASS;',len(native),'ownerinstructions')
if __name__=='__main__':main()
