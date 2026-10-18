#!/usr/bin/env python3
"""Replay the linked recovered shape code at its actual INT10 BIOS boundary."""
from pathlib import Path
import hashlib,json
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_BP,UC_X86_REG_SI
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
class Shape(DosImage):
 def __init__(self):
  super().__init__(ROOT/'build/cursor-shape/CURSOR.EXE',ROOT/'build/cursor-shape/cursor-shape.map')
  self.calls=[];self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def interrupt(self,u,n,_):
  assert n==0x10 and u.reg_read(UC_X86_REG_AX)>>8==1,(n,u.reg_read(UC_X86_REG_AX))
  self.calls.append(u.reg_read(UC_X86_REG_CX))
  # The recovered wrapper protects BP around BIOS invocation.
  u.reg_write(UC_X86_REG_BP,0xdead)
 def shape(self,flags):
  self.put('cursor_shape_test_flags',flags);self.call('cursor_shape_test')
  assert self.uc.reg_read(UC_X86_REG_BP)==0xbabe
  assert self.uc.reg_read(UC_X86_REG_SI)==0x1234

def main():
 cases=[]
 def check(name,test):test();cases.append({'case':name,'passed':True});print(name,'passed')
 def flags():
  for flag,start in [(0,0x26),(1,0x26),(2,0x26),(3,0x26),(4,0),(5,14),(6,8),(7,8),(65535,8)]:
   s=Shape();s.shape(flag)
   assert s.calls==[start*256+15],(flag,s.calls)
   assert s.get('cursor_shape_visibility_state')==int(bool(flag&4))
 check('visibility-style-and-halfheight-precedence',flags)
 def scanlines():
  for end in [1,7,13,15,31]:
   for flag,want in [(4,0),(5,end-1),(6,end//2+1)]:
    s=Shape();s.put('cursor_shape_end_scanline',end);s.shape(flag)
    assert s.get('cursor_shape_start_scanline')==want
    assert s.calls==[want*256+end]
 check('configured-font-scanline-shape-calculation',scanlines)
 def gate():
  for state in [2,3,32767]:
   s=Shape();s.put('cursor_shape_visibility_state',state);s.shape(4)
   assert not s.calls and s.get('cursor_shape_start_scanline')==0
   assert s.get('cursor_shape_visibility_state')==state
   s.shape(0);assert s.calls==[0x200f] and s.get('cursor_shape_visibility_state')==0
  for state in [0,1,65535]:
   s=Shape();s.put('cursor_shape_visibility_state',state);s.shape(4)
   assert s.calls==[0x000f] and s.get('cursor_shape_visibility_state')==1
 check('signed-show-suppression-gate-and-unconditional-hide',gate)
 def repeated():
  s=Shape()
  for flags in [4,0,6,0,5,4]:s.shape(flags)
  assert s.calls==[0x000f,0x200f,0x080f,0x280f,0x0e0f,0x000f]
 check('repeated-style-and-visibility-transitions-preserve-bp-si',repeated)
 result={'binary_sha256':hashlib.sha256((ROOT/'build/cursor-shape/CURSOR.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Actual recovered linked instructions through BIOS AH01 boundary; fake BIOS deliberately clobbers BP to verify wrapper restoration. Independent DOSBox test performs actual BIOS set/readback.'}
 (ROOT/'build/cursor-shape/checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
