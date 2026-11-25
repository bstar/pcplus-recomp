#!/usr/bin/env python3
"""Retained REDIAL selection-list codec CPU checks.

Executes src/aspect/redial_selection_store.asm (transient PCCONN codec) and
the initial value of src/terminal/redial_selection_storage.asm (resident owner)
under Unicorn 16-bit mode and
compares it with the native overlay-5 slot semantics: fifteen 7-byte slots,
5 token bytes, byte 5 always 0 and a 0/1 consumed flag. Every reachable native
state must round-trip byte for byte through the 77-byte retained form;
unreachable states and a corrupt retained mask must be refused (CF=1) without
writing the destination. Reads no original executable.
"""
import random
import subprocess
import tempfile
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,
 UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_IP,UC_X86_REG_EFLAGS,
 UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX)

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'src/aspect/redial_selection_store.asm'
STORAGE=ROOT/'src/terminal/redial_selection_storage.asm'
SLOTS,SLOT,TOKEN=15,7,5
NATIVE,RETAINED=SLOTS*SLOT,SLOTS*TOKEN+2
CS,DS,ES,SS=0x1000,0x2000,0x3000,0x4000
STOP=0xfff0
SRC,DST=0x0100,0x0400
CF,DF=1,0x400


def assemble(*defines,source=None):
 with tempfile.TemporaryDirectory() as tmp:
  out=Path(tmp)/'out'
  fmt=['-fbin','-DREDIAL_SELECTION_FLAT'] if not defines else list(defines)
  subprocess.run(['nasm',*fmt,str(source or SOURCE),'-o',str(out)],check=True)
  return out.read_bytes()


def pack_ref(native):
 out=bytearray();mask=0
 for i in range(SLOTS):
  slot=native[i*SLOT:(i+1)*SLOT]
  if slot[5]!=0 or slot[6]>1:return None
  out+=slot[:TOKEN];mask|=slot[6]<<i
 return bytes(out+mask.to_bytes(2,'little'))


def unpack_ref(retained):
 mask=int.from_bytes(retained[-2:],'little')
 if mask&0x8000:return None
 return b''.join(retained[i*TOKEN:(i+1)*TOKEN]+bytes([0,(mask>>i)&1]) for i in range(SLOTS))


class Cpu:
 def __init__(self,image):
  self.uc=Uc(UC_ARCH_X86,UC_MODE_16);self.uc.mem_map(0,0x100000)
  self.uc.mem_write(CS*16,image);self.uc.mem_write(CS*16+STOP,b'\xf4')
  self.pack,self.unpack=(int.from_bytes(image[i:i+2],'little') for i in (0,2))
 def call(self,entry,src,dst_fill,df):
  uc=self.uc
  uc.mem_write(DS*16+SRC,src);uc.mem_write(ES*16+DST,dst_fill)
  for reg,val in ((UC_X86_REG_CS,CS),(UC_X86_REG_DS,DS),(UC_X86_REG_ES,ES),(UC_X86_REG_SS,SS),
   (UC_X86_REG_SP,0xfffe),(UC_X86_REG_BP,0x5a5a),(UC_X86_REG_SI,SRC),(UC_X86_REG_DI,DST),
   (UC_X86_REG_EFLAGS,0x0002|(DF if df else 0)|CF)):uc.reg_write(reg,val)
  uc.mem_write(SS*16+0xfffc,STOP.to_bytes(2,'little'));uc.reg_write(UC_X86_REG_SP,0xfffc)
  uc.emu_start(CS*16+entry,CS*16+STOP,count=20000)
  assert uc.reg_read(UC_X86_REG_IP)==STOP
  assert uc.reg_read(UC_X86_REG_SP)==0xfffe
  for reg,val in ((UC_X86_REG_SI,SRC),(UC_X86_REG_DI,DST),(UC_X86_REG_BP,0x5a5a),
   (UC_X86_REG_DS,DS),(UC_X86_REG_ES,ES),(UC_X86_REG_SS,SS)):assert uc.reg_read(reg)==val
  carry=bool(uc.reg_read(UC_X86_REG_EFLAGS)&CF)
  return carry,bytes(uc.mem_read(ES*16+DST,len(dst_fill)))


def reachable(rng):
 out=bytearray()
 for _ in range(SLOTS):
  kind=rng.randrange(4)
  if kind==0:tok=bytes(5)
  elif kind==1:tok=bytes(rng.choice(b'0123456789') for _ in range(rng.randrange(1,6)))
  else:tok=bytes(rng.randrange(256) for _ in range(5))
  out+=tok.ljust(5,b'\0')+bytes([0,rng.randrange(2)])
 return bytes(out)


def main():
 image=assemble();cpu=Cpu(image)
 initial=assemble(source=STORAGE);assert len(initial)==RETAINED
 dgroup=bytes([0,0,0,0,0,0,1])*SLOTS
 assert unpack_ref(initial)==dgroup and pack_ref(dgroup)==initial
 carry,out=cpu.call(cpu.unpack,initial,bytes([0xcc])*NATIVE,True)
 assert not carry and out==dgroup
 rng=random.Random(0x70b4);cases=0
 for n in range(3000):
  native=reachable(rng);df=bool(n&1)
  carry,packed=cpu.call(cpu.pack,native,bytes([0xcc])*RETAINED,df)
  assert not carry and packed==pack_ref(native),n
  carry,back=cpu.call(cpu.unpack,packed,bytes([0xcc])*NATIVE,not df)
  assert not carry and back==native,n
  cases+=1
 refused=0
 for n in range(1000):
  native=bytearray(reachable(rng));i=rng.randrange(SLOTS)
  if n&1:native[i*SLOT+5]=rng.randrange(1,256)
  else:native[i*SLOT+6]=rng.randrange(2,256)
  fill=bytes(rng.randrange(256) for _ in range(RETAINED))
  carry,out=cpu.call(cpu.pack,bytes(native),fill,bool(n&2))
  assert carry and out==fill and pack_ref(bytes(native)) is None,n
  retained=bytearray(pack_ref(reachable(rng)));retained[-1]|=0x80
  fill=bytes(rng.randrange(256) for _ in range(NATIVE))
  carry,out=cpu.call(cpu.unpack,bytes(retained),fill,bool(n&2))
  assert carry and out==fill,n
  refused+=2
 code=len(image)-4
 assert b'_TEXT' in assemble('-fobj') and b'REDIAL_STORAGE' in assemble('-fobj',source=STORAGE)
 print(f'redial selection store: transient code={code} bytes resident owner={RETAINED} bytes '
  f'(paragraph {(RETAINED+15)//16*16}) native={NATIVE}; round-trips={cases} refusals={refused}: OK')


if __name__=='__main__':main()
