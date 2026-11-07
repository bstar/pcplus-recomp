#!/usr/bin/env python3
"""Exhaustive original 16-bit key dispatch only; no UI, CRT, startup or IO."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_IP
SHA='f079418fca6392cde318e2eb657874a1f5ee10db83616c83054d191441fb6244'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==SHA
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x10000,image[512:]);data=0x13f10;answer=None
 for reg,value in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x13f1),(UC_X86_REG_SS,0x13f1)):u.reg_write(reg,value)
 def word(at):return struct.unpack('<H',u.mem_read(data+at,2))[0]
 def hook(cpu,at,size,_):
  nonlocal answer
  if at==0x10f47:
   sp=cpu.reg_read(UC_X86_REG_SP);cpu.reg_write(UC_X86_REG_IP,word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2);return
  if at==0x108a2:answer=word(0x1992)
  elif at==0x1078c:
   profile=word(0x10c4);assert profile in (5,7);answer=79 if profile==7 else 80
  elif at==0x10fb5:answer=81
  elif at==0x10970:answer=82
  elif at==0x1080f:answer=83
  elif at==0x10e4d:answer=84
  elif at==0x11041:answer=85 if word(cpu.reg_read(UC_X86_REG_SP)+2)==0x1372 else 86
  elif at==0x10f3c:
   sp=cpu.reg_read(UC_X86_REG_SP);cpu.reg_write(UC_X86_REG_IP,word(sp));cpu.reg_write(UC_X86_REG_SP,sp+2);return
  else:return
  cpu.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook);values=[]
 for key in range(65536):
  answer=None;u.reg_write(UC_X86_REG_SP,0xf000);u.reg_write(UC_X86_REG_AX,key);u.mem_write(data+0x10c4,b'\x06\0')
  u.emu_start(0x103e0,0x20000,count=500);assert answer is not None,(key,hex(u.reg_read(UC_X86_REG_IP)));values.append(answer)
 runs=[];start=0
 for i in range(1,65537):
  if i==65536 or values[i]!=values[start]:runs.append([start,i,values[start]]);start=i
 result=dict(passed=True,format='keymap-dispatch-ranges-v1',original_sha256=SHA,cases=65536,sha256=hashlib.sha256(bytes(values)).hexdigest(),ranges=runs,REA_evidence='ev_36c92a6dbffeb28bf009a0e80b57cb2e21c2d857cb2fa286f036ce18277ef5aa',limitations=['Actual original branch instructions from CS:03E0; stop at slot/action boundary.','Save prompt and bell are modeled no-op returns; UI, file actions and startup not executed.','Profile wrap at0/32 is separate from this profile6 dispatch observation.'])
 assert set(range(79)).issubset(values);assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS 65536 original dispatch cases;',len(runs),'ranges')
if __name__=='__main__':main()
