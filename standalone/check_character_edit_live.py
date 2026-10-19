#!/usr/bin/env python3
"""Actual live ICH/DCH/HTS parser and recovered helpers; hardware-only oracle."""
import hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_ES,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI
from dos_image import DosImage
from check_line_edit_live import Live,Abort
ROOT=Path(__file__).resolve().parents[1]

def run():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def expected(t,row,col,units,width,insert,blank_attribute=None,end=80):
  out=t.original[:];start=row*80+col;stop=row*80+end;n=min(units*width,stop-start)
  blank=((t.original[start]>>8) if insert else 7) if blank_attribute is None else blank_attribute
  if insert:out[start:stop]=[blank*256+32]*n+t.original[start:stop-n]
  else:out[start:stop]=t.original[start+n:stop]+[blank*256+32]*n
  return out
 def normal():
  for insert,command in [(True,b'@'),(False,b'P')]:
   for profile in (4,6):
    for row,col,count,width in [(0,0,1,1),(5,17,3,1),(24,79,32767,1),(5,16,3,2),(5,78,32767,2)]:
     t=Live();t.put('csi_terminal_id',profile);t.put('attributes_monochrome',int(profile==6));t.position(row,col)
     if width==2:t.uc.mem_write(t.symbols['screen_line_flags']+row,b'\x40')
     t.feed(b'\x1b['+str(count).encode()+command)
     assert t.cells()==expected(t,row,col,count,width,insert),(insert,profile,row,col,count,width)
     assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(row,col)
     assert not t.get('csi_wrap_pending')
 check('real-parser-ICH-DCH-profile-gates-counts-border-doublewidth-cursor',normal)
 def defaults():
  for insert,command in [(True,b'@'),(False,b'P')]:
   for prefix in (b'',b'0',b'1',b'32768',b'65535'):
    t=Live();t.position(5,17);t.feed(b'\x1b['+prefix+command)
    assert t.cells()==expected(t,5,17,1,1,insert)
 check('omitted-zero-one-and-signed-high-bit-parameters-stay-one-cell',defaults)
 def outside_scroll():
  for row in (0,24):
   t=Live();t.put('screen_first_row',5);t.put('screen_last_row',10);t.position(row,17);t.feed(b'\x1b[2P')
   assert t.cells()==expected(t,row,17,2,1,False)
 check('character-edits-independent-of-vertical-scroll-margins',outside_scroll)
 def invalid():
  mutations=[('screen_cursor_row',25),('screen_cursor_column',80),('screen_last_column',80),('screen_video_offset',2),('screen_attribute_offset',1),('screen_attribute_row_bytes',0),('screen_video_row_bytes',0),('screen_columns',0),('screen_viewport_active',1),('screen_viewport_offset',1),('text_video_segment',0),('csi_last_row',25)]
  for entry in ('csi_service_d270','csi_service_d440'):
   for field,value in mutations:
    t=Live();t.position(5,17);t.put(field,value);t.put('ansi_parameters',32767);t.call(entry)
    assert t.cells()==t.original and t.get('ansi_parameters')==1,(entry,field)
   for col,last in [(17,79),(16,78)]:
    t=Live();t.position(5,col);t.uc.mem_write(t.symbols['screen_line_flags']+5,b'\x40');t.put('screen_last_column',last);t.put('ansi_parameters',32767);t.call(entry)
    assert t.cells()==t.original and t.get('ansi_parameters')==1
 check('invalid-geometry-offsets-viewports-and-doublewidth-pairs-no-op-bounded',invalid)
 def metadata():
  for insert,command in [(True,b'@'),(False,b'P')]:
   t=Live();t.position(5,17);t.put('screen_cursor_wrap',1)
   flags=bytes(i%0x40 for i in range(2000));t.uc.mem_write(t.symbols['screen_attribute_cells'],flags);t.uc.mem_write(t.symbols['erase_attribute_values'],bytes([7])*2000)
   t.feed(b'\x1b[3'+command)
   assert t.cells()==expected(t,5,17,3,1,insert,7)
   wanted=bytearray(flags);start=5*80+17;end=6*80
   for _ in range(3):
    if insert:wanted[start+1:end]=wanted[start:end-1];wanted[start]&=254
    else:wanted[start:end-1]=wanted[start+1:end];wanted[end-1]&=254
   assert bytes(t.uc.mem_read(t.symbols['screen_attribute_cells'],2000))==wanted
 check('real-parser-and-known-metadata-planes-shift-through-actual-helpers',metadata)
 def repair():
  for offset in (5*80+17,5*80+19,5*80+79):
   t=Live();t.position(5,17);t.put('screen_cursor_wrap',1);t.uc.mem_write(t.symbols['screen_attribute_cells']+offset,b'\x80')
   t.feed(b'\x1b[3P')
   assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(5,17)
   assert t.cells()!=t.original
  for pointer in ('screen_attributes_base','erase_attribute_values_base'):
   for entry in ('csi_service_d270','csi_service_d440'):
    t=Live();t.position(5,17);t.put('screen_cursor_wrap',1);t.put(pointer,0xfff0);t.put('ansi_parameters',32767);t.call(entry)
    assert t.cells()==t.original and t.get('ansi_parameters')==1
 check('marker-deletion-uses-real-repair-and-invalid-pointers-remain-no-op',repair)
 def protected():
  for insert,command in [(True,b'@'),(False,b'P')]:
   for wrap in (0,1):
    for boundary in (17,21):
     t=Live();t.position(5,17);t.put('screen_attribute_checks',1);t.put('screen_cursor_wrap',wrap);t.uc.mem_write(t.symbols['screen_attribute_cells']+5*80+boundary,b'\x80')
     t.uc.mem_write(t.symbols['erase_attribute_values'],bytes([7])*2000)
     t.feed(b'\x1b[3'+command)
     assert t.cells()==(t.original if boundary==17 else expected(t,5,17,3,1,insert,end=boundary))
 check('actual-protected-current-and-neighbor-boundaries-no-blanket-mode-skip',protected)
 def hts():
  t=Live();t.position(5,12);t.uc.mem_write(t.symbols['terminal_tab_stops'],bytes([8,16,24]+[254]*27));t.feed(b'\x1bH')
  assert bytes(t.uc.mem_read(t.symbols['terminal_tab_stops'],30))==bytes([8,12,24]+[254]*27)
  before=t.cells();t.position(5,12);t.feed(b'\x1bH');assert t.cells()==before
  for field,value in [('screen_columns',0),('screen_cursor_row',25),('screen_last_column',80),('screen_cursor_column',80)]:
   t=Live();t.position(5,12);t.put(field,value);before=bytes(t.uc.mem_read(t.symbols['terminal_tab_stops'],30));t.call('ansi_escape_service_dac6');assert bytes(t.uc.mem_read(t.symbols['terminal_tab_stops'],30))==before
 check('real-escape-HTS-replacement-duplicate-and-invalid-geometry',hts)
 def abi():
  for entry in ('csi_service_d270','csi_service_d440','ansi_escape_service_dac6'):
   t=Live();t.position(5,17);t.put('ansi_parameters',3);t.uc.reg_write(UC_X86_REG_ES,0x4321);DosImage.call(t,entry)
   for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x4321)]:assert t.uc.reg_read(reg)==value,(entry,reg)
 check('near-stack-BP-SI-DI-and-arbitrary-caller-ES-preserved',abi)
 result={'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked UART IRQ, input/CSI/ESC dispatcher, maintained bounds and recovered character helpers/video/movers/attribute repair; hardware-only BIOS video/keyboard/UART/tick oracle. Fixed80x25 live geometry; complete repair video/value comparisons are in the live repair replay. Viewport support remains diagnostic-only.'}
 (ROOT/'build/terminal/character-edit-live-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Live character editing:',len(cases),'groups passed')
if __name__=='__main__':run()
