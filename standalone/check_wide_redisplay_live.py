#!/usr/bin/env python3
"""Compose real wide parser/pane/field code with serviced menu/history/clipboard frames."""
import argparse,hashlib,itertools,json,struct
from pathlib import Path
from unicorn.x86_const import *
from check_command_menu_live import Menu
from check_line_edit_live import Live,Abort
from check_viewport_live import logical
from terminal_memory import inspect_terminal_memory
import check_transport
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Viewer(Menu):
 def interrupt(self,u,n,d):
  if n==0x10 and u.reg_read(UC_X86_REG_AX)>>8==1:
   self.cursor_shape=u.reg_read(UC_X86_REG_CX);return
  return super().interrupt(u,n,d)
def fixture(rows,hidden,profile,right,wrap,protected):
 m=Viewer()
 for name,value in dict(csi_terminal_id=profile,csi_row_count=rows,csi_last_row=rows-1,screen_last_row=rows-1,erase_cell_count=rows*80,terminal_dec_keys=1,ui_flow_suppressed=hidden).items():m.put(name,value)
 m.uc.mem_write(0x449,b'\x03\x50\x00');m.uc.mem_write(0x462,b'\0');m.uc.mem_write(0x484,b'\x18')
 assert m.call('terminal_reset_capture')==0
 assert m.call('terminal_native_width',ax=1,limit=3000000)==0
 size=rows*132;flags=bytearray(size);values=bytearray(size);words=[];carry=0x17
 marks={rows//2*132+17:0x1e,rows//2*132+80:0x2a}
 for i in range(size):
  if i in marks:flags[i]=0x80|(i&1);carry=marks[i]
  values[i]=carry;words.append((carry<<8)|(33+i%90))
 address=m.get('erase_shadow_segment')*16+m.get('erase_shadow_offset')
 m.uc.mem_write(address,struct.pack('<'+'H'*size,*words)+b'\x5a'*(8192-size*2))
 m.uc.mem_write(0xb8000,bytes((i*7+9)&255 for i in range(4000)))
 for row in range(rows):m.uc.mem_write(0xb8000+row*160,struct.pack('<80H',*words[row*132:row*132+80]))
 m.uc.mem_write(m.symbols['screen_attribute_cells'],bytes(flags)+b'\x55'*(4096-size))
 m.uc.mem_write(m.symbols['erase_attribute_values'],bytes(values)+b'\x66'*(4096-size));m.uc.mem_write(m.symbols['screen_line_flags'],bytes(128))
 m.position(rows//2,131 if right else 17)
 for name,value in dict(screen_cursor_wrap=wrap,screen_attribute_checks=protected,attributes_normal_value=0xab27,attributes_current=0x9c,attributes_preset_value=0x4e,attributes_monochrome=0).items():m.put(name,value)
 m.uc.mem_write(m.symbols['csi_erase_attribute'],b'\x17')
 m.seed(b'FROZEN README.NFO\r'+b''.join(f'Row {i:03d} CP437 '.encode()+b'\xdb\r'for i in range(80)))
 return m,address

def equal(m,c,address,other,rows,identity):
 assert logical(m,address,rows)==logical(c,other,rows),(identity,'logical display')
 for name,n in [('screen_attribute_cells',4096),('erase_attribute_values',4096),('screen_line_flags',128)]:
  assert bytes(m.uc.mem_read(m.symbols[name],n))==bytes(c.uc.mem_read(c.symbols[name],n)),(identity,name)
 for name in ['screen_cursor_row','screen_cursor_column','screen_visible_column','screen_previous_row','screen_previous_column','screen_video_offset','screen_attribute_offset','screen_viewport_active','screen_viewport_offset','screen_first_row','screen_last_row','csi_wrap_pending','screen_cursor_wrap','screen_attribute_checks']:
  assert m.get(name)==c.get(name),(identity,name)
 assert bytes(m.uc.mem_read(address+rows*264,8192-rows*264))==bytes(c.uc.mem_read(other+rows*264,8192-rows*264)),(identity,'shadow tail')
 assert bytes(m.uc.mem_read(0xb8000+rows*160,4000-rows*160))==bytes(c.uc.mem_read(0xb8000+rows*160,4000-rows*160)),(identity,'outside content')
 assert m.bios_position==c.bios_position and m.cursor_shape==c.cursor_shape,(identity,'BIOS cursor')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args();binary=a.terminal.resolve();mft=json.loads((binary.parent/'manifest.json').read_text())
 assert mft['native_reset_transaction']and sha(binary)==mft['binary_sha256']
 for name,digest in mft['sources'].items():assert sha(ROOT/name)==digest,name
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map';inspect_terminal_memory(binary,check_transport.MAP)
 cases=0;streams=0;refusals=0
 for (rows,hidden),profile,right,(wrap,protected),key in itertools.product([(1,0),(5,0),(24,0),(25,1)],(4,6),(False,True),[(0,0),(1,0),(1,1)],(0x8400,0x2c00,0x8300)):
  m,address=fixture(rows,hidden,profile,right,wrap,protected);c,other=fixture(rows,hidden,profile,right,wrap,protected);identity=(rows,hidden,profile,right,wrap,protected,key)
  m.key(key);assert m.get('_redisplay_active')==1,(identity,'viewer open')
  assert not m.get('_redisplay_live_ready')
  view=bytes(m.uc.mem_read(0xb8000,4000));frozen=bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'],63000))
  shadow=bytes(m.uc.mem_read(address,8192));m.call('terminal_viewport_admit');assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1
  assert bytes(m.uc.mem_read(address,8192))==shadow and bytes(m.uc.mem_read(0xb8000,4000))==view
  assert m.call('terminal_native_width',ax=0)==1
  refusals+=2
  samples=[b'\x1b[1;132HZ\x1b[6n\x1b[1;1HL',b'\x1b['+str(rows).encode()+b';18H\x1b[3P\x1b[6n']
  if rows>=5:samples.append(b'\x1b[2;4r\x1b[4;18H\x1bD\x1b[2;18H\x1bM\x1b[1;'+str(rows).encode()+b'r')
  for data in samples:
   m.receive(data);Live.feed(c,data)
   assert not m.get('_redisplay_live_ready')and bytes(m.uc.mem_read(0xb8000,4000))==view,(identity,'frozen local frame')
   if key==0x8400:assert bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'],63000))==frozen
   m.call('terminal_redisplay_before');assert m.get('_redisplay_live_ready')==1
   m.call('terminal_viewport_admit');assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&1
   equal(m,c,address,other,rows,identity)
   m.call('terminal_redisplay_idle');assert not m.get('_redisplay_live_ready')
   streams+=1
  if key==0x2c00:
   m.key(0x3b00);assert m.get('_command_menu_active')
   m.key(27);assert m.get('_command_menu_active')
  if cases%2:m.call('terminal_redisplay_stop')
  else:m.key(27)
  assert not m.get('_redisplay_active')and not m.get('_command_menu_active')and not m.get('_clipboard_ui_active')and not m.get('_redisplay_live_ready')
  equal(m,c,address,other,rows,identity);m.drain();c.drain()
  assert bytes(m.tx)==bytes(c.tx),(identity,'wire')
  assert not m.get('uart_rx_dropped')and not m.get('terminal_quit')
  cases+=1
 pending=0
 for(rows,hidden),profile,right in itertools.product([(1,0),(5,0),(24,0),(25,1)],(4,6),(False,True)):
  m,address=fixture(rows,hidden,profile,right,1,1);before=logical(m,address,rows)
  m.put('terminal_parser_active',1);m.key(0x2c00);m.key(0x4d00);m.key(0x4d00)
  assert m.get('terminal_menu_pending')and m.get('terminal_deferred_count')==2 and not m.get('_redisplay_active')
  m.put('terminal_parser_active',0);m.call('terminal_poll_io',limit=3000000);m.call('terminal_poll_io',limit=3000000)
  assert m.get('_command_menu_active')and b'Redisplay history'in m.text(5)
  assert not m.get('terminal_menu_pending')and not m.get('terminal_deferred_count')and not m.tx
  m.call('terminal_redisplay_stop');assert logical(m,address,rows)==before and not m.get('_redisplay_live_ready')
  pending+=1
 invalid=0
 for active,menu,ready in [(0,0,1),(0,1,1),(1,0,2),(2,0,1),(1,2,1)]:
  m,address=fixture(5,0,6,False,1,1)
  for name,value in [('_redisplay_active',active),('_command_menu_active',menu),('_redisplay_live_ready',ready)]:m.put(name,value)
  before=bytes(m.uc.mem_read(address,8192));video=bytes(m.uc.mem_read(0xb8000,4000))
  m.call('terminal_viewport_admit');assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1
  assert bytes(m.uc.mem_read(address,8192))==before and bytes(m.uc.mem_read(0xb8000,4000))==video
  invalid+=1
 typed=0
 for key,right in itertools.product((0x8400,0x2c00,0x8300),(False,True)):
  m,address=fixture(5,0,6,right,1,1);m.key(key)
  view=bytes(m.uc.mem_read(0xb8000,4000));shadow=bytes(m.uc.mem_read(address,8192))
  entry='screen_viewport_leave'if m.get('screen_viewport_active')else'screen_viewport_enter'
  try:m.call(entry)
  except Abort as error:assert error.args==((0x4850 if entry.endswith('leave')else 0x482a),)
  else:raise AssertionError(('overlay admitted for pane copy',key,right))
  assert bytes(m.uc.mem_read(address,8192))==shadow and bytes(m.uc.mem_read(0xb8000,4000))==view
  typed+=1
 result=dict(passed=True,binary_sha256=sha(binary),open_close_cases=cases,live_stream_cases=streams,overlay_copy_and_width_refusals=refusals,typed_overlay_copy_refusals=typed,deferred_menu_cases=pending,invalid_lifecycle_refusals=invalid,sources=mft['sources'],checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' Actual viewer and control replay without a viewer receive identical bytes. Compare complete logical display, metadata/shadow/status guards, pane/cursor caches, BIOS cursor and wire; typed overlay-copy refusal. Hardware modeled; no peer-width or complete child/UI acceptance.')
 (binary.parent/'wide-viewer-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS wide viewers:',cases,'open/close,',streams,'live streams,',refusals,'overlay/width refusals')
if __name__=='__main__':main()
