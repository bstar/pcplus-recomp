#!/usr/bin/env python3
"""Check actual native width projection, commit and rollback with hardware modeled."""
import argparse,hashlib,json,struct,itertools
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport
from check_terminal_reset_live import Live,Abort
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Model(Live):
 def __init__(self):
  self.bios_cursor=0x0511;self.bios_shape=0x0607
  super().__init__()
 def call(self,name,*args,**kwargs):
  if name=='terminal_native_width':
   for register,value in [(UC_X86_REG_BX,0x9876),(UC_X86_REG_CX,0x4567),(UC_X86_REG_DX,0xabcd)]:self.uc.reg_write(register,value)
  return super().call(name,*args,**kwargs)
 def interrupt(self,u,n,d):
  ax=u.reg_read(UC_X86_REG_AX)
  if n==0x10:
   if ax>>8==3:
    u.reg_write(UC_X86_REG_DX,self.bios_cursor);u.reg_write(UC_X86_REG_CX,self.bios_shape);return
   if ax>>8==2:self.bios_cursor=u.reg_read(UC_X86_REG_DX)
   if ax>>8==1:self.bios_shape=u.reg_read(UC_X86_REG_CX)
  return super().interrupt(u,n,d)
def fixture(profile=6,attribute=7,rows=24,hidden=0):
 m=Model()
 for name,value in dict(csi_terminal_id=profile,attributes_normal_value=attribute,csi_row_count=rows,
  csi_last_row=rows-1,screen_last_row=rows-1,csi_origin_bottom=rows-1,erase_cell_count=rows*80,terminal_dec_keys=1,
  ui_flow_suppressed=hidden).items():m.put(name,value)
 m.uc.mem_write(0x449,b'\x03\x50\x00');m.uc.mem_write(0x462,b'\0');m.uc.mem_write(0x484,b'\x18')
 assert m.call('terminal_reset_capture')==0;m.position(min(5,rows-1),17)
 for name,n in [('screen_attribute_cells',4096),('erase_attribute_values',4096),('screen_line_flags',128)]:
  m.uc.mem_write(m.symbols[name],bytes((i*13+5)&255 for i in range(n)))
 shadow=m.get('erase_shadow_segment')*16+m.get('erase_shadow_offset')
 m.uc.mem_write(shadow,bytes((i*7+3)&255 for i in range(8192)))
 m.uc.mem_write(m.symbols['terminal_tab_stops'],b'\x19'*30)
 return m,shadow
def near(m):return bytes(m.uc.mem_read(m.data_base,m.offset('terminal_stack_top')-m.stack_bytes))
def abi(m):
 for register,want in [(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_ES,0xb800),
  (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),
  (UC_X86_REG_BX,0x9876),(UC_X86_REG_CX,0x4567),(UC_X86_REG_DX,0xabcd)]:assert m.uc.reg_read(register)==want,(register,want)
 assert m.uc.reg_read(UC_X86_REG_EFLAGS)&0xffff==0x202
def inject(m,payload,at):
 fired=[]
 def hook(u,address,size,_):
  if fired or address!=m.symbols[at]:return
  fired.append(True);assert u.reg_read(UC_X86_REG_SS)!=m.ds
  m.rx.extend(payload);sp=u.reg_read(UC_X86_REG_SP)-6;ss=u.reg_read(UC_X86_REG_SS)
  frame=struct.pack('<3H',u.reg_read(UC_X86_REG_IP),u.reg_read(UC_X86_REG_CS),u.reg_read(UC_X86_REG_EFLAGS)&65535)
  u.mem_write(ss*16+sp,frame);u.reg_write(UC_X86_REG_SP,sp)
  u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)&~0x300)
  u.reg_write(UC_X86_REG_CS,m.code_segment);u.reg_write(UC_X86_REG_IP,m.symbols['uart_receive_interrupt']-m.code_base)
 m.uc.hook_add(UC_HOOK_CODE,hook);return fired
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text())
 assert manifest['native_reset_transaction']and sha(binary)==manifest['binary_sha256']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 memory=inspect_terminal_memory(binary,binary.parent/'terminal.map')
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map'
 successes=0;failures=0;refusals=0;row_cases=0;payload=bytes(range(256))*2
 # The independent contract lists only display fields that this operation may
 # commit. Full near-data comparison catches accidental baseline/parser writes.
 writable=['attributes_current','screen_attribute_row_bytes','screen_last_column','erase_cell_count',
  'screen_cursor_row','screen_cursor_column','screen_visible_column','screen_previous_row','screen_previous_column',
  'screen_video_offset','screen_attribute_offset','screen_viewport_enabled','screen_viewport_active',
  'screen_viewport_offset','screen_viewport_left','csi_saved_row','csi_saved_column','csi_wrap_pending','cursor_state_saved_3342','csi_origin_row','csi_origin_bottom']
 for profile in (4,6):
  for attr in (7,0x1e):
   m,shadow=fixture(profile,attr)
   for request in (1,1,0,0,1):
    if m.get('screen_viewport_enabled'):m.position(23,131)
    before=near(m);oldshadow=bytes(m.uc.mem_read(shadow,8192));video=bytes(m.uc.mem_read(0xb8000,4000))
    ui_before={name:bytes(m.uc.mem_read(m.base+item['start_linear'],4000))for name,item in memory['ui_screen_buffers'].items()}
    assert m.call('terminal_native_width',ax=request,limit=2000000)==0
    abi(m);columns=132 if request else 80
    assert (m.get('screen_attribute_row_bytes'),m.get('screen_last_column'),m.get('erase_cell_count'))==(columns,columns-1,columns*24)
    assert (m.get('screen_viewport_enabled'),m.get('screen_viewport_active'),m.get('screen_viewport_offset'),m.get('screen_viewport_left'))==(request,1,0,52 if request else 0)
    assert m.get('attributes_current')==attr and m.get('screen_cursor_row')==m.get('screen_cursor_column')==0
    assert bytes(m.uc.mem_read(0xb8000,3840))==bytes([32,attr])*1920
    assert bytes(m.uc.mem_read(0xb8000+3840,160))==video[3840:]
    for name,item in memory['ui_screen_buffers'].items():
     observed=bytes(m.uc.mem_read(m.base+item['start_linear'],4000))
     assert observed==(video[:3840]+ui_before[name][3840:]if name in('program_screen','browser_screen')else ui_before[name]),name
    after=near(m);mask=set()
    for name in writable:mask.update(range(m.offset(name),m.offset(name)+2))
    for name,n in [('screen_attribute_cells',3168),('erase_attribute_values',3168),('screen_line_flags',128),('terminal_tab_stops',30)]:mask.update(range(m.offset(name),m.offset(name)+n))
    assert all(x==y for i,(x,y)in enumerate(zip(before,after))if i not in mask),'Unowned near data changed'
    assert bytes(m.uc.mem_read(shadow+6336,1856))==oldshadow[6336:]
    expected=bytes(range(0,columns,8))+b'\xfe'*(30-len(range(0,columns,8)))
    assert bytes(m.uc.mem_read(m.symbols['terminal_tab_stops'],30))==expected
    if request:
     assert bytes(m.uc.mem_read(shadow,6336))==bytes([32,attr])*3168
     # Use actual cursor/pane/parser consumers immediately after commit.
     m.feed(b'\x1b[24;132HZ\x1b[1;1HL')
     assert m.get('screen_viewport_active')==1 and m.get('screen_cursor_column')==1
    successes+=1
   m.call('csi_reset_terminal');assert m.get('screen_attribute_row_bytes')==80 and m.get('csi_row_count')==24
 for rows,hidden,request in [(24,0,0),(24,0,1),(25,0,1),(25,1,1),(1,0,1)]:
  m,shadow=fixture(rows=rows,hidden=hidden);control,_=fixture(rows=rows,hidden=hidden);control.receive_irq(payload)
  fired=inject(m,payload,'reset_live_prepare')
  assert m.call('terminal_native_width',ax=request,limit=2000000)==0
  assert fired and m.get('uart_rx_count')==512 and not m.rx
  for name,n in [('uart_rx_buffer',4096),('uart_rx_count',2),('uart_rx_write',2),('uart_rx_read',2),('uart_rx_dropped',2)]:
   assert bytes(m.uc.mem_read(m.symbols[name],n))==bytes(control.uc.mem_read(control.symbols[name],n)),name
  abi(m);successes+=1
 # Independent row/ownership contract: a visible physical status row reserves
 # row25. Legacy narrow25 therefore adopts24; a hidden status permits all25.
 for rows in (1,5,24,25):
  for hidden in (0,1):
   for profile in (4,6):
    for origin in (0,1):
     for restricted in range(2 if rows>=5 else 1):
      m,shadow=fixture(profile,rows=rows,hidden=hidden)
      if restricted:
       m.put('screen_first_row',1);m.put('screen_last_row',rows-2);m.put('csi_origin_row',1);m.put('csi_origin_bottom',rows-2)
      m.put('csi_origin_mode',origin);m.position(rows-2 if restricted and origin else rows-1,79)
      m.put('csi_wrap_pending',1);m.feed(b'\x1b7')
      baseline_rows=rows;target=24 if rows==25 and not hidden else rows
      for request in (1,0):
       video=bytes(m.uc.mem_read(0xb8000,4000));tail=bytes(m.uc.mem_read(shadow+target*264,8192-target*264))
       assert m.call('terminal_native_width',ax=request,limit=2000000)==0,(rows,hidden,origin,restricted,request)
       abi(m);width=132 if request else 80
       assert(m.get('csi_row_count'),m.get('csi_last_row'),m.get('screen_first_row'),m.get('screen_last_row'))==(target,target-1,0,target-1)
       assert m.get('erase_cell_count')==width*target and m.get('csi_origin_mode')==origin
       assert(m.get('csi_origin_row'),m.get('csi_origin_bottom'))==(0,target-1)
       assert not m.get('csi_wrap_pending')and not m.get('cursor_state_saved_3342')
       assert m.get('csi_saved_row')<target and m.get('csi_saved_column')<width
       assert bytes(m.uc.mem_read(0xb8000,target*160))==b' \x07'*(target*80)
       assert bytes(m.uc.mem_read(0xb8000+target*160,4000-target*160))==video[target*160:]
       assert bytes(m.uc.mem_read(shadow+target*264,8192-target*264))==tail
       if request:
        assert bytes(m.uc.mem_read(shadow,target*264))==b' \x07'*(target*132)
        m.feed(b'\x1b8X')
        assert m.get('screen_cursor_row')==m.get('csi_saved_row')and m.get('screen_cursor_column')==80
        m.feed(b'\x1b['+str(target).encode()+b';132HZ\x1b7')
        assert m.get('csi_saved_column')==131 and m.get('cursor_state_saved_3342')==1
       else:
        m.feed(b'\x1b8')
        assert m.get('screen_cursor_row')==target-1 and m.get('screen_cursor_column')==79 and not m.get('csi_wrap_pending')
       row_cases+=1
      m.call('csi_reset_terminal')
      assert(m.get('csi_row_count'),m.get('screen_first_row'),m.get('screen_last_row'))==(baseline_rows,0,baseline_rows-1)
 for (rows,hidden),fault in itertools.product([(24,0),(25,0),(25,1),(1,0)],('metadata','allocation','readonly','plane_pointer','cursor')):
  m,shadow=fixture(rows=rows,hidden=hidden);control,_=fixture(rows=rows,hidden=hidden)
  for state in (m,control):
   state.position(rows-1,79);state.put('csi_wrap_pending',1);state.feed(b'\x1b7')
  control.receive_irq(payload);expected=near(control);target=24 if rows==25 and not hidden else rows
  oldshadow=bytes(m.uc.mem_read(shadow,8192));video=bytes(m.uc.mem_read(0xb8000,4000));cursor=m.bios_cursor;shape=m.bios_shape
  fired=inject(m,payload,'reset_live_prepare');changed=[];status=bytes([ord('S'),0x4f])*80
  def corrupt(u,at,size,_):
   hook_target='nreset_reset_bank_allocate'if fault=='allocation'else'reset_live_validate'
   if changed or at!=m.symbols[hook_target]:return
   changed.append(True);u.mem_write(0xb8000+3840,status)
   if fault=='allocation':
    ss=u.reg_read(UC_X86_REG_SS);sp=u.reg_read(UC_X86_REG_SP);u.mem_write(ss*16+sp+2,struct.pack('<H',6338))
   else:
    field,value={'metadata':('screen_attribute_row_bytes',133),'readonly':('csi_terminal_id',8),
     'plane_pointer':('screen_attributes_base',0),'cursor':('screen_previous_row',target)}[fault]
    bank=m.base+memory['native_reset_bank_start'];u.mem_write(bank+m.symbols['nreset_'+field]-m.base,struct.pack('<H',value))
  m.uc.hook_add(UC_HOOK_CODE,corrupt)
  assert m.call('terminal_native_width',ax=1,limit=2000000)==3
  assert fired and changed and m.get('uart_rx_count')==512 and not m.rx
  assert near(m)==expected and bytes(m.uc.mem_read(shadow,8192))==oldshadow
  expected_video=video[:3840]+status
  expected_video=video[:target*160]+expected_video[target*160:]
  assert bytes(m.uc.mem_read(0xb8000,4000))==expected_video
  assert (m.bios_cursor,m.bios_shape)==(cursor,shape);abi(m)
  assert m.call('terminal_native_width',ax=1,limit=2000000)==0,'Failed transaction did not release ownership'
  failures+=1
 owners=['terminal_program_active','terminal_program_pending','terminal_macro_active','terminal_monitor_active',
  'terminal_snapshot_active','terminal_screen_print_active','terminal_controller_active','terminal_ansi_wait_active',
  'terminal_transfer_active','terminal_transfer_pending','_redisplay_active','_redisplay_export_pending',
  '_redisplay_search_pending','_command_menu_active']
 invalid={name:1 for name in owners}
 invalid.update(terminal_browser_screen_owned=1,csi_row_count=25,screen_cursor_wrap=2,screen_attribute_checks=2,terminal_tab_wrap=1,
  screen_vertical_attribute_check=1,erase_protection_mode=2,screen_columns=132,text_video_segment=0xb000,
  text_cga_status_port=0x3da,screen_viewport_enabled=1,screen_attributes_base=0,
  erase_attribute_values_base=0,erase_shadow_segment=0,screen_cursor_column=80,csi_terminal_id=8,reset_ready=0)
 invalid.update(terminal_dec_keys=0,screen_use_bios_cursor=0,csi_last_row=24,screen_last_row=24,
  screen_video_row_bytes=264,screen_viewport_right=131,erase_shadow_offset=1,ui_flow_region_cells=132,
  ui_flow_video_base=0,ui_flow_coordinate_base=0,erase_cell_count=2000,screen_last_column=80,
  screen_viewport_active=2,screen_viewport_left=52,screen_viewport_offset=52,
  screen_reverse_wrap_blocked=1,screen_cursor_row=24,connection_state=1,reset_live_active=1,reset_bank_busy=1)
 invalid.update(screen_previous_row=24,screen_previous_column=80,screen_visible_column=80,screen_video_offset=1,screen_attribute_offset=1)
 for name,value in invalid.items():
  m,shadow=fixture();m.put(name,value,1 if name=='terminal_browser_screen_owned'else 2);before=near(m);video=bytes(m.uc.mem_read(0xb8000,4000))
  cache=m.base+memory['native_reset_bank_start'];m.uc.mem_write(cache,b'\x5a'*65504)
  assert m.call('terminal_native_width',ax=1)==1,name
  assert near(m)==before and bytes(m.uc.mem_read(0xb8000,4000))==video,name
  assert bytes(m.uc.mem_read(cache,65504))==b'\x5a'*65504,name
  refusals+=1
 for flags,foreign in [(0x602,False),(0x2,False),(0x202,True)]:
  m,shadow=fixture();before=near(m);video=bytes(m.uc.mem_read(0xb8000,4000));changed=[]
  def caller(u,at,size,_):
   if changed or at!=m.symbols['terminal_native_width_far']:return
   changed.append(True);u.reg_write(UC_X86_REG_EFLAGS,flags)
   if foreign:u.reg_write(UC_X86_REG_DS,m.ds+1)
  m.uc.hook_add(UC_HOOK_CODE,caller)
  assert m.call('terminal_native_width',ax=1)==1
  assert near(m)==before and bytes(m.uc.mem_read(0xb8000,4000))==video
  assert m.uc.reg_read(UC_X86_REG_EFLAGS)&65535==flags
  assert m.uc.reg_read(UC_X86_REG_DS)==m.ds+int(foreign);refusals+=1
 for function,request in [('terminal_native_width',2),('terminal_native_width',65535),('reset_bank_call',0x100),('reset_bank_call',0x101)]:
  m,shadow=fixture();before=near(m);cache=m.base+memory['native_reset_bank_start'];m.uc.mem_write(cache,b'\x5a'*65504)
  assert m.call(function,ax=request)==1
  assert near(m)==before and bytes(m.uc.mem_read(cache,65504))==b'\x5a'*65504
  refusals+=1
 m,_=fixture()
 m.feed(b'\x1b[?3h');assert m.get('screen_attribute_row_bytes')==132
 m.feed(b'\x1b[?3l');assert m.get('screen_attribute_row_bytes')==80
 result=dict(passed=True,binary_sha256=sha(binary),successes=successes,general_row_commits=row_cases,native_fault_rollbacks=failures,
  refusals=refusals,real_UART_ISR_in_private_context=True,root_near_and_owned_shadow_preserved_on_failure=True,
  status_row_update_preserved=True,RIS_baseline_preserved=True,peer_width_still_unbound=False,peer_width_parser_roundtrip=True,sources=manifest['sources'],memory_layout=memory,
  checker_sha256=sha(Path(__file__)),original_inputs=[],scope=__doc__+' Plain profiles4/6,1..25 rows, status-aware legacy startup normalization, full-margin reset and saved/deferred-wrap bounds. A normal parser mode3 roundtrip is checked. Faults explicitly mutate native allocation arguments/results; real error/validation/rollback executes. No actual DOS transaction or broad UI/protected-field/BBS acceptance implied.')
 (binary.parent/'reset-live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS native live transaction:',successes,'commits,',row_cases,'row/margin/save cases,',failures,'IRQ/fault rollbacks,',refusals,'refusals')
if __name__=='__main__':main()
