#!/usr/bin/env python3
"""Execute recovered reverse Tab with explicitly modeled external services."""
import hashlib,itertools,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/keyboard-reverse-tab'
class Machine:
 def __init__(self):
  self.uc=Uc(UC_ARCH_X86,UC_MODE_16);self.uc.mem_map(0,0x100000)
  self.uc.mem_write(0x10000+0xbc0,(OUT/'reverse_tab.bin').read_bytes())
  self.uc.mem_write(0x10000+0x1e30,(OUT/'left-oracle.bin').read_bytes())
  self.uc.hook_add(UC_HOOK_CODE,self.hook)
 def get(self,at):return int.from_bytes(self.uc.mem_read(0x30000+at,2),'little')
 def put(self,at,n):self.uc.mem_write(0x30000+at,struct.pack('<H',n))
 def ret(self,cleanup=0):
  u=self.uc;sp=u.reg_read(UC_X86_REG_SP);ip=int.from_bytes(u.mem_read(0x30000+sp,2),'little');u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ip)
 def pos(self,row,col):
  self.put(0x399c,row);self.put(0x399e,col);self.put(0x3346,row*80+col)
 def hook(self,u,at,size,_):
  if at==0x10000+0xf000:self.returned=True;u.emu_stop();return
  ip=at-0x10000
  if ip not in (0x1e30,0x1ea0,0x1bbe,0x2adc,0x830c,0x1f56):return
  self.trace.append(ip);row,col=self.get(0x399c),self.get(0x399e)
  if ip==0x1e30 and self.real_left:return
  if ip==0x1bbe:self.pos(u.reg_read(UC_X86_REG_AX),u.reg_read(UC_X86_REG_DX))
  elif ip==0x1e30:
   if col:self.pos(row,col-1)
   elif self.get(0x900c) and (row or not self.get(0x9038)):self.pos((row-1)%25,79)
  elif ip==0x1ea0:self.pos(row,min(col+1,79))
  elif ip==0x1f56:self.pos(0,0)
  elif ip==0x830c:
   sp=u.reg_read(UC_X86_REG_SP);num,den=struct.unpack('<HH',u.mem_read(0x30000+sp+2,4));q,r=divmod(num,den);u.reg_write(UC_X86_REG_AX,q);u.reg_write(UC_X86_REG_DX,r)
  self.ret(4 if ip==0x2adc else 0)
 def run(self,col,stops,flags=(0,0,0),protected=False,blocked=False,attr=(),wrap=True,require_return=True,real_left=False):
  u=self.uc;self.real_left=real_left;u.mem_write(0x30000,bytes(65536));self.pos(1,col)
  for at,value in zip((0x903e,0x904c,0x8ff8),flags):self.put(at,value)
  self.put(0x9038,int(blocked));self.put(0x325a,80);self.put(0x39c4,0x5000)
  self.put(0x900c,int(wrap));self.put(0x3734,int(protected))
  for at in attr:u.mem_write(0x30000+0x5000+at,b'\x81')
  assert len(stops)<30;u.mem_write(0x30000+0xce10,bytes(stops)+b'\xfe'*(30-len(stops)))
  for reg,n in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_IP,0xbc0),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_SP,0xe000),(UC_X86_REG_SI,0x1234),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_ES,0x7200),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(reg,n)
  u.mem_write(0x3e000,struct.pack('<H',0xf000));self.trace=[];self.returned=False
  u.emu_start(0x10bc0,0,count=20000)
  if not require_return:
   assert not self.returned
   return None,self.trace
  assert self.returned and u.reg_read(UC_X86_REG_SP)==0xe002
  assert u.reg_read(UC_X86_REG_SI)==0x1234 and u.reg_read(UC_X86_REG_BP)==0xbabe
  assert u.reg_read(UC_X86_REG_ES)==0x7200
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x3000
  return (self.get(0x399c),self.get(0x399e)),self.trace

def main():
 proof=json.loads((OUT/'manifest.json').read_text());assert proof['passed']
 assert hashlib.sha256((OUT/'reverse_tab.bin').read_bytes()).hexdigest()==proof['binary_sha256']
 assert hashlib.sha256((OUT/'left-oracle.bin').read_bytes()).hexdigest()==proof['left_oracle_sha256']
 for p,h in proof['sources'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
 m=Machine();cases=0
 tables=[[],[0],[3],[0,8,16,24,32,40,48,56,64,72],[2,7,9,30,78],list(range(0,29))]
 for stops,col,flags in itertools.product(tables,range(80),itertools.product((0,1),repeat=3)):
  want=next((v for v in reversed(stops) if v<col),None)
  # Native empty-table modes can suppress homing altogether. A populated table
  # with no previous stop falls back to column0, independent of these modes.
  expected=(1,col if not stops and any(flags) else (want if want is not None else 0))
  if stops and col==0 and (flags[0] or flags[1]):expected=(0,max(v for v in stops if v<79))
  got,trace=m.run(col,stops,flags);assert got==expected,(stops,col,flags,got,expected)
  assert trace in ([],[0x1bbe],[0x1e30,0x1bbe]);cases+=1
 for col in (1,8,20,79):
  got,trace=m.run(col,[0,8,16],protected=True,attr=[80])
  expected=[0x1e30]+([0x2adc] if col==1 else [])+[0x830c,0x1bbe,0x1ea0]
  assert got==(1,1) and trace==expected,(got,trace)
  cases+=1
 _,trace=m.run(0,[0,8],flags=(1,0,0),wrap=False,require_return=False,real_left=True)
 assert trace.count(0x1e30)>100 and set(trace)=={0x1e30,0x1bbe};cases+=1
 # Controlled attribute repair and protected-home callback boundaries.
 got,trace=m.run(1,[],protected=True)
 assert got==(0,0) and trace==[0x1e30,0x1f56];cases+=1
 result=dict(passed=True,cases=cases,binary_sha256=proof['binary_sha256'],checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),original_inputs=[],scope='Actual recovered226-byte instructions, six valid FE-terminated tab tables,80 columns, all eight tab-mode combinations, protected attribute search and native stack/SI/DS=SS checks. Cursor/attribute repair/division/protected-home services are declared scalar models; no video, DOS hardware or application integration claim.')
 result['native_recursion_counterexample']=dict(passed=True,real_recovered_cursor_left=True,tab_wrap=1,cursor_wrap=0,column=0,stops=[0,8],instruction_limit=20000,returned=False,scope='Actual reverse-tab and cursor-left instructions. Screen-set-cursor is the declared scalar model; preserves row1/column0 in this case. Characterizes inherited recursion, not a safety fix.')
 result['manifest_sha256']=hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest()
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Reverse Tab',cases,'cases PASS')
if __name__=='__main__':main()
