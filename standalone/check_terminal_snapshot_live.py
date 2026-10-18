#!/usr/bin/env python3
"""Actual linked snapshot/native-row/file/PROGRAM instructions; kernel/HW models."""
import hashlib,json,struct
from unicorn.x86_const import *
from check_terminal_capture_live import Capture
from check_meta_actions_live import ROOT,BINARY

class Snapshot(Capture):
 def __init__(self,*,fault=None,inject_rx=False):
  super().__init__(fault=fault);self.inject_rx=inject_rx;self.injected=False
  assert self.call('_snapshot_file_initialize')==0
  self.uc.mem_write(0x484,b'\x18')
 def interrupt(self,u,number,data):
  write=number==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x40
  super().interrupt(u,number,data)
  if write and self.inject_rx and not self.injected:
   self.injected=True
   # New UART bytes execute the real ISR but no foreground parser during IO.
   self.rx.extend(b'\x1b[2JNEW SCREEN')
   u.mem_write(0xb8000,b'Z\x07'*2000)
 def paint(self):
  video=bytearray(b'\0\x17'*2000)
  for row,text in [(0,b'  ONE  TWO  '),(1,b'A\0B\x82\xb3\xdb'),(2,b'X'*80),(24,b'END')]:
   for col,value in enumerate(text):video[(row*80+col)*2]=value
  self.uc.mem_write(0xb8000,bytes(video));return bytes(video)
 def save(self):
  self.call('terminal_snapshot_start',limit=3000000)
  assert self.uc.reg_read(UC_X86_REG_EFLAGS)&0x200,'Snapshot left hardware interrupts disabled'
  for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert self.uc.reg_read(reg)==value,('snapshot ABI',reg)
 def snapshot(self):return bytes(self.files.get('PCPLUS.SCR',b''))

WANT=b'  ONE  TWO\r\nA B\x82\xb3\xdb\r\n'+b'X'*80+b'\r\n'+b'\r\n'*21+b'END\r\n'
def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();groups=[]
 def check(name,fn):
  n=fn();groups.append(dict(case=name,inputs=n,passed=True));print(name,'PASS',n,flush=True)
 def bytes_and_freeze():
  for inject in (False,True):
   m=Snapshot(inject_rx=inject);before=m.paint();logical={n:m.get(n) for n in ['screen_cursor_row','screen_cursor_column','screen_video_offset','screen_attribute_offset','attributes_current']}
   m.save();assert m.snapshot()==WANT and m.get('terminal_snapshot_rows_written')==25
   assert not m.handles and not m.get('terminal_snapshot_failed')
   assert {n:m.get(n) for n in logical}==logical
   m.call('terminal_connection_notice_restore')
   if not inject:assert bytes(m.uc.mem_read(0xb8000,4000))==before
   else:
    assert m.get('uart_rx_count')==len(b'\x1b[2JNEW SCREEN')
    assert m.snapshot()==WANT and bytes(m.uc.mem_read(m.symbols['terminal_snapshot_image'],80)).startswith(b'  ONE  TWO')
  return 2
 check('real3446-64b8-NUL-CP437-trim80-and-frozen-view-under-later-UART-and-video-change',bytes_and_freeze)
 def append_shadow():
  m=Snapshot();m.paint();m.files['PCPLUS.SCR']=bytearray(b'OLD\x1a');m.save();m.save();assert m.snapshot()==b'OLD\x1a'+WANT*2
  m=Snapshot();cells=m.paint();m.uc.mem_write(m.symbols['erase_shadow_cells'],cells)
  m.uc.mem_write(0xb8000,b'V\x01'*2000);m.put('screen_viewport_enabled',1);m.save();assert m.snapshot()==WANT
  return 2
 check('repeat-append-preserves-prefix-and-native-shadow-route-uses-far-metadata',append_shadow)
 def status_sub():
  for suppressed in (0,1):
   m=Snapshot();m.uc.mem_write(0xb8000,b' \x07'*2000)
   m.uc.mem_write(0xb8000,b'\x1a\x07');m.uc.mem_write(0xb8000+24*160,b'\x1a\x07')
   m.put('ui_flow_suppressed',suppressed);m.save()
   assert m.snapshot()==b'\x1a\r\n'+b'\r\n'*23+(b' \r\n' if not suppressed else b'\x1a\r\n')
  m=Snapshot();m.uc.mem_write(0xb8000,b'\0\x07'*2000);m.save();assert m.snapshot()==b'\r\n'*25
  return 3
 check('native-status-row-SUB-repair-visibility-and-empty-row-bounds',status_sub)
 def concurrent():
  for held in (0,1):
   m=Snapshot();assert m.begin()==0;m.log(b'BEFORE')
   if held:m.call('_capture_session_pause')
   m.paint();m.save();assert m.snapshot()==WANT
   assert m.get('terminal_sink_398a_enabled')==1 and m.get('terminal_sink_398c_disabled')==held
   m.log(b'AFTER');assert m.call('_capture_session_shutdown')==0
   assert m.contents()==(b'BEFORE' if held else b'BEFOREAFTER') and not m.handles
  for path in (b'PCPLUS.SCR',b'C:\\PCPLUS.SCR'):
   m=Snapshot();assert m.begin(path)==0;m.log(b'KEEP');m.call('_capture_session_flush')
   prior=bytes(m.uc.mem_read(m.symbols['_capture_file_result'],96));m.paint();m.save()
   assert m.snapshot()==b'KEEP' and bytes(m.uc.mem_read(m.symbols['_capture_file_result'],96))==prior
   assert m.get('terminal_sink_398a_enabled')==1 and not m.get('terminal_snapshot_failed')
   assert m.get('terminal_snapshot_rows_written')==0
  return 4
 check('separate-open-held-capture-owner-and-canonical-same-file-denial',concurrent)
 def errors():
  for reason in ('write','short','close'):
   m=Snapshot(fault=reason);m.paint();m.save()
   expected=9 if reason=='close' else 8
   assert m.get('terminal_snapshot_failed')==expected
   assert m.snapshot()==(WANT if reason=='close' else b' ' if reason=='short' else b'')
   assert len([c for c in m.capture_calls if c[0]==0x3e])==1
   assert m.call('terminal_snapshot_shutdown')==expected
   assert len([c for c in m.capture_calls if c[0]==0x3e])==1
   if reason=='close':
    prior=list(m.capture_calls);m.save();assert m.capture_calls==prior
    assert m.queue(b'ECHO CHILD')==0;m.safe();assert not m.children
   assert not m.get('terminal_quit') and not m.get('terminal_exit_code')
  m=Snapshot();m.paint();m.files['PCPLUS.SCR']=bytearray(b'LOCKED');m.attributes['PCPLUS.SCR']=1;m.save()
  assert m.snapshot()==b'LOCKED' and not m.get('terminal_snapshot_failed') and m.call('terminal_snapshot_shutdown')==0
  return 4
 check('short-write-close-once-uncertain-repeated-hotkey-PROGRAM-block-readonly-nonfatal',errors)
 def rejects():
  n=0
  for name,value in [('terminal_macro_active',1),('terminal_program_pending',1),('terminal_ansi_wait_active',1),('terminal_transfer_pending',1),('terminal_transfer_active',1),('connection_state',3),('screen_attribute_row_bytes',132),('screen_video_row_bytes',264),('ui_flow_region_cells',132),('text_video_segment',0xb000),('text_cga_status_port',0x3da)]:
   m=Snapshot();m.put(name,value);m.save();assert not m.capture_calls and 'PCPLUS.SCR' not in m.files;n+=1
  for kind in ('mode','page','height','shadowoffset','shadowsegment'):
   m=Snapshot()
   if kind=='mode':m.mode=0x13
   elif kind=='page':m.page=1
   elif kind=='height':m.uc.mem_write(0x484,b'\x31')
   else:
    m.put('screen_viewport_enabled',1);m.put('erase_shadow_offset' if kind=='shadowoffset' else 'erase_shadow_segment',0x7777)
   m.save();assert not m.capture_calls;n+=1
  return n
 check('other-owner-geometry-CGA-retrace-and-invalid-far-source-reject-before-fileIO',rejects)
 report=dict(passed=True,binary_sha256=digest,cases=groups,scope='Actual linked native3446/64b8 and CGA-disabled brackets, maintained frozen-view writer, both checked DOS owners and PROGRAM guard. Only DOSkernel/BIOS/UART boundaries modeled. No physical DMA atomicity, physicaldisk or full viewport/UI claim.')
 (ROOT/'build/terminal/terminal-snapshot-live-checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Linked snapshot:',len(groups),'groups',sum(r['inputs'] for r in groups),'inputs PASS')
if __name__=='__main__':main()
