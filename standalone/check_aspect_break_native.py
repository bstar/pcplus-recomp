#!/usr/bin/env python3
"""Execute exact native BREAK source with declared hardware/screen/operand callbacks."""
import argparse,json,struct,subprocess,re
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from build_aspect_break_native import ROOT,OUT,FIXTURE,sha
CODE,DATA=0x10000,0x30000
class Machine:
 def __init__(self,m):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000);self.ranges=[];self.visited=set();self.trace=[];self.value=0;self.stop=None;self.fault=None;self.lcr=3;self.cursor=0x1234;self.query=[]
  for e in m['units']:
   self.u.mem_write(CODE+e['start'],(OUT/e['file']).read_bytes());self.ranges.append((e['start'],e['end']))
  for r,v in [(UC_X86_REG_CS,CODE>>4),(UC_X86_REG_DS,DATA>>4),(UC_X86_REG_SS,DATA>>4)]:self.u.reg_write(r,v)
  for a,v in [(0x7a36,0x7a38),(0x7a38,0),(0x2074,0x4300),(0x8fee,0x3fb),(0x3250,4000),(0x7a84,0xb800),(0x7a82,0),(0x1f6e,0x1f20),(0x1d46,0),(0xe38e,0),(0x1d28,350)]:self.put(a,v)
  self.u.hook_add(UC_HOOK_CODE,self.hook)
 def get(self,a):return struct.unpack('<H',self.u.mem_read(DATA+(a&65535),2))[0]
 def put(self,a,v):self.u.mem_write(DATA+(a&65535),struct.pack('<H',v&65535))
 def arg(self,n):return self.get(self.u.reg_read(UC_X86_REG_SP)+2+n*2)
 def ret(self,value=0,cleanup=0):
  sp=self.u.reg_read(UC_X86_REG_SP);self.u.reg_write(UC_X86_REG_AX,value&65535);self.u.reg_write(UC_X86_REG_IP,self.get(sp));self.u.reg_write(UC_X86_REG_SP,sp+2+cleanup)
 def event(self,name,*args):
  self.trace.append((name,*args))
  if name==self.fault:self.stop=name;self.u.emu_stop();return False
  return True
 def hook(self,u,address,size,user):
  ip=address-CODE
  if ip==0xf000:u.emu_stop();return
  if any(a<=ip<b for a,b in self.ranges):self.visited.add(ip);return
  if ip==0x798e:self.event('cursor_read');self.ret(self.cursor);return
  if ip==0x6e78:self.event('cursor_write',self.arg(0));self.ret(0,2);return
  if ip==0x829a:
   if self.event('in',self.arg(0)):self.ret(self.lcr)
   return
  if ip==0x82a8:
   if self.event('out',self.arg(0),self.arg(1)):self.lcr=self.arg(1);self.ret()
   return
  if ip==0x6b72:
   if self.event('delay',self.arg(0)):self.ret(0,2)
   return
  if ip==0x2fb8:self.event('status');self.ret();return
  if ip in (0x765c,0x6c20,0x6bf0,0x7682):
   self.event({0x765c:'save',0x6c20:'fill',0x6bf0:'text',0x7682:'restore'}[ip],self.arg(0),self.arg(1),self.arg(2));self.ret(0,6);return
  if ip==0x6b98:self.event('wait',self.arg(0));self.ret(0,2);return
  if ip==0xdd9c:
   self.event('operand',self.value)
   if not 0<=self.value<=32767:self.stop='bounded-operand';u.emu_stop()
   else:self.ret(self.value)
   return
  if ip==0xde3a:self.query.append(self.arg(0));self.event('store',self.arg(0));self.ret(0,2);return
  raise AssertionError(hex(ip))
 def run(self,entry,args=()):
  for r,v in [(UC_X86_REG_SP,0x9000),(UC_X86_REG_BP,0x9123),(UC_X86_REG_SI,0x4567),(UC_X86_REG_DI,0x6789),(UC_X86_REG_EFLAGS,0x202)]:self.u.reg_write(r,v)
  self.put(0x9000,0xf000)
  for i,v in enumerate(args):self.put(0x9002+i*2,v)
  self.u.emu_start(CODE+entry,CODE+65535,count=5000)
  if not self.stop:
   assert self.u.reg_read(UC_X86_REG_IP)==0xf000 and self.u.reg_read(UC_X86_REG_SP)==0x9002
   assert self.u.reg_read(UC_X86_REG_BP)==0x9123 and self.u.reg_read(UC_X86_REG_SI)==0x4567 and self.u.reg_read(UC_X86_REG_DI)==0x6789
   assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==DATA>>4

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();m=json.loads((OUT/'manifest.json').read_text());coverage=set();count=0
 for path,h in m['sources'].items():assert sha(ROOT/path)==h,path
 def done(x):
  nonlocal count
  count+=1;coverage.update(x.visited)
 for lcr in range(256):
  for delay in (0,1,350,32767,65535):
   for disabled in (0,1):
    x=Machine(m);x.lcr=lcr;x.put(0x1d28,delay);x.put(0x1d46,disabled);x.run(0xe67b)
    names=[t[0] for t in x.trace];assert names==(['cursor_read']+([] if disabled else ['save','fill','text'])+['in','out','delay','out','cursor_write','status'])
    assert [t for t in x.trace if t[0]=='out']==[('out',0x3fb,lcr|64),('out',0x3fb,lcr&191)]
    assert ('delay',delay) in x.trace and ('cursor_write',0x1234) in x.trace and x.get(0x7a36)==0x7a38
    if not disabled:assert ('text',0x4300,0x1f20,0xbfa9) in x.trace
    done(x)
 for mode in (0,1,65535):
  for value in (0,1,32767,32768,65535):
   x=Machine(m);x.value=value;x.put(0xe38e,mode);x.put(0x1d28,0xabcd);x.run(0xe8a7)
   if mode:assert x.query==[0xabcd] and x.get(0x1d28)==0xabcd
   elif value<=32767:assert x.get(0x1d28)==value
   else:assert x.stop=='bounded-operand' and x.get(0x1d28)==0xabcd
   done(x)
 for cursor in (0x7a38,0x7a4c):
  x=Machine(m);x.put(0x7a36,cursor);x.run(0x6b5a);assert x.get(cursor)==0x1234 and x.get(0x7a36)==min(cursor+2,0x7a4c);done(x)
 # Literal native memory comparison aliases the first saved cursor, not a guarded floor.
 for current,first,expected in [(0x7a3a,0x1234,0x7a38),(0x7a3a,0x7a3a,0x7a3a),(0x7a38,0,0x7a36),(0x7a4c,0,0x7a4a)]:
  x=Machine(m);x.put(0x7a36,current);x.put(0x7a38,first);x.run(0x6b42);assert x.get(0x7a36)==expected and ('cursor_write',x.get(expected)) in x.trace;done(x)
 for ticks in (0,1,65535):
  x=Machine(m);x.run(0x31bb,(0x4300,ticks));assert ('wait',ticks) in x.trace if ticks else not any(t[0]=='wait' for t in x.trace)
  assert any(t[0]=='restore' for t in x.trace)==bool(ticks);done(x)
 x=Machine(m);x.lcr=3;x.fault='delay';x.run(0xe67b);assert x.lcr==67 and not any(t[0] in ('status','cursor_write') for t in x.trace);done(x)
 original=None
 if a.original:
  b=a.original.read_bytes();assert sha(a.original)==json.loads(FIXTURE.read_text())['original_sha256']
  for e in m['units']:assert b[e['original_file_offset']:e['original_file_offset']+e['length']]==(OUT/e['file']).read_bytes()
  table=struct.unpack_from('<215H',b,0x25950+0x4b08);assert table[13]==0xca53
  assert b[0x1200+0xca53:0x1200+0xca53+12]==bytes.fromhex('9aec02ec0a1200ea7be60000')
  assert struct.unpack_from('<H',b,0x25950+0x4d24+18)[0]==0xc5f7
  assert b[0x1200+0xc5f7:0x1200+0xc5f7+12]==bytes.fromhex('9aec02ec0a1300eaa7e80000')
  assert struct.unpack_from('<H',b,0x25950+0x1d28)[0]==350
  original=dict(exact_bytes=sum(e['length'] for e in m['units']),dispatch_opcode=13,setting_selector=9,default_raw_units=350)
 all_addresses=set()
 for e in m['units']:
  listing=subprocess.check_output(['ndisasm','-b16','-o',str(e['start']),str(OUT/e['file'])],text=True)
  all_addresses.update(int(line.split()[0],16) for line in listing.splitlines() if re.match(r'^[0-9A-F]{8} ',line))
 assert coverage==all_addresses,('uncovered native instructions',sorted(all_addresses-coverage))
 report=dict(passed=True,cases=count,instruction_addresses=len(coverage),all_native_instructions=len(all_addresses),coverage=sorted(coverage),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),optional_original=original,scope='Actual249native source bytes. Hardware I/O, calibrated delay, cursor BIOS/video, screen services, bounded operand and status refresh are declared synchronous component callbacks. Fault callback stop proves missing native cleanup; no actual DOS, physical duration, maintained child integration or notice pointer initialization claim.')
 (OUT/('checks-native.json' if a.original else 'checks.json')).write_text(json.dumps(report,indent=2)+'\n');print(count,'native BREAK component cases PASS;',len(coverage),'instruction addresses')
if __name__=='__main__':main()
