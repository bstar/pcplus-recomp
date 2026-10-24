#!/usr/bin/env python3
"""Native alternate field output, byte preservation, output maps and reset ownership."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport
from check_protected_erase_live import ROOT,stage
from check_viewport_live import logical
from check_line_edit_live import Abort

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enable(m,translated):
 m.put('attributes_color_mode',0);m.put('render_translation_enabled',translated)
 m.put('render_translation_base',m.offset('render_translation_table'))
 m.uc.mem_write(m.symbols['render_translation_mask'],b'\xff')
 return m.get('screen_attribute_offset')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args();binary=a.terminal.resolve();mf=json.loads((binary.parent/'manifest.json').read_text())
 assert sha(binary)==mf['binary_sha256']
 for n,h in mf['sources'].items():assert sha(ROOT/n)==h,n
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map';cases=0
 names=['screen_cursor_row','screen_cursor_column','screen_attribute_offset','screen_video_offset','screen_visible_column','screen_viewport_active','screen_viewport_offset','csi_wrap_pending']
 for(rows,hidden),(cols,right),profile,translated in itertools.product([(1,0),(5,0),(24,0),(25,1)],[(80,False),(132,False),(132,True)],(4,6),(0,1)):
  m,address,cells,flags,values,row=stage(cols,rows,hidden,profile,right,60,2,1);start=enable(m,translated);n=rows*cols
  cursor=[m.get(x)for x in names];oldshadow=bytes(m.uc.mem_read(address,8192));original_flags=bytearray(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096));original_values=bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096));video=bytearray(m.uc.mem_read(0xb8000,4000));at=m.get('screen_video_offset')
  for char in range(256):
   old=(char*29+0x17)&255;preset=char^0x4e
   m.put('attributes_preset_value',preset);m.uc.mem_write(0xb8000+at,bytes([0x5a,old]));m.uc.mem_write(m.symbols['screen_attribute_cells']+start,b'\x81')
   expected=values[start-1]if translated and start else values[0]if translated and flags[0]&0x80 else 0x17 if translated else(old&0xf8)|(preset&7)
   m.call('render_font_output',[start,char],cleanup=4)
   assert bytes(m.uc.mem_read(0xb8000+at,2))==bytes([char,expected]),(rows,cols,right,profile,translated,char,'cell')
   original_flags[start]=3 if translated else 1
   assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096))==original_flags
   assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],4096))==original_values
   assert bytes(m.uc.mem_read(address,8192))==oldshadow
   assert [m.get(x)for x in names]==cursor
   current=bytearray(m.uc.mem_read(0xb8000,4000));current[at:at+2]=video[at:at+2];assert current==video
   for reg,want in [(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_ES,0xb800),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert m.uc.reg_read(reg)==want
   cases+=1
 # Actual high-level renderer applies the map/mask before output. A short
 # stream crosses the logical edge without invoking unrelated bottom scrolling.
 streams=0
 table=bytes(i^0x55 for i in range(256));data=[0x41,0xdb,0xff,0,0x80,0x7f]
 for(cols,right),translated,checks,protect,direct,mask in itertools.product([(80,False),(132,False),(132,True)],(0,1),(0,1),(0,1),(0,1),(0x7f,0xff)):
  m,address,cells,flags,values,row=stage(cols,5,0,6,right,60,0,protect);enable(m,translated);m.put('screen_attribute_checks',checks);m.put('render_direct_output',direct);m.uc.mem_write(m.symbols['render_translation_mask'],bytes([mask]));m.uc.mem_write(m.symbols['render_translation_table'],table)
  m.uc.mem_write(m.symbols['screen_attribute_cells'],bytes(4096));flags=bytearray(len(cells));m.position(1,cols-3);row=1;col=cols-3;expected=list(cells)
  for raw in data:
   i=row*cols+col;char=table[raw&mask]if translated else raw;old=expected[i]>>8
   if direct:attr=0x9c
   elif translated:attr=values[i-1]if i else 0x17;flags[i]=3
   elif protect:attr=(old&0xf8)|(0x4e&7);flags[i]=1
   else:attr=old
   expected[i]=(attr<<8)|char
   m.call('render_character',[raw])
   row,col=(row+1,0)if col==cols-1 else(row,col+1)
  actual=logical(m,address,5)if cols==132 else bytes(m.uc.mem_read(0xb8000,5*160))
  assert actual==struct.pack('<'+'H'*len(cells),*expected),(cols,right,translated,checks,protect,direct,mask,'rendered stream')
  assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],len(cells)))==flags
  assert bytes(m.uc.mem_read(m.symbols['erase_attribute_values'],len(cells)))==bytes(values)
  assert(m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(row,col)
  streams+=1
 # Interrupt during the native reader's deliberately foreign video DS. The
 # real parent IRQ must restore it before LODSB and subsequent metadata writes.
 irq_cases=0;payload=bytes(range(256))*2
 for(cols,right),profile in itertools.product([(80,False),(132,False),(132,True)],(4,6)):
  m,address,*_=stage(cols,5,0,profile,right,60,0,1);start=enable(m,0);fired=[];at=m.get('screen_video_offset');old=bytes(m.uc.mem_read(0xb8000+at,2))
  def irq(u,pc,size,_):
   if fired or pc!=m.symbols['alternate_output_read']+22:return
   fired.append(True);assert u.reg_read(UC_X86_REG_DS)==0xb800 and u.reg_read(UC_X86_REG_SS)==m.ds
   m.rx.extend(payload);sp=u.reg_read(UC_X86_REG_SP)-6;ss=u.reg_read(UC_X86_REG_SS);f=u.reg_read(UC_X86_REG_EFLAGS)&65535;assert f&0x200
   u.mem_write(ss*16+sp,struct.pack('<3H',u.reg_read(UC_X86_REG_IP),u.reg_read(UC_X86_REG_CS),f));u.reg_write(UC_X86_REG_SP,sp);u.reg_write(UC_X86_REG_EFLAGS,f&~0x300);u.reg_write(UC_X86_REG_CS,m.code_segment);u.reg_write(UC_X86_REG_IP,m.symbols['uart_receive_interrupt']-m.code_base)
  m.uc.hook_add(UC_HOOK_CODE,irq);m.call('render_font_output',[start,0xdb],cleanup=4)
  assert fired and m.get('uart_rx_count')==512 and not m.rx and bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],512))==payload
  assert bytes(m.uc.mem_read(0xb8000+at,2))==bytes([0xdb,(old[1]&0xf8)|6])and m.uc.reg_read(UC_X86_REG_DS)==m.ds
  irq_cases+=1
 refusals=0
 for name,value in [('screen_attribute_offset',1),('screen_video_offset',1),('screen_cursor_column',132),('screen_attributes_base',65535),('erase_attribute_values_base',65535),('attributes_color_mode',1),('screen_cursor_wrap',0),('render_translation_enabled',2),('render_translation_base',65535)]:
  m,address,*_=stage(132,5,0,6,True,60,0,1);start=enable(m,0);m.put(name,value);before=(bytes(m.uc.mem_read(0xb8000,4000)),bytes(m.uc.mem_read(address,8192)),bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096)))
  try:m.call('render_font_output',[start,0xdb],cleanup=4)
  except Abort as e:assert e.args==(0xbb53,)
  else:raise AssertionError(('missing alternate output refusal',name))
  assert before==(bytes(m.uc.mem_read(0xb8000,4000)),bytes(m.uc.mem_read(address,8192)),bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],4096)))
  refusals+=1
 resets=0
 for cols,right in [(80,False),(132,False),(132,True)]:
  m,address,*_=stage(cols,5,0,6,right,60,0,1);enable(m,1);m.uc.mem_write(m.symbols['render_translation_mask'],b'\x7f');m.uc.mem_write(m.symbols['render_translation_table'],table);assert m.call('terminal_reset_capture')==0
  m.put('render_translation_enabled',0);m.put('render_translation_base',65535);m.uc.mem_write(m.symbols['render_translation_mask'],b'\x03');m.call('csi_reset_terminal',limit=3000000)
  assert m.get('render_translation_enabled')==1 and m.get('render_translation_base')==m.offset('render_translation_table')
  assert bytes(m.uc.mem_read(m.symbols['render_translation_mask'],1))==b'\x7f'and bytes(m.uc.mem_read(m.symbols['render_translation_table'],256))==table
  resets+=1
 width_commits=0
 for profile,translated in itertools.product((4,6),(0,1)):
  m,address,*_=stage(80,5,0,profile,False,60,0,1);enable(m,translated);m.uc.mem_write(m.symbols['render_translation_table'],table)
  for request in (1,0,1):
   assert m.call('terminal_native_width',ax=request,limit=3000000)==0
   assert m.get('attributes_color_mode')==0 and m.get('render_translation_enabled')==translated
   assert m.get('render_translation_base')==m.offset('render_translation_table')and bytes(m.uc.mem_read(m.symbols['render_translation_table'],256))==table
   m.position(0,60);start=m.get('screen_attribute_offset');at=m.get('screen_video_offset');old=m.uc.mem_read(0xb8000+at+1,1)[0]
   m.uc.mem_write(m.symbols['screen_attribute_cells']+start,bytes(2))
   expected_char=table[0xdb]if translated else 0xdb
   expected_attr=m.uc.mem_read(m.symbols['erase_attribute_values']+start-1,1)[0]if translated else(old&0xf8)|(m.get('attributes_preset_value')&7)
   m.call('render_character',[0xdb])
   assert bytes(m.uc.mem_read(0xb8000+at,2))==bytes([expected_char,expected_attr])
   assert m.get('screen_cursor_column')==61
   width_commits+=1
 result=dict(passed=True,cell_cases=cases,renderer_streams=streams,foreign_DS_IRQ_cases=irq_cases,pre_mutation_refusals=refusals,RIS_cases=resets,active_width_commits=width_commits,binary_sha256=sha(binary),sources=mf['sources'],checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' Both profiles/panes/widths,1/5/24/25 rows, every byte and palette value, direct/native-renderer paths, mapping/masks and source-owned reset selection. Only BIOS/UART hardware is modeled; actual DOS/ASPECT and physical acceptance remain separate.')
 (binary.parent/'alternate-output-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS alternate output:',cases,'cells,',streams,'renderer streams,',irq_cases,'foreign-DS IRQ,',resets,'RIS,',refusals,'refusals')
if __name__=='__main__':main()
