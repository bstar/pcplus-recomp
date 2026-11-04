#!/usr/bin/env python3
"""Execute actual BIOS/canonical/RIS owner; BIOS/UART boundaries are modeled."""
import argparse,hashlib,json,struct
from types import SimpleNamespace
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
from check_status_transition_live import Transaction
from check_recording_rx_live import ordinary,inject
from check_mouse_keyboard import Owner as MouseBoundary
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Geometry(Transaction):
 def __init__(self,adapter="vga"):
  self.adapter=adapter;self.vrows=25;self.scanlines=400 if adapter=="vga" else 350;self.font_height=16 if adapter=="vga" else 14;self.hardware=[]
  self.mouse_boundary=None
  self.font_refusals=0;self.mode_refusals=0
  super().__init__()
  self.uc.mem_write(0x449,b'\x03\x50\x00');self.uc.mem_write(0x462,b'\0')
  self.uc.mem_write(0x463,struct.pack('<H',0x3d4));self.uc.mem_write(0x489,b'\x90' if adapter=='vga' else b'\x00')
  self.initial_keys=bytes(self.uc.mem_read(self.symbols['terminal_keymap'],948))
  self.initial_tabs=bytes(self.uc.mem_read(self.symbols['terminal_tab_stops'],30))
 def interrupt(self,u,n,d):
  if self.mouse_boundary is not None and (n==0x33 or n==0x21 and (u.reg_read(UC_X86_REG_AX)==0x3533 or u.reg_read(UC_X86_REG_AX)>>8 in (0x48,0x49))):
   return MouseBoundary.interrupt(self.mouse_boundary,u,n,d)
  if n!=0x10:return super().interrupt(u,n,d)
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;al=ax&255;bx=u.reg_read(UC_X86_REG_BX)
  if ah==0xfe or ax==0x6f00:return
  if ah==0x12:
   if bx&255==0x10:
    if self.adapter!='cga':u.reg_write(UC_X86_REG_BX,0x10)
    return
   assert bx&255==0x30
   self.scanlines={0:200,1:350,2:400}[al];self.hardware.append(('scanlines',self.scanlines));return
  if ax==0x1a00:
   if self.adapter=='vga':u.reg_write(UC_X86_REG_AX,0x1a);u.reg_write(UC_X86_REG_BX,8)
   return
  if ah==0:
   if self.mouse_boundary and self.mouse_boundary.allocations and self.get('_terminal_row_geometry_active'):
    assert self.mouse_boundary.driver[:6]==bytes(6),'Mouse callback remained installed during BIOS mode change'
   self.hardware.append(('mode',al))
   if self.mode_refusals:self.mode_refusals-=1;return
   self.mode=al&127;self.columns=80;self.page=0;self.cursor=0;self.shape=0x607
   self.font_height=14 if self.scanlines==350 else 16;self.vrows=self.scanlines//self.font_height
   u.mem_write(0x484,bytes([self.vrows-1]));u.mem_write(0xb8000,b' \x07'*4000);return
  if ah==0x11:
   if self.mouse_boundary and self.mouse_boundary.allocations and self.get('_terminal_row_geometry_active'):
    assert self.mouse_boundary.driver[:6]==bytes(6),'Mouse callback remained installed during font change'
   assert al in (0x11,0x12)
   self.hardware.append(('font',al))
   if self.font_refusals:self.font_refusals-=1;return
   self.font_height=14 if al==0x11 else 8;self.vrows=self.scanlines//self.font_height
   u.mem_write(0x484,bytes([self.vrows-1]));return
  if ah==6:
   cx=u.reg_read(UC_X86_REG_CX);dx=u.reg_read(UC_X86_REG_DX)
   top,left,bottom,right=cx>>8,cx&255,dx>>8,dx&255
   assert 0<=top<=bottom<self.vrows and 0<=left<=right<80
   old=bytes(u.mem_read(0xb8000,8000));fill=bytes([32,bx>>8])*(right-left+1)
   for row in range(top,bottom+1):
    source=((row+al)*80+left)*2
    u.mem_write(0xb8000+(row*80+left)*2,old[source:source+len(fill)] if al and row+al<=bottom else fill)
   return
  return super().interrupt(u,n,d)
 def start_mouse(self):
  driver=bytes((i*19+7)&255 for i in range(256))
  self.mouse_boundary=SimpleNamespace(vector=(0x7000,0x40),driver=driver,size=256,dos_memory=True,events=[],
   allocations={},alloc_fail=False,free_fail=False,request_bytes=None,present=True,corrupt_save=False)
  self.call('_terminal_mouse_bootstrap');self.put('process_memory_released',1)
  assert self.call('_terminal_mouse_start')==0
  assert self.set_rows(0,entry='terminal_rows_mouse_phase_far')==1
 def set_rows(self,rows,flags=0x202,entry='_terminal_row_geometry_set'):
  initial_active=self.get('_terminal_row_geometry_active')
  u=self.uc;seg,off=self.entries[entry];sp=self.offset('terminal_stack_top')-6
  u.mem_write(self.data_base+sp,struct.pack('<3H',self.return_offset,self.code_segment,rows))
  u.mem_write(self.data_base+sp-3000,b'GUARD!')
  for r,v in ((UC_X86_REG_CS,self.base_segment+seg),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),
   (UC_X86_REG_SP,sp),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x5678),(UC_X86_REG_DI,0x6789),(UC_X86_REG_EFLAGS,flags)):u.reg_write(r,v)
  self.returned=False;u.emu_start(self.symbols[entry],0,count=5000000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4 and u.reg_read(UC_X86_REG_BP)==0xbabe
  assert u.reg_read(UC_X86_REG_SI)==0x5678 and u.reg_read(UC_X86_REG_DI)==0x6789
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds
  assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x600
  assert bytes(u.mem_read(self.data_base+sp-3000,6))==b'GUARD!'
  assert self.get('_terminal_row_geometry_active')==initial_active
  return u.reg_read(UC_X86_REG_AX)
 def full(self):
  words={o:int.from_bytes(self.uc.mem_read(self.data_base+o,2),'little') for o in self.values()}
  byte_table=self.symbols['reset_byte_addresses'];byte_end=self.symbols['reset_byte_addresses_end']
  bs={int.from_bytes(self.uc.mem_read(a,2),'little'):0 for a in range(byte_table,byte_end,2)}
  bs={o:bytes(self.uc.mem_read(self.data_base+o,1)) for o in bs}
  planes={n:bytes(self.uc.mem_read(self.symbols[n],size)) for n,size in [('screen_attribute_cells',4096),('erase_attribute_values',4096),('screen_line_flags',128),('erase_shadow_cells',8192),('terminal_keymap',948),('terminal_tab_stops',30),('ansi_parameters',32),('terminal_history_buffer',63000)]}
  return dict(words=words,bytes=bs,defaults=self.values(),planes=planes,video=bytes(self.uc.mem_read(0xb8000,8000)),
   ui=tuple(self.get(n) for n in ('ui_window_rows','ui_flow_video_base','ui_flow_coordinate_base','ui_flow_suppressed')),
   hardware=(self.mode,self.vrows,self.scanlines,self.font_height,self.cursor,self.shape),tx=bytes(self.tx))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 transport.BINARY=a.terminal.resolve();transport.MAP=transport.BINARY.parent/'terminal.map'
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((transport.BINARY.parent/'manifest.json').read_text());assert manifest['experimental_row_geometry_owner']
 cases=[]
 def done(name,count=1):cases.append(dict(case=name,inputs=count,passed=True));print('PASS',name,count,flush=True)
 m=Geometry();history=m.full()['planes']['terminal_history_buffer']
 for rows in (28,43,50,25):
  before_history=bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'],63000));calls=len(m.calls)
  assert m.set_rows(rows)==0,rows
  assert bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'],63000))==before_history and len(m.calls)==calls
  assert m.vrows==m.get('ui_window_rows')==rows and m.get('csi_row_count')==m.value('csi_row_count')==rows-1
  assert m.get('csi_last_row')==m.get('screen_last_row')==m.get('csi_origin_bottom')==rows-2
  assert m.get('erase_cell_count')==(rows-1)*80
  assert m.get('ui_flow_video_base')==(rows-1)*160 and m.get('ui_flow_coordinate_base')==(rows-1)*256
  video=bytes(m.uc.mem_read(0xb8000,rows*160));assert video[:(rows-1)*160]==b' \x07'*((rows-1)*80)
  assert b'Alt-Z FOR HELP' in video[(rows-1)*160::2]
  assert bytes(m.uc.mem_read(m.symbols['erase_shadow_cells'],rows*160))==video
  ordinary(m,b'\x1b[99;1HQ\x1b[6n');m.drain();assert bytes(m.tx).endswith(f'\x1b[{rows-1};2R'.encode())
  m.call('csi_reset_terminal',limit=1000000);assert m.get('csi_row_count')==rows-1 and m.get('screen_cursor_row')==0
 assert bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'],63000))!=history # Parsed Qs were recorded.
 done('real-BIOS-chain-canonical-status-shadow-parser-CPR-and-RIS',4)
 m=Geometry();assert m.invoke()==0
 for rows in (28,43,50,25):
  assert m.set_rows(rows)==0 and m.get('ui_flow_suppressed')==1
  assert m.get('csi_row_count')==m.value('csi_row_count')==rows
  assert bytes(m.uc.mem_read(0xb8000,rows*160))==b' \x07'*(rows*80)
 done('hidden-status-retained-through-physical-row-resets',4)
 for adapter in ('ega','cga'):
  for rows in (25,28,43,50):
   m=Geometry(adapter);before=m.full();supported=rows==25 or adapter=='ega' and rows==43
   assert m.set_rows(rows)==(0 if supported else 3),(adapter,rows)
   if supported:assert m.vrows==rows and m.get('csi_row_count')==m.value('csi_row_count')==rows-1
   else:assert m.full()==before
 done('adapter-capability-admission-and-EGA-canonical-reset',8)
 for rows in (0,24,26,51,0x12b,0xffff):
  m=Geometry();before=m.full();assert m.set_rows(rows)==1 and m.full()==before
 done('invalid-requests-preserve-full-state',6)
 owners=['_terminal_row_geometry_active','_terminal_status_toggle_active','terminal_program_active','terminal_program_pending','terminal_aspect_active','terminal_parser_active','terminal_macro_active','terminal_ansi_wait_active','terminal_monitor_active','terminal_snapshot_active','terminal_screen_print_active','terminal_controller_active','terminal_transfer_active','terminal_transfer_pending','uart_break_hold','terminal_tx_count','_redisplay_active','_redisplay_live_ready','_redisplay_export_pending','_redisplay_search_pending','_command_menu_active','_terminal_elapsed_view_active','terminal_screen_pause_active','terminal_manual_init_active','reset_bank_busy','terminal_auto_answer_notice_active','terminal_script_overlay_visible','_clipboard_ui_active','_clipboard_ui_visible','_clipboard_paste_pending','terminal_menu_pending','connection_state']
 for name in owners:
  m=Geometry();m.put(name,1);before=m.full();assert m.set_rows(43)==3 and m.full()==before,name
 done('live-owner-and-online-refusals',len(owners))
 invalid=[('screen_columns',40),('screen_video_row_bytes',264),('screen_attribute_row_bytes',132),('screen_last_column',78),('erase_shadow_offset',1),('screen_attributes_base',0),('ui_window_rows',26),('ui_flow_video_base',4000),('ui_flow_coordinate_base',0),('csi_row_count',25),('erase_cell_count',0),('screen_previous_row',1),('screen_previous_column',1),('screen_video_offset',2),('screen_attribute_offset',1),('csi_saved_column',80),('terminal_tab_wrap',1),('terminal_parity',5),('terminal_data_bits',4),('terminal_stop_bits',3),('terminal_baud_low',17)]
 for name,value in invalid:
  m=Geometry();m.put(name,value);before=m.full();assert m.set_rows(43)==3 and m.full()==before,name
 for name in ('terminal_browser_screen_owned','terminal_editor_screen_owned'):
  m=Geometry();m.put(name,1,1);before=m.full();assert m.set_rows(43)==3 and m.full()==before
 for flags in (0x2,0x602):
  m=Geometry();before=m.full();assert m.set_rows(43,flags)==3 and m.full()==before
 m=Geometry();m.put('reset_ready',0);before=m.full();assert m.set_rows(43)==2 and m.full()==before
 m=Geometry();m.set_baseline('csi_last_row',99);before=m.full();assert m.set_rows(43)==3 and m.full()==before
 done('invalid-layout-config-ABI-and-baseline-refuse-before-BIOS-change',len(invalid)+6)
 for name,value in [('screen_video_row_bytes',264),('text_video_segment',0xb000)]:
  m=Geometry();m.put(name,value);before=m.full()
  assert m.set_rows(0,entry='terminal_status_notice_refresh')==3 and m.full()==before
 m=Geometry();assert m.set_rows(43)==0;m.uc.mem_write(0xb8000+42*160,b'?\x07'*80)
 assert m.set_rows(0,entry='terminal_status_notice_refresh')==0
 assert b'Alt-Z FOR HELP' in bytes(m.uc.mem_read(0xb8000+42*160,160))[::2]
 done('generalized-status-retains-old-video-guards-and-repaints-real-bottom-row',3)
 m=Geometry();ordinary(m,b'\x1b[31mPEER');m.uc.mem_write(m.symbols['terminal_keymap'],b'K'*948);m.uc.mem_write(m.symbols['terminal_tab_stops'],b'T'*30)
 assert m.set_rows(43)==0 and m.get('attributes_current')==m.value('attributes_current')
 assert bytes(m.uc.mem_read(m.symbols['terminal_keymap'],948))==m.initial_keys
 assert bytes(m.uc.mem_read(m.symbols['terminal_tab_stops'],30))==m.initial_tabs
 done('real-RIS-restores-configured-profile-without-recapturing-peer-state')
 for rows in (25,43):
  m=Geometry();assert m.set_rows(rows)==0
  ordinary(m,b'\x1b[4;12H\x1b[31mOLD\x1b7')
  m.uc.mem_write(m.symbols['terminal_keymap'],b'K'*948);m.uc.mem_write(m.symbols['terminal_tab_stops'],b'T'*30)
  before=m.full();seen=[]
  def fail(u,address,size,data):
   if address==m.symbols['terminal_status_notice_refresh']:seen.append(True);m.put('terminal_parity',5)
  hook=m.uc.hook_add(UC_HOOK_CODE,fail)
  try:assert m.set_rows(50)==4
  finally:m.uc.hook_del(hook)
  m.put('terminal_parity',0);assert seen and m.full()==before
 done('late-renderer-failure-restores-BIOS-all-live-defaults-full-planes-and-keys',2)
 m=Geometry();m.populate();before=m.full();drawn=[];start=m.symbols['status_renderer_refresh'];end=m.symbols['status_sprintf']
 def after_draw(u,address,size,data):
  if start<=address<end and bytes(u.mem_read(address,1))==b'\xa1':
   drawn.append(bytes(u.mem_read(0xb8000,8000))!=before['video']);m.put('status_error',3)
 hook=m.uc.hook_add(UC_HOOK_CODE,after_draw)
 try:assert m.set_rows(50)==4
 finally:m.uc.hook_del(hook)
 assert drawn==[True] and m.full()==before
 done('post-draw-error-restores-every-owned-plane-and-BIOS-cursor')
 m=Geometry()
 for rows in (43,25):assert m.set_rows(rows)==0
 for request in (1,0):
  assert m.call('terminal_native_width',ax=request,limit=4000000)==0
  assert m.get('screen_attribute_row_bytes')==(132 if request else 80)
 # Native width leaves its viewport-active latch set even after narrow mode.
 # Preserve the row owner's explicit refusal; genuine configured RIS retires it.
 assert m.set_rows(28)==3
 m.call('csi_reset_terminal',limit=1000000)
 assert m.set_rows(28)==0
 done('shared-workspace-reinitialized-by-width-and-reused-by-row-owner')
 m=Geometry();before=m.full();m.font_refusals=1;assert m.set_rows(50)==4 and m.full()==before
 done('BIOS-font-refusal-rolls-back-after-verified-baseline-fallback')
 m=Geometry();assert m.set_rows(43)==0;armed=[]
 def fatal(u,address,size,data):
  if address==m.symbols['terminal_status_notice_refresh']:
   armed.append(True);m.put('terminal_parity',5);m.font_refusals=1
 hook=m.uc.hook_add(UC_HOOK_CODE,fatal)
 try:assert m.set_rows(50)==5
 finally:m.uc.hook_del(hook)
 assert armed and m.get('terminal_quit')==1 and m.get('terminal_exit_code')==2 and m.get('csi_unimplemented_service')==0x6ef6
 done('unrestorable-hardware-requests-existing-fatal-shutdown')
 m=Geometry();inject(m,b'\x1b[49;1HQ\x1b[6n');queued=tuple(m.get(n) for n in ('uart_rx_count','uart_rx_read','uart_rx_write'))
 assert m.set_rows(50)==0 and tuple(m.get(n) for n in ('uart_rx_count','uart_rx_read','uart_rx_write'))==queued
 ordinary(m,b'');m.drain();assert bytes(m.tx).endswith(b'\x1b[49;2R') and bytes(m.uc.mem_read(0xb8000+48*160,1))==b'Q'
 done('queued-UART-preserved-until-parser-consumes-new-geometry')
 for hard in (False,True):
  m=Geometry();payload=bytes(range(256))*13+bytes(range(248)) if hard else b'\x1b[49;1H'+b'A'*512+b'\x1b[6n'
  if hard:m.put('uart_hardware_flow',1)
  staged=[]
  def arriving(u,address,size,data):
   if address==m.symbols['drows_native_display_select_rows'] and not staged:
    assert m.get('_terminal_row_geometry_active')==1;staged.append(True);m.rx.extend(payload)
  hook=m.uc.hook_add(UC_HOOK_CODE,arriving)
  try:assert m.set_rows(50)==0
  finally:m.uc.hook_del(hook)
  assert staged and not m.rx and m.get('uart_rx_count')==len(payload) and not m.get('uart_rx_dropped')
  if hard:
   assert not m.mcr&2,'Driver high-water RTS hold lost during geometry transaction'
   observed=bytes(m.call('uart_receive_byte') for _ in payload);assert observed==payload
   m.call('uart_poll_flow');assert m.mcr&2 and not m.get('uart_rx_count')
  else:
   ordinary(m,b'');m.drain();assert bytes(m.tx).endswith(b'\x1b[49;33R')
 done('actual-UART-ISR-arrival-during-BIOS-work-preserves-parser-and-HARD-watermarks',2)
 m=Geometry();m.start_mouse();allocations=dict(m.mouse_boundary.allocations)
 for rows in (43,25):
  assert m.set_rows(rows)==0 and m.set_rows(0,entry='terminal_rows_mouse_phase_far')==1
  assert m.mouse_boundary.allocations==allocations and m.mouse_boundary.driver[:6]!=bytes(6)
 done('real-mouse-owner-suspends-callback-before-font-change-and-resumes-after',2)
 m.put('mouse_count',1);before=m.full();assert m.set_rows(43)==3 and m.full()==before and m.get('mouse_count')==1
 m.put('mouse_count',0);assert m.set_rows(0,entry='_terminal_mouse_pause_far')==0
 before=m.full();assert m.set_rows(43)==3 and m.full()==before
 assert m.set_rows(0,entry='_terminal_mouse_resume_far')==0
 done('pending-mouse-input-and-foreign-suspended-owner-refuse',2)
 for button,count,code,expected in [(1,1,4,[13]),(0,2,1,[0x4d00,0x4d00])]:
  m=Geometry();m.start_mouse();staged=[]
  def late_input(u,address,size,data):
   if address==m.symbols['_terminal_mouse_pause_far'] and not staged:
    staged.append(True);m.put('mouse_button_pending',button);m.put('mouse_count',count);m.put('mouse_code',code)
  hook=m.uc.hook_add(UC_HOOK_CODE,late_input)
  try:assert m.set_rows(43)==0
  finally:m.uc.hook_del(hook)
  assert staged and m.get('mouse_count')==count and m.get('mouse_code')==code
  assert [m.call('keyboard_read') for _ in expected]==expected and not m.get('mouse_count')
 done('mouse-input-arriving-at-pause-boundary-survives-init-and-native-consumption',2)
 m=Geometry();m.start_mouse();m.mouse_boundary.vector=(0x7001,0x40);before=m.full()
 assert m.set_rows(43)==6 and m.get('terminal_quit')==1 and m.get('terminal_exit_code')==14
 assert m.full()==before and m.mouse_boundary.allocations and m.set_rows(0,entry='terminal_rows_mouse_phase_far')==3
 done('failed-mouse-pause-restores-defaults-and-requests-existing-quarantine-shutdown')
 m=Geometry();m.start_mouse();injected=[]
 def mouse_failure(u,address,size,data):
  if address==m.symbols['terminal_status_notice_refresh']:
   injected.append(True);m.mouse_boundary.present=False
 hook=m.uc.hook_add(UC_HOOK_CODE,mouse_failure)
 try:assert m.set_rows(43)==6
 finally:m.uc.hook_del(hook)
 assert injected and m.get('terminal_quit')==1 and m.get('terminal_exit_code')==14
 assert m.vrows==43 and m.get('csi_row_count')==42 and m.mouse_boundary.allocations
 assert m.set_rows(0,entry='terminal_rows_mouse_phase_far')==3
 done('failed-mouse-resume-keeps-coherent-geometry-and-quarantined-storage')
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 result=dict(passed=True,terminal_sha256=sha(transport.BINARY),manifest_sha256=sha(transport.BINARY.parent/'manifest.json'),cases=cases,
  checker_sha256=sha(Path(__file__)),scope=__doc__+' Actual linked C/ASM/native BIOS request chains, full rollback, RIS/status/parser and UART IRQ code execute. BIOS effects, DOS allocations, INT33 driver/vector boundaries and failure responses modeled; mouse arrival seeds native pending data at the pause boundary, not physical IRQ timing. Renderer fault changes an input at real boundary. No function/instruction/return patch, ordinary key binding, online/BBS or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
