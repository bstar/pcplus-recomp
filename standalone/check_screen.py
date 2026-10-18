#!/usr/bin/env python3
"""Replay linked recovered cursor instructions and real BIOS/CRTC boundaries."""
from pathlib import Path
import hashlib,json,struct
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_INS_OUT
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
class UnrecoveredService(Exception):pass
class Cursor(DosImage):
 def __init__(self):
  super().__init__(ROOT/'build/screen/SCREEN.EXE',ROOT/'build/screen/screen.map')
  self.positions=[];self.ports=[]
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.uc.hook_add(UC_HOOK_INSN,lambda u,p,s,v,x:self.ports.append((p,s,v)),None,1,0,UC_X86_INS_OUT)
 def interrupt(self,u,n,_):
  if n==3:raise UnrecoveredService('unrecovered viewport/attribute/wrap service reached')
  assert n==0x10 and u.reg_read(UC_X86_REG_AX)>>8==2,(n,hex(u.reg_read(UC_X86_REG_AX)))
  self.positions.append(u.reg_read(UC_X86_REG_DX))
 def position(self,row,col):
  self.uc.reg_write(UC_X86_REG_AX,row);self.uc.reg_write(UC_X86_REG_DX,col)
  self.call('screen_set_cursor')
  assert self.get('screen_cursor_row')==row and self.get('screen_cursor_column')==col
  assert self.uc.reg_read(UC_X86_REG_SI)==0x1234 and self.uc.reg_read(UC_X86_REG_DI)==0x5678
 def rowcol(self):return self.get('screen_cursor_row'),self.get('screen_cursor_column')
 def flags(self,row,value):self.uc.mem_write(self.symbols['screen_line_flags']+row,bytes([value]))

def main():
 cases=[]
 def check(name,test):test();cases.append({'case':name,'passed':True});print(name,'passed')
 def absolute():
  c=Cursor()
  for row,col in [(10,20),(10,21),(5,0),(0,79),(24,79),(0,0)]:
   c.position(row,col)
   assert c.get('screen_video_offset')==row*160+col*2
   assert c.get('screen_attribute_offset')==row*80+col
   assert c.positions[-1]==row*256+col
 check('absolute-and-relative-buffer-offsets-with-bios-position',absolute)
 def movement():
  c=Cursor();c.position(10,20)
  for call,want in [('right',(10,21)),('down',(11,21)),('left',(11,20)),('up',(10,20))]:
   c.call('screen_cursor_'+call);assert c.rowcol()==want
  c.position(0,0);c.call('screen_cursor_left');c.call('screen_cursor_up');assert c.rowcol()==(0,0)
  c.position(24,79);c.call('screen_cursor_right');c.call('screen_cursor_down');assert c.rowcol()==(24,79)
  c.put('screen_top_margin',5);c.put('screen_bottom_margin',15)
  c.position(5,10);c.call('screen_cursor_up');assert c.rowcol()==(5,10)
  c.position(15,10);c.call('screen_cursor_down');assert c.rowcol()==(15,10)
 check('single-step-directions-and-configured-margins',movement)
 def width():
  c=Cursor();c.flags(10,0x40);c.position(10,20)
  c.call('screen_cursor_right');assert c.rowcol()==(10,22)
  c.call('screen_cursor_left');assert c.rowcol()==(10,20)
  c.position(10,78);c.call('screen_cursor_right');assert c.rowcol()==(10,78)
  c.put('screen_doublewidth_enabled',1);c.flags(11,0)
  c.position(10,20);c.call('screen_cursor_down');assert c.rowcol()==(11,10)
  c.call('screen_cursor_up');assert c.rowcol()==(10,20)
 check('double-width-row-steps-and-width-transitions',width)
 def inherited_underflow():
  c=Cursor();c.flags(10,0x40);c.position(10,1);c.call('screen_cursor_left')
  assert c.rowcol()==(10,65535)
  # This is inherited behavior requiring caller alignment or a deliberate fix.
 check('original-double-width-odd-column-underflow-characterized',inherited_underflow)
 def wrap():
  c=Cursor();c.put('screen_cursor_wrap',1);c.position(0,20);c.call('screen_cursor_up');assert c.rowcol()==(24,20)
  c.position(10,0);c.call('screen_cursor_left');assert c.rowcol()==(9,79)
  c.position(0,0);c.call('screen_cursor_left');assert c.rowcol()==(24,79)
  c.put('screen_reverse_wrap_blocked',1);c.position(0,0);c.call('screen_cursor_left');assert c.rowcol()==(0,0)
  c.position(10,79)
  try:c.call('screen_cursor_right')
  except UnrecoveredService:pass
  else:raise AssertionError('forward wrap must reach an explicit unresolved service')
 check('reverse-wrap-and-forward-wrap-dependency',wrap)
 def viewport():
  c=Cursor();c.put('screen_viewport_enabled',1);c.put('screen_viewport_left',40)
  try:c.position(10,20)
  except UnrecoveredService:pass
  else:raise AssertionError('viewport service unexpectedly hidden')
 check('horizontal-viewport-boundary-remains-explicit',viewport)
 def crtc():
  c=Cursor();c.put('screen_use_bios_cursor',0)
  c.uc.mem_write(0x463,struct.pack('<H',0x3d4));c.uc.mem_write(0x44e,b'\0\0')
  c.position(10,20)
  assert c.uc.mem_read(0x450,2)==struct.pack('<H',0x0a14)
  assert c.ports==[(0x3d4,1,14),(0x3d5,1,3),(0x3d4,1,15),(0x3d5,1,0x34)],c.ports
  assert c.positions==[]
 check('direct-crtc-output-and-bios-data-area',crtc)
 result={'binary_sha256':hashlib.sha256((ROOT/'build/screen/SCREEN.EXE').read_bytes()).hexdigest(),'cases':cases,'limitations':['CPU replay of linked source-built DOS diagnostic; physical video hardware not tested.','Forward wrap, viewport manipulation, and attribute-boundary correction are unresolved dependencies and trap.','Odd-column double-width left underflow is characterized, not fixed or declared valid.']}
 (ROOT/'build/screen/checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
