#!/usr/bin/env python3
"""Exercise actual linked high-level renderer, video writers and cursor services."""
from pathlib import Path
import hashlib,json,struct
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX
from dos_image import DosImage
from check_scroll import Scroll
ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'build/render/RENDER.EXE'
class MissingRenderService(Exception):pass
class Render(DosImage):
 def __init__(self):
  super().__init__(BINARY,ROOT/'build/render/render.map');self.positions=[];self.calls=[];self.video=0xb8000
  self.uc.mem_write(self.video,b'\xa5'*4000)
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def interrupt(self,uc,number,_):
  if number==3:raise MissingRenderService(self.get('render_unimplemented_service'))
  if number==0x10 and uc.reg_read(UC_X86_REG_AX)>>8==2:self.positions.append(uc.reg_read(UC_X86_REG_DX))
  else:Scroll.interrupt(self,uc,number,None)
 def cells(self):return list(struct.unpack('<2000H',self.uc.mem_read(self.video,4000)))
 def character(self,value):
  self.put('render_input_character',value)
  self.call('render_test_character')
 def position(self,row,column):
  self.uc.reg_write(UC_X86_REG_AX,row);self.uc.reg_write(UC_X86_REG_DX,column)
  self.call('screen_set_cursor')
 def cell(self,row,column):return bytes(self.uc.mem_read(self.video+row*160+column*2,2))

def run():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def ordinary():
  a=Render()
  for value in range(256):
   a.position(value//80,value%80);a.put('attributes_current',255-value);a.character(value)
   assert a.cell(value//80,value%80)==bytes([value,255-value])
   assert a.get('screen_video_offset')==((value//80)*80+min(value%80+1,79))*2
 check('all-256-character-attribute-values-and-cursor-offsets',ordinary)
 def deferred():
  a=Render();a.position(1,79);a.character(ord('A'))
  assert a.get('csi_wrap_pending')==1 and a.get('screen_cursor_column')==79
  a.character(ord('B'));assert a.cell(2,0)==b'B\x07' and a.get('screen_cursor_column')==1 and a.get('csi_wrap_pending')==0
  a=Render();a.put('render_autowrap',0);a.position(1,79);a.character(ord('A'));a.character(ord('B'))
  assert a.cell(1,79)==b'B\x07' and a.get('screen_cursor_row')==1 and a.get('screen_cursor_column')==79
 check('deferred-wrap-and-autowrap-disabled',deferred)
 def immediate():
  a=Render();a.put('attributes_color_mode',0);a.position(1,79);a.character(ord('A'))
  assert a.get('screen_cursor_row')==2 and a.get('screen_cursor_column')==0 and not a.get('csi_wrap_pending')
  a=Render();a.position(24,79);a.character(ord('A'));a.character(ord('B'))
  assert a.cell(24,0)==b'B\x07' and a.get('screen_cursor_row')==24
 check('immediate-wrap-and-bottom-with-scrolling-disabled',immediate)
 def mapping():
  a=Render();a.put('ansi_charset_g0_flag_a',1);a.put('cursor_state_value_cdfc',1);a.character(ord('#'));assert a.cell(0,0)==b'\x9c\x07'
  a=Render();a.put('ansi_charset_g0_flag_graphics',1);a.put('cursor_state_value_cdfc',1)
  a.uc.mem_write(a.symbols['render_graphics_map']+ord('q'),b'\xc4');a.character(ord('q'));assert a.cell(0,0)==b'\xc4\x07'
  a=Render();a.put('attributes_color_mode',0);a.put('screen_cursor_wrap',1);a.put('render_translation_enabled',1);a.put('render_direct_output',1)
  a.uc.mem_write(a.symbols['render_translation_table']+ord('A'),b'Z');a.character(ord('A'));assert a.cell(0,0)==b'Z\x07'
 check('british-pound-graphics-and-configured-translation-paths',mapping)
 def doublewidth():
  a=Render();a.uc.mem_write(a.symbols['screen_line_flags'],b'\x42');a.character(ord('A'))
  assert a.cell(0,0)==b' \x07' and a.cell(0,1)==b' \x07' and a.get('screen_cursor_column')==2
  a=Render();a.uc.mem_write(a.symbols['screen_line_flags'],b'\x40');a.character(ord('A'))
  assert a.cell(0,0)==b' \x07' and a.cell(0,1)==b'A\x07' and a.get('screen_cursor_column')==2
 check('lineflag-two-cell-output-through-real-fill-and-packed-writers',doublewidth)
 def unavailable():
  for setup,want in [(lambda a:a.put('terminal_mode_372c',1),0xb9f7),(lambda a:(a.put('attributes_color_mode',0),a.put('screen_attribute_checks',1),a.put('screen_cursor_wrap',1),a.uc.mem_write(a.symbols['screen_attribute_cells'],b'\x81')),0x2adc)]:
   a=Render();setup(a)
   try:a.character(ord('B'))
   except MissingRenderService as error:assert error.args==(want,)
   else:raise AssertionError('unsupported renderer feature silently succeeded')
 check('unrecovered-mode-and-attribute-boundaries-fail-fast',unavailable)
 def scrolling():
  a=Render();a.put('scroll_enabled',1);a.position(24,79);a.character(ord('A'));a.character(ord('B'))
  assert a.cell(23,79)==b'A\x07' and a.cell(24,0)==b'B\x07' and a.cell(24,1)==b' \x07'
  assert a.get('screen_cursor_row')==24 and a.get('screen_cursor_column')==1 and len(a.calls)==1
 check('bottom-margin-deferred-wrap-through-real-scroll-service',scrolling)
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual recovered highlevel character/cursor/video instructions with host-supplied configuration and glyph-map fixtures; unresolved services trap.'}
 (ROOT/'build/render/checks.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':run()
