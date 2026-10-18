#!/usr/bin/env python3
"""Exercise linked original erase logic with an explicit BIOS video model."""
from pathlib import Path
import hashlib,json,struct
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
class UnrecoveredService(Exception):pass
class Erase(DosImage):
 def __init__(self):
  super().__init__(ROOT/'build/erase/ERASE.EXE',ROOT/'build/erase/erase.map')
  self.calls=[];self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.original=[((i//80)%7+1)*256+(33+i%80) for i in range(2000)]
  self.uc.mem_write(0xb8000,struct.pack('<2000H',*self.original))
 def cells(self):return list(struct.unpack('<2000H',self.uc.mem_read(0xb8000,4000)))
 def interrupt(self,u,n,_):
  if n==3:raise UnrecoveredService('complex protected erase/attribute repair not recovered')
  ax,bx,cx,dx=[u.reg_read(r) for r in [UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX]]
  assert n==0x10 and ax>>8 in (6,7),(n,ax)
  top,left,bottom,right=cx>>8,cx&255,dx>>8,dx&255
  assert 0<=top<=bottom<25 and 0<=left<=right<80,(top,left,bottom,right)
  self.calls.append({'function':ax>>8,'count':ax&255,'attribute':bx>>8,'rectangle':[top,left,bottom,right]})
  old=self.cells();new=old[:];count=ax&255;delta=count if ax>>8==6 else -count
  for row in range(top,bottom+1):
   for col in range(left,right+1):
    source=row+delta
    new[row*80+col]=old[source*80+col] if count and top<=source<=bottom else ((bx>>8)*256+32)
  u.mem_write(0xb8000,struct.pack('<2000H',*new))
 def rectangle(self,top,left,bottom,right,count=0,attribute=7):
  for name,value in [('top',top*256+left),('bottom',bottom*256+right),('scroll',count&65535),('attribute',attribute)]:self.put('erase_test_'+name,value)
  self.call('erase_test_rectangle')
 def assert_clear(self,predicate,attr=7):
  assert self.cells()==[attr*256+32 if predicate(i//80,i%80) else v for i,v in enumerate(self.original)]

def main():
 cases=[]
 def check(name,test):test();cases.append({'case':name,'passed':True});print(name,'passed')
 def rectangle():
  for a,b,c,d in [(0,0,24,79),(1,2,3,5),(24,79,24,79),(0,0,0,0)]:
   e=Erase();e.rectangle(a,b,c,d,attribute=0x1e);e.assert_clear(lambda r,x:a<=r<=c and b<=x<=d,0x1e)
   assert len(e.calls)==1 and e.calls[0]['function']==6
 check('rectangle-clear-exact-inclusive-bounds',rectangle)
 def scroll():
  for count in [1,-1,2,-2]:
   e=Erase();e.rectangle(2,3,5,10,count=count,attribute=0x2f)
   expected=e.original[:]
   for row in range(2,6):
    for col in range(3,11):
     source=row+count
     expected[row*80+col]=e.original[source*80+col] if 2<=source<=5 else 0x2f20
   assert e.cells()==expected
   assert e.calls[0]['function']==(6 if count>0 else 7)
 check('positive-negative-multiline-scroll-and-fill',scroll)
 def before():
  e=Erase();e.call('csi_service_d844');e.assert_clear(lambda r,c:r==10 and c<=20)
  assert e.get('csi_wrap_pending')==0
  e=Erase();e.call('csi_service_d85e');e.assert_clear(lambda r,c:r<10 or r==10 and c<=20)
  e=Erase();e.put('screen_cursor_row',0);e.put('screen_cursor_column',0);e.call('csi_service_d85e');e.assert_clear(lambda r,c:r==0 and c==0)
 check('line-and-display-before-cursor',before)
 def after():
  for flag in [0,1]:
   e=Erase();e.put('erase_test_flag',flag);e.call('erase_test_after');e.assert_clear(lambda r,c:r==10 and c>=20 or bool(flag) and r>10)
  e=Erase();e.put('attributes_monochrome',1);e.put('attributes_current',0x70);e.call('erase_test_after');e.assert_clear(lambda r,c:r==10 and c>=20,0x70)
 check('line-and-display-after-with-monochrome-attribute',after)
 def lineflags():
  for count,want in [(1,[2,3,4,0]),(-1,[0,1,2,3])]:
   e=Erase();e.put('erase_lineflags_enabled',1);e.uc.mem_write(e.symbols['screen_line_flags']+2,bytes([1,2,3,4]));e.rectangle(2,0,5,79,count=count)
   assert list(e.uc.mem_read(e.symbols['screen_line_flags']+2,4))==want
  e=Erase();e.put('erase_lineflags_enabled',1);e.uc.mem_write(e.symbols['screen_line_flags'],b'\x40'*25);e.call('csi_service_d85e')
  assert e.uc.mem_read(e.symbols['screen_line_flags'],10)==bytes(10)
 check('overlapping-lineflag-move-and-clearing',lineflags)
 def shadow():
  e=Erase();e.put('screen_viewport_enabled',1);e.put('screen_attribute_row_bytes',120)
  base=e.symbols['erase_shadow_cells'];e.uc.mem_write(base,b'\xaa'*8192)
  e.rectangle(2,0,2,9,attribute=0x1e)
  assert e.cells()==e.original and not e.calls
  assert e.uc.mem_read(base+480,20)==b'\x20\x1e'*10
  assert e.uc.mem_read(base+478,2)==b'\xaa\xaa' and e.uc.mem_read(base+500,2)==b'\xaa\xaa'
 check('offscreen-viewport-shadow-fill-without-visible-write',shadow)
 def attribute_planes():
  e=Erase();e.put('screen_cursor_wrap',1);base=e.symbols['erase_attribute_flags'];values=e.symbols['erase_attribute_values']
  e.uc.mem_write(base,b'\x02'*2000);e.uc.mem_write(values+819,b'\x2e');e.call('erase_test_after')
  assert e.uc.mem_read(base+820,60)==bytes(60)
  assert e.uc.mem_read(values+820,60)==b'\x2e'*60
  e.assert_clear(lambda r,c:r==10 and c>=20,0x2e)
  e=Erase();e.put('screen_cursor_wrap',1);e.put('screen_attribute_checks',1)
  try:e.call('erase_test_after')
  except UnrecoveredService:pass
  else:raise AssertionError('protected erase dependency unexpectedly hidden')
 check('attribute-plane-updates-and-explicit-protected-dependency',attribute_planes)
 result={'binary_sha256':hashlib.sha256((ROOT/'build/erase/ERASE.EXE').read_bytes()).hexdigest(),'cases':cases,'limitations':['Linked CPU replay uses an explicit INT10 text-video model; independent DOSBox smoke validates a real BIOS rectangle.','Complex protected erase and attribute repair remain unimplemented and trap.','Does not establish all viewport/video modes, physical adapters or complete parser integration.']}
 (ROOT/'build/erase/checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
