#!/usr/bin/env python3
"""Exercise linked original scroll logic with an explicit BIOS video model."""
from pathlib import Path
import hashlib,json,struct
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_SI,UC_X86_REG_DI
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
class UnrecoveredService(Exception):pass
class Scroll(DosImage):
 def __init__(self):
  super().__init__(ROOT/'build/scroll/SCROLL.EXE',ROOT/'build/scroll/scroll.map')
  self.calls=[];self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.original=[((i//80)%7+1)*256+(33+i%80) for i in range(2000)]
  self.uc.mem_write(0xb8000,struct.pack('<2000H',*self.original))
 def cells(self):return list(struct.unpack('<2000H',self.uc.mem_read(0xb8000,4000)))
 def interrupt(self,u,n,_):
  if n==3:raise UnrecoveredService(self.get('scroll_unimplemented_service'))
  ax,bx,cx,dx=[u.reg_read(r) for r in [UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX]]
  assert n==0x10,(n,ax)
  if ax>>8==2:return
  assert ax>>8 in (6,7),(n,ax)
  top,left,bottom,right=cx>>8,cx&255,dx>>8,dx&255
  assert 0<=top<=bottom<25 and 0<=left<=right<80,(top,left,bottom,right)
  self.calls.append({'function':ax>>8,'count':ax&255,'attribute':bx>>8,'rectangle':[top,left,bottom,right]})
  old=self.cells();new=old[:];count=ax&255;delta=count if ax>>8==6 else -count
  for row in range(top,bottom+1):
   for col in range(left,right+1):
    source=row+delta
    new[row*80+col]=old[source*80+col] if count and top<=source<=bottom else ((bx>>8)*256+32)
  u.mem_write(0xb8000,struct.pack('<2000H',*new))
 def position(self,row,col):
  self.uc.reg_write(UC_X86_REG_AX,row);self.uc.reg_write(UC_X86_REG_DX,col)
  self.call('screen_set_cursor')
 def rowcol(self):return self.get('screen_cursor_row'),self.get('screen_cursor_column')
 def expected_scroll(self,top,bottom,delta,attribute=7):
  cells=self.original[:]
  for row in range(top,bottom+1):
   for col in range(80):
    source=row+delta
    cells[row*80+col]=self.original[source*80+col] if top<=source<=bottom else attribute*256+32
  return cells

def main():
 cases=[]
 def check(name,test):test();cases.append({'case':name,'passed':True});print(name,'passed')
 def linefeed():
  c=Scroll();c.position(10,20);c.call('screen_linefeed');assert c.rowcol()==(11,20) and not c.calls
  c.call('screen_wrap_forward');assert c.rowcol()==(12,0) and not c.calls
  assert c.get('screen_video_offset')==12*160 and c.get('screen_attribute_offset')==12*80
  c.position(10,20);c.put('scroll_suppress_next_linefeed',1);c.call('screen_linefeed')
  assert c.rowcol()==(10,20) and c.get('scroll_suppress_next_linefeed')==0
 check('linefeed-wrap-and-one-shot-suppression',linefeed)
 def bottom():
  c=Scroll();c.position(24,20);c.call('screen_linefeed')
  assert c.rowcol()==(24,20) and c.cells()==c.expected_scroll(0,24,1)
  c=Scroll();c.position(24,20);c.put('scroll_enabled',0);c.call('screen_linefeed')
  assert c.rowcol()==(24,20) and c.cells()==c.original and not c.calls
  c.put('screen_cursor_wrap',1);c.call('screen_linefeed');assert c.rowcol()==(0,20) and not c.calls
 check('bottom-scroll-disabled-and-wrap-modes',bottom)
 def region():
  for entry,delta,row in [('scroll_index',1,10),('scroll_reverse_index',-1,5)]:
   c=Scroll();c.put('screen_first_row',5);c.put('screen_last_row',10);c.put('csi_erase_attribute',0x1e)
   c.position(row,20);c.call(entry)
   assert c.rowcol()==(row,20) and c.cells()==c.expected_scroll(5,10,delta,0x1e)
   assert c.calls[0]['rectangle']==[5,0,10,79]
  c=Scroll();c.position(10,20);c.call('scroll_reverse_index');assert c.rowcol()==(9,20) and not c.calls
  c.call('scroll_index');assert c.rowcol()==(10,20) and not c.calls
 check('index-reverse-index-with-scroll-region-outside-preservation',region)
 def fills():
  for mono,attribute in [(0,7),(1,0x70)]:
   c=Scroll();c.put('attributes_monochrome',mono);c.put('attributes_current',0x70);c.call('scroll_up')
   assert c.cells()==c.expected_scroll(0,24,1,attribute)
   assert c.get('csi_wrap_pending')==0
 check('scroll-fill-attribute-and-pending-wrap-reset',fills)
 def planes():
  c=Scroll();c.put('screen_cursor_wrap',1);c.put('scroll_skip_attribute_scan',1)
  flags=bytes(i%0x80 for i in range(2000));values=bytes((i%16)+0x20 for i in range(2000))
  f=c.symbols['erase_attribute_flags'];v=c.symbols['erase_attribute_values']
  c.uc.mem_write(f,flags);c.uc.mem_write(v,values);c.call('scroll_up')
  assert c.uc.mem_read(f,2000)==flags[80:]+bytes(80)
  assert c.uc.mem_read(v,2000)==values[80:]+bytes([values[-1]])*80
  assert c.cells()==c.expected_scroll(0,24,1,values[-1])
 check('wrap-mode-attribute-planes-shift-overlap-and-last-row-fill',planes)
 def unresolved():
  c=Scroll();c.put('screen_cursor_wrap',1);c.uc.mem_write(c.symbols['erase_attribute_flags'],b'\x80')
  try:c.call('scroll_up')
  except UnrecoveredService as error:assert error.args==(0x2d98,)
  else:raise AssertionError('Required attribute repair did not trap')
 check('protection-triggered-attribute-repair-remains-explicit',unresolved)
 def width():
  c=Scroll();c.position(10,20);c.uc.mem_write(c.symbols['screen_line_flags']+10,b'\x40');c.put('screen_doublewidth_enabled',1)
  c.call('screen_linefeed');assert c.rowcol()==(11,10)
  assert c.uc.reg_read(UC_X86_REG_SI)==0x1234 and c.uc.reg_read(UC_X86_REG_DI)==0x5678
 check('linefeed-double-width-coordinate-transition-and-abi',width)
 result={'binary_sha256':hashlib.sha256((ROOT/'build/scroll/SCROLL.EXE').read_bytes()).hexdigest(),'cases':cases,'limitations':['Linked CPU replay with explicit INT10 text-video model; separate real DOSBox video-memory checks cover basic scroll/reverse-index/wrap.','Complex attribute repair, viewport services and physical adapters remain unresolved or unvalidated.']}
 (ROOT/'build/scroll/checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
