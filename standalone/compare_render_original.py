#!/usr/bin/env python3
"""Optional analyst comparison: original resident renderer versus linked source.

Reads an ignored verified original. Never required by the source-only build.
The original and reconstructed paths execute their real cursor/video routines.
"""
from pathlib import Path
import hashlib,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *
from check_render import Render
from check_scroll import Scroll
ROOT=Path(__file__).resolve().parents[1]
EXPECTED='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
class Original:
 def __init__(self,image,source):
  self.uc=Uc(UC_ARCH_X86,UC_MODE_16);self.uc.mem_map(0,0x100000)
  self.base=0x10000;self.data_base=0x50000;self.video=0xb8000;self.positions=[];self.calls=[];self.returned=False
  self.uc.mem_write(self.base,image[0x1200:0x1200+53456]);self.uc.mem_write(self.video,b'\xa5'*4000)
  state={}
  for name in ('render','screen','text','erase','scroll'):
   proof=json.loads((ROOT/f'reconstruction/{name}/provenance.json').read_text())
   state.update({symbol:int(at,16) for at,symbol in proof['state'].items()})
  self.symbols={name:self.data_base+offset for name,offset in state.items()}
  for name,address in self.symbols.items():
   width=1 if name=='render_translation_mask' else 2
   self.uc.mem_write(address,bytes(source.uc.mem_read(source.symbols[name],width)))
  # Original near data pointers must refer to this instance's DS, not linked DS.
  self.put('screen_attributes_base',0x6000);self.put('render_translation_base',0x7000)
  self.put('erase_attribute_values_base',0x2000);self.put('erase_shadow_offset',0xa000);self.put('erase_shadow_segment',0x5000)
  self.uc.mem_write(self.data_base+0x2000,bytes(source.uc.mem_read(source.symbols['erase_attribute_values'],4096)))
  self.uc.mem_write(self.symbols['render_graphics_map'],bytes(source.uc.mem_read(source.symbols['render_graphics_map'],128)))
  self.uc.mem_write(self.symbols['screen_line_flags'],bytes(source.uc.mem_read(source.symbols['screen_line_flags'],128)))
  self.uc.mem_write(self.data_base+0x7000,bytes(source.uc.mem_read(source.symbols['render_translation_table'],256)))
  self.uc.hook_add(UC_HOOK_CODE,self.stop);self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def get(self,name,width=2):return int.from_bytes(self.uc.mem_read(self.symbols[name],width),'little')
 def put(self,name,value,width=2):self.uc.mem_write(self.symbols[name],value.to_bytes(width,'little'))
 def stop(self,uc,address,size,data):
  if address==self.base+0xf000:self.returned=True;uc.emu_stop()
 def interrupt(self,uc,number,data):
  if number==0x10 and uc.reg_read(UC_X86_REG_AX)>>8==2:self.positions.append(uc.reg_read(UC_X86_REG_DX))
  else:Scroll.interrupt(self,uc,number,None)
 def cells(self):return list(struct.unpack('<2000H',self.uc.mem_read(self.video,4000)))
 def call(self,entry,character=None,row=0,column=0):
  for register,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x5000),(UC_X86_REG_SS,0x5000),(UC_X86_REG_EFLAGS,0x202),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_AX,row),(UC_X86_REG_DX,column)]:self.uc.reg_write(register,value)
  words=[0xf000]+([] if character is None else [character]);sp=0xe000-len(words)*2
  self.uc.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));self.uc.reg_write(UC_X86_REG_SP,sp)
  self.returned=False;self.uc.emu_start(self.base+entry,self.base+0x10000,count=200000)
  assert self.returned and self.uc.reg_read(UC_X86_REG_SP)==sp+2
 def position(self,row,column):self.call(0x1bbe,row=row,column=column)
 def character(self,value):self.call(0x730,character=value)

def main():
 image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 cases=[];count=0
 fields=['screen_cursor_row','screen_cursor_column','screen_visible_column','screen_previous_row','screen_previous_column','screen_video_offset','screen_attribute_offset','csi_wrap_pending','render_deferred_row','render_deferred_column','scroll_suppress_next_linefeed']
 def compare(name,setup,actions):
  nonlocal count
  source=Render();setup(source);original=Original(image,source)
  for action,args in actions:
   getattr(source,action)(*args);getattr(original,action)(*args)
   assert bytes(source.uc.mem_read(source.video,4000))==bytes(original.uc.mem_read(original.video,4000)),(name,action,args,'video')
   for field in fields:assert source.get(field)==original.get(field),(name,action,args,field,source.get(field),original.get(field))
   assert source.positions==original.positions,(name,'BIOS cursor calls');assert source.calls==original.calls,(name,'BIOS scroll calls');count+=1
  cases.append({'case':name,'passed':True});print(name,'matched',flush=True)
 compare('all-byte-character-outputs',lambda a:None,[('position',(i//80,i%80)) if index%2==0 else ('character',(i,)) for i in range(256) for index in range(2)])
 compare('deferred-wrap',lambda a:None,[('position',(4,79)),('character',(65,)),('character',(66,))])
 compare('autowrap-disabled',lambda a:a.put('render_autowrap',0),[('position',(4,79)),('character',(65,)),('character',(66,))])
 compare('immediate-wrap',lambda a:a.put('attributes_color_mode',0),[('position',(4,79)),('character',(65,)),('character',(66,))])
 compare('bottom-no-scroll',lambda a:None,[('position',(24,79)),('character',(65,)),('character',(66,))])
 compare('pound-glyph',lambda a:(a.put('ansi_charset_g0_flag_a',1),a.put('cursor_state_value_cdfc',1)),[('character',(35,))])
 compare('graphics-glyph',lambda a:(a.put('ansi_charset_g0_flag_graphics',1),a.put('cursor_state_value_cdfc',1),a.uc.mem_write(a.symbols['render_graphics_map']+113,b'\xc4')),[('character',(113,))])
 compare('translation',lambda a:(a.put('attributes_color_mode',0),a.put('screen_cursor_wrap',1),a.put('render_translation_enabled',1),a.put('render_direct_output',1),a.uc.mem_write(a.symbols['render_translation_table']+65,b'Z')),[('character',(65,))])
 compare('two-cell-line',lambda a:a.uc.mem_write(a.symbols['screen_line_flags'],b'\x40'),[('character',(65,))])
 compare('bottom-with-real-scroll',lambda a:a.put('scroll_enabled',1),[('position',(24,79)),('character',(65,)),('character',(66,))])
 result={'passed':True,'original_sha256':EXPECTED,'linked_binary_sha256':hashlib.sha256((ROOT/'build/render/RENDER.EXE').read_bytes()).hexdigest(),'compared_operations':count,'cases':cases,'scope':'Original resident and linked source high-level renderer/cursor/video instructions under Unicorn, identical public configuration/map fixtures; full4000-byte screen and cursor/deferredwrap fields checked after every operation.'}
 (ROOT/'build/render/original-comparison.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':main()
