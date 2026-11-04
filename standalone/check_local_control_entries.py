#!/usr/bin/env python3
"""Source-only local control entry proof, with optional genuine original bytes."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import *
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--original',type=Path);a=p.parse_args()
a.output=a.output.resolve();assert a.output.is_relative_to(ROOT/'build') and not a.output.exists();a.output.mkdir(parents=True)
original=a.original.read_bytes() if a.original else None
if original:assert hashlib.sha256(original).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
units=[]
for name,entry,size in [('reset',0x1368,11),('duplex',0x3316,13)]:
 source=ROOT/'reconstruction/local_controls'/(name+'.asm');binary=a.output/(name+'.bin')
 subprocess.run(['nasm','-fbin','-DRECON_FLAT',str(source),'-o',str(binary)],check=True);code=binary.read_bytes();assert len(code)==size
 if original:assert code==original[0x1200+entry:0x1200+entry+size]
 checks=0
 for value in ([0] if name=='reset' else list(range(256))+[0x7fff,0x8000,0xfffe,0xffff]):
  u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000);u.mem_write(0x10000+entry,code);u.mem_write(0x51d1a,struct.pack('<H',value));u.mem_write(0x5effe,struct.pack('<H',0xf000));u.mem_write(0x120a4,b'\xc3')
  for reg,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x5000),(UC_X86_REG_SS,0x5000),(UC_X86_REG_SP,0xeffe)]:u.reg_write(reg,v)
  hits=[]
  def observe(u,address,size,_):
   if address==0x120a4:
    sp=u.reg_read(UC_X86_REG_SP);assert struct.unpack('<H',u.mem_read(0x50000+sp+2,2))[0]==1
    hits.append(address) # declared reset service boundary, not a full reset proof
   if address==0x1f000:u.emu_stop()
  u.hook_add(UC_HOOK_CODE,observe);u.emu_start(0x10000+entry,0,count=100)
  assert u.reg_read(UC_X86_REG_SP)==0xf000 and u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==0x5000
  if name=='reset':assert hits==[0x120a4]
  else:assert struct.unpack('<H',u.mem_read(0x51d1a,2))[0]==int(value==0)
  checks+=1
 units.append(dict(name=name,entry=hex(entry),bytes=size,sha256=hashlib.sha256(code).hexdigest(),cases=checks))
r=dict(passed=True,units=units,original_compared=original is not None,sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('standalone/check_local_control_entries.py','reconstruction/local_controls/reset.asm','reconstruction/local_controls/duplex.asm')},scope='Actual recovered entry instructions and stack/data ABI; reset callee is an explicit modeled boundary. No UI integration, full reset semantics, BBS, DOS or hardware acceptance.')
(a.output/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS local Reset/Duplex native entries:',sum(x['cases'] for x in units),'cases')
