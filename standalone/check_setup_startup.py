#!/usr/bin/env python3
"""Linked pre-connect setup ABI and status gates; actual DOS EXEC is separate."""
import hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import UC_X86_INS_IN,UC_X86_INS_OUT,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/terminal/TERMINAL.EXE';MAP=ROOT/'build/terminal/terminal.map';OUT=ROOT/'build/setup-startup'
class Model(DosImage):
 def __init__(self,status=0,child_status=0,path=b'TEST.PRM',enabled=True):
  super().__init__(BINARY,MAP);self.calls=0;self.status=status;self.child_status=child_status;self.path=path
  self.put('terminal_option_mask',8208 if enabled else 16)
  self.uc.mem_write(self.symbols['terminal_config_path'],path+b'\0'*(64-len(path)))
  self.uc.reg_write(UC_X86_REG_ES,0x3333)
  self.uc.mem_write(self.symbols['_process_run'],b'\xb8'+struct.pack('<H',status)+b'\xc3')
  self.uc.hook_add(UC_HOOK_CODE,self.exec_stub,begin=self.symbols['_process_run'],end=self.symbols['_process_run'])
  self.uc.hook_add(UC_HOOK_INTR,self.forbid)
  for ins in (UC_X86_INS_IN,UC_X86_INS_OUT):self.uc.hook_add(UC_HOOK_INSN,self.forbid,None,1,0,ins)
 def forbid(self,*args):raise AssertionError('Setup scheduler attempted interrupt or UART IO outside mocked EXEC')
 def string(self,ptr,limit=64):
  raw=bytes(self.uc.mem_read(self.data_base+ptr,limit));assert b'\0' in raw;return raw.split(b'\0')[0]
 def exec_stub(self,uc,address,size,_):
  self.calls+=1;sp=uc.reg_read(UC_X86_REG_SP)
  path,tail,result=struct.unpack('<3H',uc.mem_read(self.data_base+sp+2,6))
  assert self.string(path)==b'PRMEDIT.EXE'
  assert self.string(tail)==b' '+self.path
  assert result==self.offset('setup_startup_result')
  uc.mem_write(self.data_base+result,struct.pack('<4H',self.status,5 if self.status else 0,self.child_status,9011))
 def run(self):
  value=self.call('terminal_run_startup_setup',limit=10000)
  for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x3333)]:assert self.uc.reg_read(reg)==want
  return value

def main():
 cases=[]
 for status in range(7):
  for child in [0,1,9,255,256,511]:
   m=Model(status,child);assert m.run()==(0 if not status and not child else 11) and m.calls==1
 cases.append({'case':'all-process-statuses-and-normal-abnormal-child-exits','inputs':42,'passed':True})
 for path in [b'A',b'A.PRM',b'12345678.PRM']:
  m=Model(path=path);assert m.run()==0 and m.calls==1
 cases.append({'case':'direct-tail-argument-order-bounded-copy-and-preserved-callee-registers','inputs':3,'passed':True})
 m=Model(path=b'X'*64);assert m.run()==11 and m.calls==0
 m=Model(enabled=False);assert m.run()==0 and m.calls==0
 cases.append({'case':'unterminated-path-guard-and-disabled-option-no-EXEC','inputs':2,'passed':True})
 result={'passed':True,'cases':cases,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['src/terminal/setup_startup.asm','standalone/check_setup_startup.py','standalone/dos_image.py']},'scope':'Actual linked 8086 setup scheduler with mocked EXEC only; all interrupts/IN/OUT forbidden. Tests near-cdecl arguments, status gate, caller cleanup and callee registers. Actual editor/EXEC/serial and startup ordering are checked by the separate DOS suite.'}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'linked.json').write_text(json.dumps(result,indent=2)+'\n');print('Linked setup scheduler passed 47 inputs')
if __name__=='__main__':main()
