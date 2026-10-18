#!/usr/bin/env python3
"""Optional original resident comparison for input/control/history paths.

ANSI stream integration is covered by the source-only tests; original overlay
loading is outside this comparison's scope. No original bytes are patched.
"""
from pathlib import Path
import hashlib,json
from check_input_dispatch import Input
from compare_render_original import Original,EXPECTED
ROOT=Path(__file__).resolve().parents[1]
class OriginalInput(Original):
 def __init__(self,image,source):
  super().__init__(image,source)
  proof=json.loads((ROOT/'reconstruction/input_dispatch/provenance.json').read_text())
  for offset,name in proof['state'].items():
   self.symbols[name]=self.data_base+int(offset,16)
   if name.endswith('_dispatch_table'):continue
   width=1 if name in ('terminal_backspace_erases','terminal_history_pending') else 2
   self.uc.mem_write(self.symbols[name],bytes(source.uc.mem_read(source.symbols[name],width)))
  # Copy verified original pointer values, not reconstructed addresses.
  startup=image[153936:153936+60080]
  self.uc.mem_write(self.data_base+0x445e,startup[0x445e:0x44e0])
  self.uc.mem_write(self.data_base+0xce10,bytes(source.uc.mem_read(source.symbols['terminal_tab_stops'],30)))
  self.put('terminal_history_start',0xe000);self.put('terminal_history_pointer',0xe000)
  self.uc.mem_write(self.data_base+0x4ec0,(0x5000).to_bytes(2,'little'))
  self.put('terminal_history_end',0xe000+source.get('terminal_history_end')-source.get('terminal_history_start'))
 def character(self,value):self.call(0x610,character=value)
 def history(self):
  start=self.get('terminal_history_start');end=self.get('terminal_history_pointer')
  return bytes(self.uc.mem_read(self.data_base+start,end-start))

def main():
 image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
 cases=[];operations=0
 def compare(name,data,setup=lambda c:None):
  nonlocal operations
  source=Input();setup(source);original=OriginalInput(image,source)
  for value in data:
   source.call('terminal_receive_character',(value,));original.character(value)
   assert bytes(source.uc.mem_read(source.video,4000))==bytes(original.uc.mem_read(original.video,4000)),(name,value,'video')
   for field in ['screen_cursor_row','screen_cursor_column','screen_video_offset','screen_attribute_offset','csi_wrap_pending','scroll_suppress_next_linefeed','terminal_history_pending','terminal_history_wrapped']:
    width=1 if field=='terminal_history_pending' else 2
    assert source.get(field,width)==original.get(field,width),(name,value,field,source.get(field,width),original.get(field,width))
   assert source.history()==original.history(),(name,value,'history')
   assert source.positions==original.positions and source.calls==original.calls,(name,value,'BIOS calls')
   operations+=1
  cases.append({'case':name,'passed':True});print(name,'matched',flush=True)
 compare('ordinary-and-high-byte-input',bytes(range(32,127))+bytes(range(128,256)))
 compare('tab-cr-lf-backspace-history',b'AB\tC\r\nD\x08E\x00\x7f')
 compare('deferred-wrap',b'A'*80+b'B')
 compare('carriage-return-adds-linefeed',b'AB\rCD',lambda c:c.put('terminal_cr_adds_lf',1))
 compare('linefeed-returns-column',b'AB\nCD',lambda c:c.put('terminal_newline_mode_9020',1))
 compare('history-ring-wrap',b'ABCDE',lambda c:c.put('terminal_history_end',c.get('terminal_history_start')+4))
 # Observe original bad function-pointer selection without executing its target.
 unsafe=[]
 from unicorn import UC_HOOK_CODE
 from unicorn.x86_const import UC_X86_REG_BX
 for argument,want_offset,want_target in [(0xffb1,0x4402,0x5d58),(0xffff,0x449e,0xbb3b)]:
  source=Input();original=OriginalInput(image,source)
  original.uc.mem_write(original.data_base+0x4400,image[153936+0x4400:153936+0x445e])
  captured=[]
  def inspect(uc,address,size,data):
   if address==original.base+0x6a7:
    offset=(uc.reg_read(UC_X86_REG_BX)+0x44a0)&0xffff
    target=int.from_bytes(uc.mem_read(original.data_base+offset,2),'little')
    captured.append((offset,target));uc.emu_stop()
  original.uc.hook_add(UC_HOOK_CODE,inspect)
  try:original.character(argument)
  except AssertionError:pass # Stopped intentionally before unsafe indirect call.
  assert captured==[(want_offset,want_target)],captured
  unsafe.append({'argument':argument,'original_pointer_offset':want_offset,'original_target':want_target,'stopped_before_call':True})
 result={'passed':True,'original_sha256':EXPECTED,'linked_binary_sha256':hashlib.sha256((ROOT/'build/input_dispatch/INPUT.EXE').read_bytes()).hexdigest(),'operations':operations,'original_out_of_bounds_pointer_observations':unsafe,'cases':cases,'scope':'Unmodified original resident input/control/render/video/cursor/history/logging instructions versus source-linked entry per character; actual originalDScontrol pointers; overlay ANSI dispatch excluded and independently source-integration tested.'}
 (ROOT/'build/input_dispatch/original-comparison.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':main()
