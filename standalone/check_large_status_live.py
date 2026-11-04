#!/usr/bin/env python3
"""Linked full-height offline status controls, scroll/rollback and parser bounds.
Actual product code executes; BIOS/UART/DOS and renderer fault timing modeled.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--small-terminal',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 mfest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==mfest['binary_sha256'] and mfest['experimental_large_view_frames'] and mfest['experimental_program_display_owner']
 for n,h in mfest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from check_row_geometry_live import Geometry
 from program_display_model import Program
 from check_recording_rx_live import ordinary,inject
 class Status(Geometry):
  setup=Program.setup
  def seed(self):
   self.uc.mem_write(self.symbols['screen_attribute_cells'],bytes(i%251 for i in range(4096)))
   self.uc.mem_write(self.symbols['erase_attribute_values'],bytes((i+19)%251 for i in range(4096)))
   self.uc.mem_write(self.symbols['screen_line_flags'],bytes(range(128)))
   self.uc.mem_write(self.symbols['erase_shadow_cells'],b'\x55\xaa'*4096)
 def fresh(rows,profile=6):
  m=Status();m.put('csi_terminal_id',profile);m.setup(rows);m.tx.clear();return m
 def state(m,rows,hidden):
  logical=rows-(not hidden);assert m.get('ui_flow_suppressed')==hidden and m.get('csi_row_count')==logical and m.get('csi_last_row')==logical-1 and m.get('erase_cell_count')==logical*80
  assert m.value('csi_row_count')==logical and m.value('csi_last_row')==logical-1
  assert not m.get('_terminal_status_toggle_active') and not m.get('terminal_quit') and not m.get('terminal_local_control_status')
  assert bytes(m.uc.mem_read(m.symbols['erase_shadow_cells'],rows*160))==bytes(m.uc.mem_read(0xb8000,rows*160))
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,'PASS',flush=True)
 n=0
 for rows in (25,28,43,50):
  for profile in (4,6):
   for key in (0x1b1d,0x001d,0xe01d):
    m=fresh(rows,profile);m.seed();before=m.full();m.key(key);state(m,rows,1)
    assert bytes(m.uc.mem_read(0xb8000,(rows-1)*160))==before['video'][:(rows-1)*160]
    attr=m.get('ui_flow_attribute')&255;assert bytes(m.uc.mem_read(0xb8000+(rows-1)*160,160))==bytes([32,attr])*80
    assert bytes(m.uc.mem_read(0xb8000+rows*160,8000-rows*160))==before['video'][rows*160:]
    assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells']+rows*80,4096-rows*80))==before['planes']['screen_attribute_cells'][rows*80:]
    assert bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'],63000))==before['planes']['terminal_history_buffer']
    ordinary(m,b'\x1b[18t\x1b[99;80H\x1b[6n');m.drain();assert bytes(m.tx)==b'\x1b'+f'[8;{rows};80t'.encode()+b'\x1b'+f'[{rows};80R'.encode();m.tx.clear()
    ordinary(m,b'\x1bc\x1b[18t\x1b[99;80H\x1b[6n');m.drain();assert bytes(m.tx)==b'\x1b'+f'[8;{rows};80t'.encode()+b'\x1b'+f'[{rows};80R'.encode();m.tx.clear()
    m.key(0x2c00);m.key(key);state(m,rows,0)
    assert not m.get('_redisplay_active') and not m.get('_command_menu_active')
    ordinary(m,b'\x1b[18t\x1b[99;80H\x1b[6n');m.drain();assert bytes(m.tx)==b'\x1b'+f'[8;{rows-1};80t'.encode()+b'\x1b'+f'[{rows-1};80R'.encode();m.tx.clear()
    ordinary(m,b'\x1bc\x1b[18t\x1b[99;80H\x1b[6n');m.drain();assert bytes(m.tx)==b'\x1b'+f'[8;{rows-1};80t'.encode()+b'\x1b'+f'[{rows-1};80R'.encode();n+=2
 done('all-heights-profiles-normalized-keys-reference-return-RIS-defaults-CPR-and-canaries',n)
 n=0
 for rows in (25,28,43,50):
  for custom in (False,True):
   m=fresh(rows);assert m.invoke()==0;m.seed()
   for name,value in {'screen_cursor_row':rows-1,'screen_previous_row':rows-1,'csi_saved_row':rows-1,'screen_cursor_column':7,'screen_previous_column':7,'screen_visible_column':7,'screen_video_offset':(rows-1)*160+14,'screen_attribute_offset':(rows-1)*80+7}.items():m.put(name,value)
   first,last=(2,rows-3) if custom else (0,rows-1)
   if custom:
    m.put('screen_first_row',first);m.put('screen_last_row',last);m.put('csi_origin_row',1);m.put('csi_origin_bottom',rows-4)
   before=m.full();assert m.invoke()==0;state(m,rows,0);expected=bytearray(before['video'])
   expected[first*160:last*160]=before['video'][(first+1)*160:(last+1)*160];expected[last*160:(last+1)*160]=b' \x07'*80
   assert bytes(m.uc.mem_read(0xb8000,(rows-1)*160))==expected[:(rows-1)*160]
   assert m.get('screen_cursor_row')==m.get('screen_previous_row')==m.get('csi_saved_row')==rows-2
   assert m.get('screen_last_row')==(last if custom else rows-2) and m.get('csi_origin_bottom')==(rows-4 if custom else rows-2)
   flags=bytearray(before['planes']['screen_attribute_cells']);flags[first*80:last*80]=flags[(first+1)*80:(last+1)*80];flags[last*80:(last+1)*80]=bytes(80)
   assert bytes(m.uc.mem_read(m.symbols['screen_attribute_cells'],(rows-1)*80))==flags[:(rows-1)*80];n+=1
 done('native-bottom-cursor-scroll-custom-margins-and-metadata-at-every-height',n)
 n=0
 for rows in (25,28,43,50):
  for after_draw in (False,True):
   m=fresh(rows);assert m.invoke()==0;m.seed()
   for name,value in {'screen_cursor_row':rows-1,'screen_previous_row':rows-1,'screen_cursor_column':7,'screen_previous_column':7,'screen_visible_column':7,'screen_video_offset':(rows-1)*160+14,'screen_attribute_offset':(rows-1)*80+7}.items():m.put(name,value)
   before=m.full();seen=[];start=m.symbols['status_renderer_refresh'];end=m.symbols['status_sprintf']
   def fault(u,at,size,d):
    if not after_draw and at==m.symbols['terminal_status_notice_refresh']:seen.append(True);m.put('terminal_parity',5)
    if after_draw and start<=at<end and bytes(u.mem_read(at,1))==b'\xa1':seen.append(bytes(u.mem_read(0xb8000,8000))!=before['video']);m.put('status_error',3)
   hook=m.uc.hook_add(UC_HOOK_CODE,fault)
   try:assert m.invoke()==4
   finally:m.uc.hook_del(hook)
   m.put('terminal_parity',0);after=m.full()
   assert seen==[True] and after==before,(rows,after_draw,seen,[k for k in before if before[k]!=after[k]],[(k,v,after['words'][k]) for k,v in before['words'].items() if after['words'][k]!=v],[(i,x,y) for i,(x,y) in enumerate(zip(before['video'],after['video'])) if x!=y][:24],before['hardware'],after['hardware']);n+=1
 done('real-pre-render-and-post-draw-failure-restore-all-physical-rows-planes-defaults-cursor',n)
 n=0
 for rows in (25,28,43,50):
  for field,value in [('connection_state',6),('ui_window_rows',26),('ui_flow_video_base',0xffff),('screen_attribute_row_bytes',132),('terminal_screen_pause_active',1),('terminal_auto_answer_notice_active',1),('_redisplay_live_ready',1)]:
   m=fresh(rows);m.put(field,value);before=m.full();assert m.invoke()==3 and m.full()==before;n+=1
  m=fresh(rows);m.uc.mem_write(0x484,b'\x19');before=m.full();assert m.invoke()==3 and m.full()==before;n+=1
  m=fresh(rows);assert m.invoke()==0;m.put('screen_first_row',rows-1);m.put('screen_last_row',rows-1);before=m.full();assert m.invoke()==3 and m.full()==before;n+=1
 done('online-owner-invalid-BIOS-geometry-and-unrepresentable-margin-refusals',n)
 n=0
 for rows in (25,28,43,50):
  for profile in (4,6):
   m=fresh(rows,profile);inject(m,b'\x1b'+f'[{rows};1HQ'.encode()+b'\x1b[6n');queued=(m.get('uart_rx_count'),m.get('uart_rx_write'),m.get('uart_rx_read'))
   assert m.invoke()==0 and (m.get('uart_rx_count'),m.get('uart_rx_write'),m.get('uart_rx_read'))==queued
   ordinary(m,b'');m.drain();assert bytes(m.tx)==b'\x1b'+f'[{rows};2R'.encode() and bytes(m.uc.mem_read(0xb8000+(rows-1)*160,1))==b'Q';m.tx.clear()
   m.key(0x3100);assert m.get('terminal_local_control_status')==3 and not m.tx
   assert Program.far_entry(m,'terminal_auto_answer_admit_far')==1
   m.key(0x1b1d);state(m,rows,0);assert Program.far_entry(m,'terminal_auto_answer_admit_far')==0;n+=1
 done('real-UART-queue-preserved-for-new-last-row-and-hidden-modal-admission',n)
 small=None
 if a.small_terminal:
  small_path=a.small_terminal.resolve();sm=json.loads((small_path.parent/'manifest.json').read_text());assert sha(small_path)==sm['binary_sha256'] and not sm['experimental_large_view_frames'] and not sm['experimental_program_display_owner']
  for name,h in sm['sources'].items():assert sha(ROOT/name)==h,name
  transport.BINARY=small_path;transport.MAP=small_path.parent/'terminal.map'
  for rows in (28,43,50):
   m=Geometry();assert m.set_rows(rows)==0;before=m.full();assert m.invoke()==3 and m.full()==before
  small=dict(path=str(small_path.relative_to(ROOT)),sha256=sha(small_path));done('small-frame-image-refuses-coherent-larger-layouts-before-loan',3)
 for name,h in mfest['sources'].items():assert sha(ROOT/name)==h,name
 sources=['standalone/check_large_status_live.py','standalone/check_row_geometry_live.py','standalone/check_status_transition_live.py','standalone/program_display_model.py']
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),small_frame_image=small,inputs=sum(c['inputs'] for c in cases),cases=cases,sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Offline resize only; no live NAWS/BBS/SIP/physical acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
