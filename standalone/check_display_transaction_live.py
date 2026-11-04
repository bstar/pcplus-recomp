#!/usr/bin/env python3
"""Execute composed offline selector/BIOS/canonical/RIS transaction.
BIOS, DOS allocation and mouse driver boundaries modeled; no normal UI/online claim.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
import check_transport as transport
from check_display_select_live import Selection
from check_recording_rx_live import ordinary
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Transaction(Selection):
 def invoke(self,selector=1,rows=43,mode=0,entry='_terminal_display_select'):
  arguments=[selector,rows,mode] if entry=='_terminal_display_select' else []
  u=self.uc;seg,_=self.entries[entry];sp=self.offset('terminal_stack_top')-4-2*len(arguments)
  u.mem_write(self.data_base+sp,struct.pack('<'+'H'*(2+len(arguments)),self.return_offset,self.code_segment,*arguments))
  u.mem_write(self.data_base+sp-3000,b'GUARD!')
  for reg,value in ((UC_X86_REG_CS,self.base_segment+seg),(UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_SP,sp),
   (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x5678),(UC_X86_REG_DI,0x6789),(UC_X86_REG_EFLAGS,0x202)):u.reg_write(reg,value)
  self.returned=False;u.emu_start(self.symbols[entry],0,count=5000000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
  for reg,value in ((UC_X86_REG_DS,self.ds),(UC_X86_REG_SS,self.ds),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x5678),(UC_X86_REG_DI,0x6789)):assert u.reg_read(reg)==value
  assert bytes(u.mem_read(self.data_base+sp-3000,6))==b'GUARD!'
  assert self.get('_terminal_row_geometry_active')==0
  return u.reg_read(UC_X86_REG_AX)
 def meta(self):return tuple(self.get('_terminal_display_'+s) for s in ('selector','selector_ready','fallback','physical_result'))
 def saved(self,hidden=0,selector=1,rows=43,mode=0):
  self.uc.mem_write(self.symbols['_terminal_display_preferences'],struct.pack('<4H',hidden,selector,rows,mode));self.put('_terminal_display_preferences_ready',1)
 def all(self):return self.full(),self.meta()
 def verify(self,physical,hidden=0):
  effective=physical if hidden else physical-1
  assert self.vrows==self.get('ui_window_rows')==physical
  assert self.get('csi_row_count')==self.value('csi_row_count')==effective
  assert self.get('csi_last_row')==self.get('screen_last_row')==effective-1
  assert self.get('ui_flow_suppressed')==hidden
  assert self.get('ui_flow_video_base')==(physical-1)*160
  video=bytes(self.uc.mem_read(0xb8000,physical*160));shadow=bytes(self.uc.mem_read(self.symbols['erase_shadow_cells'],8192))
  assert video[:effective*160]==b' \x07'*(effective*80)
  if not hidden:assert b'Alt-Z FOR HELP' in video[effective*160::2]
  assert shadow[:len(video)]==video and shadow[len(video):]==bytes(8192-len(video))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();mfest=json.loads((binary.parent/'manifest.json').read_text());assert mfest['experimental_display_preferences'] and sha(binary)==mfest['binary_sha256']
 for n,h in mfest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map';out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[]
 def done(name,n=1):cases.append(dict(case=name,inputs=n,passed=True));print('PASS',name,n,flush=True)
 count=0
 for hidden in (0,1):
  m=Transaction();m.saved(hidden=0xffff if hidden else 0);saved=bytes(m.uc.mem_read(m.symbols['_terminal_display_preferences'],8))
  assert m.invoke(entry='_terminal_display_apply_saved')==0
  for selector,rows,mode,physical,accepted,fallback,result in [(1,50,0,25,1,0,0),(2,43,0,43,2,0,0),(0,50,3,43,0,0,0),(3,50,3,25,3,0,0),(4,50,3,50,4,0,0),(3,50,0,25,1,1,0),(4,50,0,25,1,1,0),(3,50,0x12,25,1,1,3)]:
   assert m.invoke(selector,rows,mode)==0;m.verify(physical,hidden);assert m.meta()==(accepted,1,fallback,result)
   assert bytes(m.uc.mem_read(m.symbols['_terminal_display_preferences'],8))==saved
   ordinary(m,b'\x1b[999;1HT\x1b[6n');m.drain();effective=physical if hidden else physical-1
   assert bytes(m.tx).endswith(('\x1b[%d;2R'%effective).encode());count+=1
 done('visible-hidden-selector-commit-accepted-fallback-RIS-status-shadow-and-parser-CPR',count)
 count=0
 for mode,wanted in [(0,[2,1,2,1]),(3,[2,3,4,1]),(0xffff,[2,1,2,1])]:
  m=Transaction();m.saved(mode=mode);assert m.invoke(entry='_terminal_display_apply_saved')==0
  for selector in wanted:
   assert m.invoke(entry='_terminal_display_cycle')==0 and m.meta()[0]==selector;count+=1
 done('saved-zero-nonzero-cycle-policy-uses-accepted-selector',count)
 m=Transaction();before=m.all();assert m.invoke(entry='_terminal_display_apply_saved')==7 and m.all()==before
 assert m.invoke(entry='_terminal_display_cycle')==7 and m.all()==before
 m.saved();assert m.invoke(entry='_terminal_display_cycle')==7 and m.meta()[1]==0
 m.saved(selector=0xffff);before=m.all();assert m.invoke(entry='_terminal_display_apply_saved')==1 and m.all()==before
 done('missing-preferences-live-selector-and-invalid-saved-selection-refuse',4)
 for invalid in (5,0x8000,0xffff):
  m=Transaction();before=m.all();assert m.invoke(invalid)==1 and m.all()==before
 done('public-selector-cannot-enter-internal-raw-row-sentinel-path',3)
 count=0
 for field,value in [('connection_state',1),('connection_state',6),('terminal_transfer_active',1),('terminal_program_active',1),('_command_menu_active',1),('reset_bank_busy',1)]:
  m=Transaction();m.put(field,value);before=m.all();assert m.invoke(2)==3 and m.all()==before;count+=1
 done('online-and-foreground-owner-refusals-preserve-selector-and-complete-owned-state',count)
 for mode in (2,7):
  m=Transaction();assert m.invoke(2)==0;before=m.all()
  assert m.invoke(3,43,mode)==4 and m.all()==before,(mode,m.meta())
 done('alternate-text-mode-restores-admitted-mode3-and-all-owned-planes',2)
 m=Transaction();assert m.invoke(2)==0;before=m.all();fault=[]
 def renderer(u,address,size,data):
  if address==m.symbols['terminal_status_notice_refresh']:fault.append(True);m.put('terminal_parity',5)
 hook=m.uc.hook_add(UC_HOOK_CODE,renderer)
 try:assert m.invoke(4,50,3)==4
 finally:m.uc.hook_del(hook)
 assert fault and m.all()==before
 done('late-real-renderer-refusal-restores-BIOS-defaults-planes-and-live-selector')
 m=Transaction();assert m.invoke(2)==0;fault=[]
 def unrecoverable(u,address,size,data):
  if address==m.symbols['terminal_status_notice_refresh']:fault.append(True);m.put('terminal_parity',5);m.font_refusals=1
 hook=m.uc.hook_add(UC_HOOK_CODE,unrecoverable)
 try:assert m.invoke(4,50,3)==5
 finally:m.uc.hook_del(hook)
 assert fault and m.get('terminal_quit')==1 and m.get('terminal_exit_code')==2
 done('unverified-old-geometry-requests-existing-fatal-shutdown')
 m=Transaction();m.font_refusals=1;assert m.invoke(2,50)==0;m.verify(25);assert m.meta()==(1,1,1,3)
 done('BIOS-font-failure-commits-verified-fallback-and-metadata-together')
 m=Transaction();payload=b'\x1b[49;1HQ\x1b[6n';arrived=[]
 def rx(u,address,size,data):
  if address==m.symbols['_native_display_select'] and not arrived:arrived.append(True);m.rx.extend(payload)
 hook=m.uc.hook_add(UC_HOOK_CODE,rx)
 try:assert m.invoke(4,50,3)==0
 finally:m.uc.hook_del(hook)
 assert arrived and not m.rx and m.get('uart_rx_count')==len(payload) and not m.get('uart_rx_dropped')
 ordinary(m,b'');m.drain();assert bytes(m.tx).endswith(b'\x1b[49;2R') and m.meta()==(4,1,0,0)
 done('actual-UART-ISR-arrival-waits-for-complete-new-canonical-geometry')
 m=Transaction();m.start_mouse();allocations=dict(m.mouse_boundary.allocations)
 assert m.invoke(4,50,3)==0 and m.mouse_boundary.allocations==allocations and m.meta()==(4,1,0,0)
 done('real-mouse-owner-suspended-across-configured-mode-and-font-changes')
 m=Transaction();m.start_mouse();injected=[]
 def mouse_failure(u,address,size,data):
  if address==m.symbols['terminal_status_notice_refresh']:injected.append(True);m.mouse_boundary.present=False
 hook=m.uc.hook_add(UC_HOOK_CODE,mouse_failure)
 try:assert m.invoke(4,50,3)==6
 finally:m.uc.hook_del(hook)
 assert injected and m.get('terminal_quit')==1 and m.get('terminal_exit_code')==14
 assert m.vrows==50 and m.get('csi_row_count')==49 and m.meta()==(4,1,0,0) and m.mouse_boundary.allocations
 done('post-commit-mouse-failure-keeps-coherent-selector-and-quarantined-shutdown')
 m=Transaction();assert m.invoke(2)==0;assert m.set_rows(25)==0 and m.meta()[1]==0
 assert m.invoke(entry='_terminal_display_cycle')==7
 done('direct-physical-row-request-invalidates-derived-live-selector')
 m=Transaction();m.put('_terminal_display_selector_ready',0x5aa5);stopped=[]
 ip,cs=struct.unpack_from('<HH',binary.read_bytes(),0x14);u=m.uc
 def stop(u,address,size,data):
  if address==m.symbols['_terminal_mouse_bootstrap']:stopped.append(True);u.emu_stop()
 hook=u.hook_add(UC_HOOK_CODE,stop)
 for reg,value in ((UC_X86_REG_CS,m.base_segment+cs),(UC_X86_REG_DS,0x2000),(UC_X86_REG_SS,0x2000),(UC_X86_REG_ES,0x2000)):u.reg_write(reg,value)
 try:u.emu_start((m.base_segment+cs)*16+ip,0,count=100)
 finally:u.hook_del(hook)
 assert stopped and m.get('_terminal_display_selector_ready')==0
 done('actual-MZ-entry-clears-live-selector-readiness')
 for n,h in mfest['sources'].items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),cases=cases,checker_sha256=sha(Path(__file__)),scope=__doc__+' Actual selector and canonical owner, RIS/parser/status/shadow/rollback, UART ISR and mouse owner execute. BIOS/DOS/INT33 effects modeled; faults change real-boundary inputs. No instruction/function replacement, normal command, online/BBS/physical or deployment acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
