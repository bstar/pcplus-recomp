#!/usr/bin/env python3
"""Compare linked original path helper with unmodified-original CPU execution."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def run(code,offset,ds,path,fail):
 u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
 u.mem_write(0x10000+offset,code)
 u.mem_write(ds*16+0x200,path+b'\0'*4)
 u.mem_write(ds*16+0xe000,struct.pack('<HH',0xf000,0x200))
 initial={UC_X86_REG_CS:0x1000,UC_X86_REG_DS:ds,UC_X86_REG_SS:ds,
  UC_X86_REG_SP:0xe000,UC_X86_REG_AX:0xabcd,UC_X86_REG_BX:0xbcde,
  UC_X86_REG_CX:0x1234,UC_X86_REG_DX:0x2345,UC_X86_REG_SI:0x3456,
  UC_X86_REG_DI:0x4567,UC_X86_REG_BP:0x5678,UC_X86_REG_ES:0x6789,
  UC_X86_REG_EFLAGS:0x602}
 for reg,value in initial.items():u.reg_write(reg,value)
 calls=[];returned=[]
 def interrupt(u,n,_):
  assert n==0x21
  ax=u.reg_read(UC_X86_REG_AX)
  if ax>>8==0x3b:
   at=u.reg_read(UC_X86_REG_DS)*16+u.reg_read(UC_X86_REG_DX)
   text=bytes(u.mem_read(at,128)).split(b'\0',1)[0]
   calls.append(('CHDIR',text.hex(),fail));u.reg_write(UC_X86_REG_AX,3 if fail else 0)
   flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,(flags|1) if fail else (flags&~1))
  else:
   assert ax>>8==0x0e
   calls.append(('SELECT',u.reg_read(UC_X86_REG_DX)&255));u.reg_write(UC_X86_REG_AX,0x0e1a)
 def stop(u,at,size,_):
  if at==0x1f000:returned.append(True);u.emu_stop()
 u.hook_add(UC_HOOK_INTR,interrupt);u.hook_add(UC_HOOK_CODE,stop)
 u.emu_start(0x10000+offset,0,count=500)
 assert returned and u.reg_read(UC_X86_REG_SP)==0xe004
 for reg in (UC_X86_REG_CX,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_BP,UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES):
  assert u.reg_read(reg)==initial[reg]
 return calls,tuple(u.reg_read(r) for r in initial)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('program','original','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 proof=json.loads((ROOT/'reconstruction/file_path/provenance.json').read_text());assert sha(a.original)==proof['source_sha256']
 original=a.original.read_bytes()[proof['file_offset']:proof['file_offset']+proof['bytes']]
 image=DosImage(a.program,a.program.with_name('PATH.map'))
 linked=bytes(image.uc.mem_read(image.symbols['file_path_native_change'],proof['bytes']))
 assert hashlib.sha256(linked).hexdigest()==proof['sha256'] and linked==original
 cases=0
 paths=[bytes([lead])+suffix for lead in range(256) for suffix in (b'',b':',b':\\X')]
 paths += [b'',b'.',b'..',b'C:\\ONE',b'c:SUB',b'Y:',b'\\ONE',b'A'*63]
 for offset,ds in [(0x400,0x4000),(0x2111,0x5400)]:
  for fail in (False,True):
   for path in paths:
    expected=run(original,proof['start'],ds,path,fail)
    actual=run(linked,offset,ds,path,fail)
    assert expected==actual,(offset,ds,path,fail)
    cases+=1
 r={'passed':True,'paired_cases':cases,'original_sha256':sha(a.original),'program_sha256':sha(a.program),
  'native_sha256':proof['sha256'],'native_bytes':proof['bytes'],'checker_sha256':sha(Path(__file__)),
  'scope':__doc__+' Complete modeled DOS-call sequence, registers/FLAGS and callee-clean stack across two code/data placements. Not original UI or actual DOS mutation semantics.'}
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS original path helper:',cases,'paired cases')

if __name__=='__main__':main()
