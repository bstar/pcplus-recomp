#!/usr/bin/env python3
"""Execute optional offline status transaction, actual parser/RIS and rollback.
Actual C/ASM parent helpers; BIOS/UART boundaries modeled. No online size policy.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
from check_recording_ui_live import UI
from check_recording_rx_live import ordinary,inject
from check_reset_rows_live import Defaults,CHANGES
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Transaction(Defaults):
 def __init__(self):
  super().__init__();self.put('connection_state',0)
  self.put('terminal_baud_low',38400);self.put('terminal_baud_high',0)
  self.put('terminal_parity',0);self.put('terminal_data_bits',8);self.put('terminal_stop_bits',1)
 def invoke(self):
  initial_active=self.get('_terminal_status_toggle_active')
  u=self.uc;manifest=json.loads((transport.BINARY.parent/'manifest.json').read_text())
  cs=self.base_segment+next(x['relative_segment'] for x in manifest['memory_layout']['code_segments'] if x['name']=='CONFIG_CODE')
  sp=self.offset('terminal_stack_top')-4
  for r,v in ((UC_X86_REG_CS,cs),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_EFLAGS,0x202)):u.reg_write(r,v)
  u.mem_write(self.data_base+sp,struct.pack('<HH',self.return_offset,self.code_segment));u.mem_write(self.data_base+sp-1500,b'GUARD!')
  self.returned=False;u.emu_start(self.symbols['_terminal_status_toggle'],0,count=1000000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4 and u.reg_read(UC_X86_REG_BP)==0xbabe
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds
  assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==0x200
  assert bytes(u.mem_read(self.data_base+sp-1500,6))==b'GUARD!'
  assert self.get('_terminal_status_toggle_active')==initial_active
  return u.reg_read(UC_X86_REG_AX)
 def video(self):return bytes(self.uc.mem_read(0xb8000,4000))
 def populate(self):
  data=b''.join(bytes([65+r,7+r%8])*80 for r in range(25));self.uc.mem_write(0xb8000,data)
  self.uc.mem_write(self.symbols['screen_attribute_cells'],bytes((i%251 for i in range(2000))))
  self.uc.mem_write(self.symbols['erase_attribute_values'],bytes(((i+19)%251 for i in range(2000))))
  self.uc.mem_write(self.symbols['screen_line_flags'],bytes(range(128)))
  self.uc.mem_write(self.symbols['erase_shadow_cells'],b'\x55\xaa'*2000)
 def snapshot(self):
  fields=CHANGES|{'ui_flow_suppressed','screen_cursor_column','screen_visible_column','screen_previous_column','csi_saved_column','csi_wrap_pending'}
  return dict(hardware_cursor=(self.cursor,self.shape),video=self.video(),words={name:self.get(name) for name in fields},defaults=self.values(),
   flags=bytes(self.uc.mem_read(self.symbols['screen_attribute_cells'],2000)),attributes=bytes(self.uc.mem_read(self.symbols['erase_attribute_values'],2000)),
   lines=bytes(self.uc.mem_read(self.symbols['screen_line_flags'],128)),shadow=bytes(self.uc.mem_read(self.symbols['erase_shadow_cells'],4000)),
   history=bytes(self.uc.mem_read(self.symbols['terminal_history_buffer'],63000)),tx=bytes(self.tx))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 transport.BINARY=a.terminal.resolve();transport.MAP=transport.BINARY.parent/'terminal.map'
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((transport.BINARY.parent/'manifest.json').read_text());assert manifest['experimental_status_owner']
 cases=[]
 def done(name,count=1):cases.append(dict(case=name,inputs=count,passed=True));print('PASS',name,count,flush=True)
 m=Transaction();m.populate();before=m.snapshot();assert m.invoke()==0
 assert m.get('ui_flow_suppressed')==1 and m.get('csi_row_count')==25 and m.get('csi_last_row')==24
 assert m.get('screen_last_row')==m.get('csi_origin_bottom')==24 and m.get('erase_cell_count')==2000
 assert m.video()[:3840]==before['video'][:3840] and m.video()[3840:]==b' \x1e'*80
 assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells']+1920,80))==bytes(80)
 assert m.value('csi_row_count')==25 and m.value('csi_last_row')==24
 assert bytes(m.uc.mem_read(m.symbols['erase_shadow_cells'],4000))==m.video()
 assert m.invoke()==0 and not m.get('ui_flow_suppressed') and m.get('csi_row_count')==24
 assert m.video()[:3840]==before['video'][:3840] and b'Alt-Z FOR HELP' in m.video()[3840::2]
 assert not m.tx and bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'],63000))==before['history']
 done('real-hide-show-bounds-plane-initialization-status-and-history')
 m=Transaction();assert m.invoke()==0
 ordinary(m,b'\x1b[25;1HX\x1b[6n');m.drain();assert b'\x1b[25;2R' in bytes(m.tx) and m.video()[3840]==ord('X')
 m.call('csi_reset_terminal',limit=1000000);assert m.get('csi_row_count')==25 and m.get('csi_last_row')==24
 assert m.invoke()==0
 ordinary(m,b'\x1b[25;1HY\x1b[6n');m.drain();assert bytes(m.tx).endswith(b'\x1b[24;2R') and m.video()[3680]==ord('Y')
 m.call('csi_reset_terminal',limit=1000000);assert m.get('csi_row_count')==24 and m.get('csi_last_row')==23
 done('actual-parser-CPR-clamping-and-RIS-follow-both-effective-sizes')
 for showing in (False,True):
  m=Transaction()
  if showing:assert m.invoke()==0
  ordinary(m,b'\x1b[6;80HA');assert m.get('csi_wrap_pending')==1
  assert m.invoke()==0 and m.get('csi_wrap_pending')==1
  ordinary(m,b'X');assert m.video()[6*160]==ord('X')
  assert m.get('screen_cursor_row')==6 and m.get('screen_cursor_column')==1
 done('pending-deferred-wrap-survives-hide-and-nonscrolling-show',2)
 for custom in (False,True):
  m=Transaction();assert m.invoke()==0;m.populate();m.put('screen_cursor_row',24);m.put('screen_cursor_column',7);m.put('screen_visible_column',7)
  m.put('screen_video_offset',3854);m.put('screen_attribute_offset',1927);m.put('screen_previous_row',24);m.put('screen_previous_column',7);m.put('csi_saved_row',24)
  if custom:m.put('screen_first_row',2);m.put('screen_last_row',10);m.put('csi_origin_row',1);m.put('csi_origin_bottom',20)
  before=m.snapshot();assert m.invoke()==0
  assert m.get('screen_cursor_row')==m.get('screen_previous_row')==m.get('csi_saved_row')==23
  assert m.get('screen_video_offset')==23*160+14 and m.get('screen_attribute_offset')==23*80+7
  assert m.get('screen_previous_column')==m.get('screen_cursor_column')==7
  first,last=(2,10) if custom else (0,24)
  expected=bytearray(before['video']);expected[first*160:last*160]=before['video'][(first+1)*160:(last+1)*160]
  expected[last*160:(last+1)*160]=b' \x07'*80
  assert m.video()[:3840]==expected[:3840],custom
  assert m.get('screen_first_row')==(2 if custom else 0) and m.get('screen_last_row')==(10 if custom else 23)
  assert m.get('csi_origin_bottom')==(20 if custom else 23)
  flags=bytearray(before['flags']);flags[first*80:last*80]=before['flags'][(first+1)*80:(last+1)*80];flags[last*80:(last+1)*80]=bytes(80)
  assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],1920))==flags[:1920]
 done('real-native-scroll-custom-margins-and-saved-cursor-clamp',2)
 owners=['_terminal_status_toggle_active','terminal_program_active','terminal_program_pending','terminal_aspect_active','terminal_parser_active','terminal_macro_active','terminal_ansi_wait_active','terminal_monitor_active','terminal_snapshot_active','terminal_screen_print_active','terminal_controller_active','terminal_transfer_active','terminal_transfer_pending','uart_break_hold','terminal_tx_count','_redisplay_active','_redisplay_live_ready','_redisplay_export_pending','_redisplay_search_pending','_command_menu_active','_terminal_elapsed_view_active','terminal_screen_pause_active','terminal_manual_init_active','reset_bank_busy','terminal_auto_answer_notice_active','terminal_script_overlay_visible','_clipboard_ui_active','_clipboard_ui_visible','_clipboard_paste_pending','terminal_menu_pending']
 for field in owners:
  m=Transaction();m.populate();m.put(field,1);before=m.snapshot();assert m.invoke()==3 and m.snapshot()==before,field
 for field in ('terminal_browser_screen_owned','terminal_editor_screen_owned'):
  m=Transaction();m.put(field,1,width=1);before=m.snapshot();assert m.invoke()==3 and m.snapshot()==before,field
 done('quiescent-frame-owner-admission',len(owners)+2)
 invalid=[('connection_state',6),('connection_state',1),('ui_flow_suppressed',2),('ui_window_rows',43),('ui_flow_region_cells',79),('ui_flow_video_base',3680),('screen_columns',40),('screen_attribute_row_bytes',132),('screen_viewport_enabled',1),('screen_cursor_wrap',1),('screen_attribute_checks',1),('erase_protection_mode',1),('text_video_segment',0xb000),('text_cga_status_port',0x3da),('csi_row_count',25),('csi_last_row',24),('erase_cell_count',2000),('screen_cursor_row',24),('screen_cursor_column',80),('screen_video_offset',2),('screen_attribute_offset',1),('terminal_parity',5),('terminal_baud_high',1),('screen_previous_row',24),('screen_previous_row',1),('screen_previous_column',1),('csi_saved_row',24)]
 for field,value in invalid:
  m=Transaction();m.put(field,value);before=m.snapshot();assert m.invoke()==3 and m.snapshot()==before,field
 m=Transaction();m.put('reset_ready',0);before=m.snapshot();assert m.invoke()==2 and m.snapshot()==before
 for kind,value in [('mode',7),('columns',40),('page',1),('height',49)]:
  m=Transaction()
  if kind=='height':m.uc.mem_write(0x484,bytes([value]))
  else:setattr(m,kind,value)
  before=m.snapshot();assert m.invoke()==3 and m.snapshot()==before,kind
 done('invalid-geometry-profile-and-connected-size-refusals',len(invalid)+5)
 m=Transaction();m.set_baseline('csi_last_row',99);before=m.snapshot();assert m.invoke()==3 and m.snapshot()==before
 m=Transaction();assert m.invoke()==0;m.put('screen_first_row',24);m.put('screen_last_row',24);before=m.snapshot();assert m.invoke()==3 and m.snapshot()==before
 done('invalid-baseline-and-unrepresentable-custom-margin-refuse-before-commit',2)
 m=Transaction();pointer=m.offset('_command_menu_script');m.uc.mem_write(m.data_base+pointer,b'Existing notice\0')
 # The near API accepts SI, so seed it exactly at the genuine entry.
 def notice(u,address,size,data):
  if address==m.symbols['terminal_connection_notice']:u.reg_write(UC_X86_REG_SI,pointer)
 hook=m.uc.hook_add(UC_HOOK_CODE,notice)
 try:m.call('terminal_connection_notice',limit=1000000)
 finally:m.uc.hook_del(hook)
 before=m.snapshot();assert m.invoke()==3 and m.snapshot()==before
 m.call('terminal_connection_notice_restore');assert m.invoke()==0
 done('notice-lease-must-be-retired-before-frame-acquisition')
 m=Transaction();assert m.invoke()==0;m.populate();before=m.snapshot();injected=[]
 def fault(u,address,size,data):
  if address==m.symbols['terminal_status_notice_refresh']:
   injected.append(True);m.put('terminal_parity',5)
 hook=m.uc.hook_add(UC_HOOK_CODE,fault)
 try:assert m.invoke()==4
 finally:m.uc.hook_del(hook)
 assert injected;m.put('terminal_parity',0);assert m.snapshot()==before
 done('late-real-renderer-refusal-rolls-back-live-defaults-and-all-screen-planes')
 m=Transaction();assert m.invoke()==0;m.populate()
 for field,value in [('screen_cursor_row',24),('screen_previous_row',24),('screen_cursor_column',7),('screen_previous_column',7),('screen_visible_column',7),('screen_video_offset',3854),('screen_attribute_offset',1927)]:m.put(field,value)
 before=m.snapshot();observed=[];start=m.symbols['status_renderer_refresh'];end=m.symbols['status_sprintf']
 def after_draw(u,address,size,data):
  # Fault the real renderer's result only after its real draw routine returns.
  # No instruction, return address or callback is replaced.
  if start<=address<end and bytes(u.mem_read(address,1))==b'\xa1':
   observed.append(m.video()!=before['video']);m.put('status_error',3)
 hook=m.uc.hook_add(UC_HOOK_CODE,after_draw)
 try:assert m.invoke()==4
 finally:m.uc.hook_del(hook)
 assert observed==[True] and m.snapshot()==before
 done('post-draw-failure-restores-scrolled-video-metadata-shadow-and-hardware-cursor')
 m=Transaction();inject(m,b'\x1b[25;1HQ\x1b[6n');queued=(m.get('uart_rx_count'),m.get('uart_rx_write'),m.get('uart_rx_read'))
 assert queued[0] and m.invoke()==0
 assert (m.get('uart_rx_count'),m.get('uart_rx_write'),m.get('uart_rx_read'))==queued
 ordinary(m,b'');m.drain();assert m.video()[3840]==ord('Q') and bytes(m.tx).endswith(b'\x1b[25;2R')
 done('queued-native-UART-input-retained-for-parser-after-commit')
 for source,digest in manifest['sources'].items():assert sha(ROOT/source)==digest,source
 result=dict(passed=True,terminal_sha256=sha(transport.BINARY),manifest_sha256=sha(transport.BINARY.parent/'manifest.json'),cases=cases,sources={f:sha(ROOT/f) for f in ('src/terminal/status_transition.c','src/terminal/status_transition.h','src/terminal/status_transition_glue.asm','src/terminal/connection_ui.asm','standalone/check_status_transition_live.py')},scope=__doc__+' Offline fixed80x25 narrow/unprotected component; actual frame/metadata/default rollback, native scroll/cursor/status and parser/CPR/RIS execute. Late fault changes a configuration input at renderer entry; no product function replaced. No key/menu binding, online resize/NAWS, larger/wide mode, actual DOS/BBS/physical or deployment acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
