#!/usr/bin/env python3
"""Actual application near/far repair and all native repaint dependencies."""
import hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_line_edit_live import Live,Abort
from check_attribute_repair import Machine as Reference
from check_scroll_fields_live import reference as scroll_reference
from check_terminal_key_edit import Edit
from check_terminal_reverse_tab import Reverse
from check_keyboard_mapping_raw import KEYS
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/attribute-repair'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 cases=0;visited=set();geometry_errors=0
 def stage(height,cursor,flags,values,wrap):
  t=Live();t.put('csi_last_row',height-1);t.put('screen_last_row',height-1);t.put('erase_cell_count',height*80)
  t.position(*divmod(cursor,80));t.put('screen_cursor_wrap',wrap)
  for name,value in [('attributes_current',0x9c),('attributes_preset_value',0x4e),('attributes_normal_value',0x27),('csi_erase_attribute',0x17)]:t.put(name,value,1)
  t.uc.mem_write(t.symbols['screen_attribute_cells'],b'\x55'*4096);t.uc.mem_write(t.symbols['erase_attribute_values'],b'\x66'*4096)
  t.uc.mem_write(t.symbols['screen_attribute_cells'],bytes(flags));t.uc.mem_write(t.symbols['erase_attribute_values'],bytes(values))
  t.uc.hook_add(UC_HOOK_CODE,lambda u,at,size,data:visited.add(at))
  return t
 def snapshots(t):
  return (bytes(t.uc.mem_read(t.symbols['screen_attribute_cells'],4096)),bytes(t.uc.mem_read(t.symbols['erase_attribute_values'],4096)),bytes(t.uc.mem_read(0xb8000,8000)))
 for height,pattern,mode,wrap in itertools.product((1,5,25),range(6),(0,1,2,3,4),(0,1)):
  n=height*80
  flags=bytes(0 if pattern==0 else 0x81 if pattern==1 else (0x80 if i%17==0 else i%4) if pattern==2 else (0x80 if i==0 else 0) if pattern==3 else (0x80 if i==n-1 else i%4) if pattern==4 else (0x80 if i%79==0 else 0x40|i%4) for i in range(n))
  for cursor in sorted({0,1,min(79,n-1),n//2,n-1}):
   values=bytes((i*31+0x17)&255 for i in range(n));t=stage(height,cursor,flags,values,wrap);before=snapshots(t)
   r=object.__new__(Reference);r.cols=80;r.rows=height;r.flags=flags;r.values=values;r.cursor=cursor;r.video=bytearray(before[2]);r.shadow=bytearray(8000)
   expected_values,expected_video,_,_=r.reference(mode,wrap,None)
   t.call('erase_repair_attributes',[mode],cleanup=2,limit=2000000)
   after=snapshots(t)
   assert after[0]==before[0] and after[1]==expected_values+before[1][n:]
   assert after[2]==expected_video,(height,pattern,mode,wrap,cursor,'video')
   assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==divmod(cursor,80)
   for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_DS,t.ds),(UC_X86_REG_SS,t.ds)]:assert t.uc.reg_read(reg)==value
   cases+=1
 mutations=[('screen_columns',0),('screen_attribute_row_bytes',0),('screen_video_row_bytes',0),('text_video_segment',0),('screen_viewport_enabled',1),('screen_viewport_active',2),('screen_viewport_offset',1),('screen_last_column',78),('csi_last_row',25),('screen_first_row',25),('screen_last_row',25),('erase_cell_count',1999),('screen_attributes_base',0xff00),('erase_attribute_values_base',0xff00),('screen_cursor_column',80),('screen_attribute_offset',1),('screen_video_offset',1)]
 for name,value in mutations:
  t=stage(25,417,bytes(2000),bytes(2000),1);t.put(name,value);before=snapshots(t)
  try:t.call('erase_repair_attributes',[2],cleanup=2)
  except Abort as e:assert e.args==(0x2d98,)
  else:raise AssertionError(('Missing repair geometry rejection',name))
  assert snapshots(t)==before;cases+=1;geometry_errors+=1
  # The native wrap-disabled service is a no-op even with unusable geometry.
  t.put('screen_cursor_wrap',0);t.call('erase_repair_attributes',[2],cleanup=2);assert snapshots(t)==before;cases+=1
 for name in ('attribute_repair_native','attribute_repair_write','attribute_repair_advance','attribute_position_to_video','erase_default_attribute','erase_previous_attribute','text_write_char'):
  assert t.symbols[name] in visited,('Native dependency did not execute',name)
 # Live consumers now keep metadata and pixels inside the same rectangle.
 # The separate native component retains its recovered whole-plane behavior.
 def repair_reference(flags,values,video,cursor,mode):
  r=object.__new__(Reference);r.cols=80;r.rows=25;r.flags=bytes(flags);r.values=bytes(values);r.cursor=cursor;r.video=bytearray(video);r.shadow=bytearray(8000)
  values,video,_,_=r.reference(mode,True,None);return bytes(values),bytes(video)
 consumer_cases=0
 for top,bottom,method,pattern in itertools.product((0,5),(10,24),('scroll_up','screen_wrap_forward','reverse-key'),range(3)):
  if method=='reverse-key' and bottom==24:continue
  flags=bytearray(2000);flags[0]=0x80;flags[bottom*80+79]=0x80
  if pattern==1:
   for i in range(7,2000,29):flags[i]|=1
  elif pattern==2:
   for i in range(19,2000,47):flags[i]|=0x80
  values=bytes((i*31+0x17)&255 for i in range(2000))
  t=Reverse() if method=='reverse-key' else Live()
  t.put('screen_first_row',top);t.put('screen_last_row',bottom);t.put('screen_cursor_wrap',1);t.put('screen_attribute_checks',int(method=='reverse-key'));t.put('scroll_skip_attribute_scan',0)
  for name,value in [('attributes_current',0x9c),('attributes_preset_value',0x4e),('attributes_normal_value',0x27),('csi_erase_attribute',0x17)]:t.put(name,value,1)
  t.position(bottom+1 if method=='reverse-key' else bottom,10 if method=='reverse-key' else 79)
  t.uc.mem_write(t.symbols['screen_attribute_cells'],bytes(flags));t.uc.mem_write(t.symbols['erase_attribute_values'],values)
  cells=t.cells()
  expected,shifted_flags,wanted_values,_=scroll_reference(cells,flags,values,80,25,top,bottom,False,values[(bottom+1)*80-1],False)
  wanted_video=struct.pack('<2000H',*expected)
  if method=='reverse-key':assert t.key()==0 and t.wire()==b'R'
  else:t.call(method,limit=2000000)
  assert bytes(t.uc.mem_read(t.symbols['screen_attribute_cells'],2000))==shifted_flags,(top,bottom,method,pattern,'flags')
  assert bytes(t.uc.mem_read(t.symbols['erase_attribute_values'],2000))==wanted_values,(top,bottom,method,pattern,'values')
  assert bytes(t.uc.mem_read(0xb8000,4000))==wanted_video,(top,bottom,method,pattern,'video')
  assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==(bottom,79 if method=='scroll_up' else 0)
  cases+=1;consumer_cases+=1
 for offset,count,keyboard in itertools.product((417,419,479),(1,3),(False,True)):
  if keyboard and count!=1:continue
  t=Edit() if keyboard else Live();t.position(5,17);t.put('screen_cursor_wrap',1)
  for name,value in [('attributes_current',0x9c),('attributes_preset_value',0x4e),('attributes_normal_value',0x27),('csi_erase_attribute',0x17)]:t.put(name,value,1)
  flags=bytearray(2000);flags[offset]=0x80;flags[650]=0x81
  values=bytearray((i*31+0x17)&255 for i in range(2000));video=t.cells();start=417;end=480
  t.uc.mem_write(t.symbols['screen_attribute_cells'],bytes(flags));t.uc.mem_write(t.symbols['erase_attribute_values'],bytes(values))
  for _ in range(count):
   marker=bool(flags[start]&0x80);video[start:end-1]=video[start+1:end];video[end-1]=values[end-1]*256+32
   flags[start:end-1]=flags[start+1:end];flags[end-1]&=0xfe;values[start:end-1]=values[start+1:end]
   if marker:
    repaired,painted=repair_reference(flags,values,struct.pack('<2000H',*video),start,2)
    values=bytearray(repaired);video=list(struct.unpack('<2000H',painted))
  if keyboard:
   t.uc.mem_write(t.symbols['terminal_keymap']+9*12,b'K\0'+bytes(10));assert t.key(KEYS[9])==0 and t.wire()==b'K'
  else:t.feed(b'\x1b['+str(count).encode()+b'P')
  assert t.cells()==video,(offset,count,keyboard,'video')
  assert bytes(t.uc.mem_read(t.symbols['screen_attribute_cells'],2000))==flags
  assert bytes(t.uc.mem_read(t.symbols['erase_attribute_values'],2000))==values
  cases+=1;consumer_cases+=1
 prewire_cases=0
 for keyboard,mutation in itertools.product(('delete','reverse'),[('erase_attribute_values_base',0xff00),('erase_cell_count',1999),('screen_viewport_enabled',1),('screen_last_column',78),('screen_first_row',25),('screen_video_offset',1)]):
  t=Edit() if keyboard=='delete' else Reverse();t.position(5,17) if keyboard=='delete' else t.position(11,10)
  t.put('screen_cursor_wrap',1);t.put('screen_attribute_checks',int(keyboard=='reverse'))
  if keyboard=='reverse':t.put('screen_last_row',10)
  t.uc.mem_write(t.symbols['screen_attribute_cells']+(417 if keyboard=='delete' else 879),b'\x80')
  t.put(*mutation);t.put('ansi_parameters',32767);before=snapshots(t)
  value=t.key(KEYS[9]) if keyboard=='delete' else t.key()
  assert value==3 and not t.wire() and snapshots(t)==before,(keyboard,mutation)
  assert t.get('ansi_parameters')==32767
  assert (t.get('screen_cursor_row'),t.get('screen_cursor_column'))==((5,17) if keyboard=='delete' else (11,10))
  cases+=1;prewire_cases+=1
 report=dict(passed=True,cases=cases,consumer_cases=consumer_cases,prewire_cases=prewire_cases,geometry_errors=geometry_errors,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),reference_sha256=hashlib.sha256((ROOT/'standalone/check_attribute_repair.py').read_bytes()).hexdigest(),original_inputs=[],scope='Actual application RET2 resident bridge, checked far repair and real coordinate/default/previous/video dependencies. Full flag/value guards and video, cursor/DS=SS/callee ABI, malformed geometry before mutation; actual scroll, wrapped reverse Tab and repeated parser/keyboard DCH consumers. Invalid repair backing/geometry rejects keys before wire/cursor/parser/video/plane changes. Live scroll metadata and repair stay inside the requested video region. No viewport or physical hardware compatibility claim.')
 (OUT/'live-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Live attribute repair',cases,'cases PASS')
if __name__=='__main__':main()
