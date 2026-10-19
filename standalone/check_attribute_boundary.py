#!/usr/bin/env python3
"""Actual boundary, offset conversion and signed divide; cursor/notice models."""
import hashlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/attribute-boundary'
class Machine:
 def __init__(self):
  self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
  proof=json.loads((OUT/'manifest.json').read_text())
  for p,h in proof['sources'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
  for unit in proof['units']:
   b=(OUT/(Path(unit['file']).stem+'.bin')).read_bytes();assert hashlib.sha256(b).hexdigest()==unit['sha256']
   self.u.mem_write(0x10000+unit['start'],b)
  self.u.hook_add(UC_HOOK_CODE,self.hook)
 def put(self,at,n):self.u.mem_write(0x30000+at,struct.pack('<H',n))
 def hook(self,u,at,size,_):
  if at==0x1f000:self.returned=True;u.emu_stop();return
  if at==0x11bbe:self.positions.append((u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX)))
  elif at==0x1376d:self.notices+=1
  else:return
  sp=u.reg_read(UC_X86_REG_SP);ip=int.from_bytes(u.mem_read(0x30000+sp,2),'little');u.reg_write(UC_X86_REG_SP,sp+2);u.reg_write(UC_X86_REG_IP,ip)
 def call(self,at,args):
  u=self.u
  for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_SP,0xe000),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x7200),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,value)
  u.mem_write(0x3e000,struct.pack('<'+'H'*(1+len(args)),0xf000,*args));self.returned=False;self.positions=[];self.notices=0
  u.emu_start(0x10000+at,0,count=200000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==0xe002+len(args)*2
  assert [u.reg_read(r) for r in (UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES)]==[0xbabe,0x1234,0x5678,0x7200]
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x3000
  return u.reg_read(UC_X86_REG_AX)
 def setup(self,cols,n,flags):
  self.u.mem_write(0x30000,bytes(65536));self.put(0x325a,cols);self.put(0x7a72,cols);self.put(0x325c,n);self.put(0x39c4,0x5000);self.u.mem_write(0x35000,bytes(flags))
def main():
 m=Machine();cases=0
 for cols,n in [(1,1),(8,32),(80,2000)]:
  patterns=[bytes(n),bytes([0x81])*n,bytes(0x80 if i%3==0 else 0 for i in range(n)),bytes(1 if i%5 else 2 for i in range(n)),bytes(0x81 if i==0 or i==n-1 else 0 for i in range(n))]
  offsets=range(n) if n<100 else [0,1,2,79,80,81,900,1920,1998,1999]
  for flags,offset,direction in itertools.product(patterns,offsets,(0,1)):
   m.setup(cols,n,flags);value=m.call(0x2adc,(offset,direction))
   if not(flags[offset]&0x81):assert value==0 and m.positions==[] and m.notices==0
   else:
    step=1 if direction else -1
    target=next(((offset+step*j)%n for j in range(1,n+1) if not(flags[(offset+step*j)%n]&0x81)),None)
    if target is None:assert value==0 and m.positions==[(0,0)] and m.notices==1
    else:assert value==1 and m.positions==[divmod(target,cols)] and m.notices==0,(offset,direction,m.positions,target)
   cases+=1
 for enabled,active,left,right,row,col in itertools.product((0,1),(0,1),(0,40),(79,131),(0,3,24),(0,39,40,79,80,131)):
  m.setup(132,3300,bytes(3300));m.put(0xcdfa,enabled);m.put(0x3256,active);m.put(0xce2e,left);m.put(0x7a7e,right);m.put(0x7a72,80)
  m.call(0x2bde,(0xe100,row*132+col))
  # Native inactive viewport compares against uint16(left-1); left0 wraps
  # that threshold toFFFF and classifies every column as hidden.
  visible=not enabled or (col<=right if active else left!=0 and col>=left)
  adjusted=col-left if enabled and not active and visible else col
  expected=(int(visible),row,col,2*(row*(80 if visible else 132)+adjusted))
  got=struct.unpack('<4H',m.u.mem_read(0x3e100,8));assert got==expected,(enabled,active,left,right,row,col,got,expected)
  cases+=1
 report=dict(passed=True,cases=cases,checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest(),original_inputs=[],scope='Actual recovered boundary scanner, offset/viewport coordinate helpers and native signed divide. Circular forward/backward protection search, all-protected notice/home, exact callee cleanup and preserved registers. Cursor positioning and notification are explicit recording models; complete application viewport ownership and physical audio/video remain unverified.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Attribute boundary',cases,'cases PASS')
if __name__=='__main__':main()
