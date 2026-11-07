#!/usr/bin/env python3
"""Replay the exact EMULATE owner; byte-reader and reset are modeled boundaries."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
from build_context_help import ROOT,sha
EXPECTED='e6d7360b2eaabb705a1e28786e80cd5d3c4e5729e5eb7e27e1387087e30536d2'
START=0xe6f1

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False)
 source=ROOT/'src/aspect/emulate_native.asm';binary=out/'emulate.bin'
 subprocess.run(['nasm','-fbin','-DASPECT_EMULATE_FLAT',str(source),'-o',str(binary)],check=True)
 subprocess.run(['nasm','-fobj',str(source),'-o',str(out/'emulate.obj')],check=True)
 assert binary.stat().st_size==15 and sha(binary)==EXPECTED
 if a.original:
  original=a.original.read_bytes();assert hashlib.sha256(original).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
  assert original[118529:118544]==binary.read_bytes()
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x10000+START,binary.read_bytes())
 def word(at):return int.from_bytes(u.mem_read(0x30000+at,2),'little')
 def ret(value):
  sp=u.reg_read(UC_X86_REG_SP);u.reg_write(UC_X86_REG_AX,value);u.reg_write(UC_X86_REG_IP,word(sp));u.reg_write(UC_X86_REG_SP,sp+2)
 state={}
 def hook(u,at,size,unused):
  if at==0x1f800:u.emu_stop();return
  if 0x10000+START<=at<0x10000+START+15:return
  if at==0x14cb4:
   state['events'].append('read');assert word(0x1d18)==0xa55a
   if state['fail']=='read':state['stopped']='read';u.emu_stop();return
   ret(state['selector']);return
  if at==0x120a4:
   state['events'].append('reset');assert word(0x1d18)==state['selector'];assert word(u.reg_read(UC_X86_REG_SP)+2)==1
   if state['fail']=='reset':state['stopped']='reset';u.emu_stop();return
   ret(0x6789);return
  raise AssertionError(hex(at))
 u.hook_add(UC_HOOK_CODE,hook);count=0
 for selector in range(256):
  for fail in ('','read','reset'):
   state.update(selector=selector,fail=fail,events=[],stopped='')
   u.mem_write(0x31d16,b'ZZ\x5a\xa5ZZ');u.mem_write(0x3d000,b'\x00\xf8')
   for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_ES,0x4567),(UC_X86_REG_SP,0xd000),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_EFLAGS,0x202)]:u.reg_write(r,v)
   u.emu_start(0x10000+START,0x20000,count=40)
   assert u.mem_read(0x31d16,2)==b'ZZ' and u.mem_read(0x31d1a,2)==b'ZZ'
   assert word(0x1d18)==(0xa55a if fail=='read' else selector)
   assert state['events']==(['read'] if fail=='read' else ['read','reset'])
   if fail:assert state['stopped']==fail
   else:
    assert u.reg_read(UC_X86_REG_IP)==0xf800 and u.reg_read(UC_X86_REG_SP)==0xd002
    assert u.reg_read(UC_X86_REG_AX)==0x6789 and u.reg_read(UC_X86_REG_BX)==1
   for r,v in [(UC_X86_REG_DS,0x3000),(UC_X86_REG_SS,0x3000),(UC_X86_REG_ES,0x4567),(UC_X86_REG_BP,0xabcd),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert u.reg_read(r)==v
   count+=1
 names=['src/aspect/emulate_native.asm','standalone/check_aspect_emulate.py','standalone/build_context_help.py']
 report=dict(passed=True,cases=count,native_bytes=15,binary_sha256=sha(binary),sources={n:sha(ROOT/n) for n in names},original_inputs=([{'sha256':hashlib.sha256(original).hexdigest(),'range':[118529,118544]}] if a.original else []),optional_original=bool(a.original),scope=__doc__+' All256 byte selectors, read-error and reset-error stops. Direct selector store precedes caller-cleaned reset(1), no native selector bounds check or rollback. DS=SS/stack/callee-saved registers and adjacent state checked. Stops model nonreturning callbacks, not runtime fault recovery. No actual reset/display/parent adoption, opcode binding or physical acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS EMULATE native:',count,'cases,15 exact bytes')
if __name__=='__main__':main()
