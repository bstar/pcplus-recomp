#!/usr/bin/env python3
"""Actual redisplay/far callback/file owner; only DOS/BIOS/UART are modeled."""
import hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_EFLAGS,UC_X86_REG_AX
from check_scroll import Scroll
from check_redisplay_live import Redisplay
from check_terminal_capture_live import Capture
ROOT=Path(__file__).resolve().parents[1]
class History(Capture):
 cells=Scroll.cells
 def interrupt(self,u,n,data):
  if n==0x10 and u.reg_read(UC_X86_REG_AX)>>8 in (6,7):return Scroll.interrupt(self,u,n,data)
  return super().interrupt(u,n,data)
 key=Redisplay.key
 text=Redisplay.text
 seed=Redisplay.seed
 open=Redisplay.open
 receive=Redisplay.receive
 def __init__(self,**options):
  super().__init__(**options)
  self.call('csi_clear_tabs',[1]);self.call('terminal_clear_home');assert self.call('terminal_reset_capture')==0
 def request(self,path=b'HISTORY.TXT'):
  self.key(ord('w'))
  for byte in path:self.key(byte)
  self.key(13)
 def step(self):
  self.call('terminal_redisplay_idle',limit=3000000)
  assert self.uc.reg_read(UC_X86_REG_EFLAGS)&512
 def finish(self):
  turns=0
  while self.get('_redisplay_export_pending'):
   self.step();turns+=1;assert turns<1000
  return turns
 def result(self):return bytes(self.uc.mem_read(self.symbols['_history_file_result'],96))
def main():
 cases=[]
 def check(name,fn):
  count=fn();cases.append(dict(case=name,inputs=count,passed=True));print(name,count,flush=True)
 def ordinary():
  for prefix in (b'',b'old\x1a',b'P'*70000):
   m=History();raw=b'ONE\rA\x00\x1a\x82\tB\rTAIL';m.seed(raw);m.open()
   if prefix:m.files['HISTORY.TXT']=bytearray(prefix)
   m.request();assert not m.capture_calls
   m.finish();want=prefix+raw.replace(b'\r',b'\r\n')
   assert bytes(m.files['HISTORY.TXT'])==want and not m.handles
   r=m.result();assert struct.unpack_from('<III',r,20)==(len(prefix),len(want)-len(prefix),len(want))
   assert b'History appended' in m.text(24)
   m.request();m.finish();assert bytes(m.files['HISTORY.TXT'])==want+raw.replace(b'\r',b'\r\n')
  return 3
 check('exclusive-create-or-append-preserves-prefix-NUL-SUB-CP437-tabs-and-DWORD-offsets',ordinary)
 def full():
  for raw,head in [(b'\r'*63000,1),(b'A'*62999+b'\r',62999)]:
   m=History();m.seed(raw,True,head);m.open();m.request();turns=m.finish()
   want=(raw[1:] if raw[:1]==b'\r' else raw).replace(b'\r',b'\r\n')
   assert bytes(m.files['HISTORY.TXT'])==want
   assert struct.unpack_from('<I',m.result(),24)[0]==len(want)
   writes=[x for x in m.capture_calls if x[0]==0x40]
   assert all(0<x[3]<=256 for x in writes) and turns>=494
   assert not m.handles and b'History appended' in m.text(24)
  return 2
 check('full63000-circular-snapshots-oldest-CR-skip-125998-output-and-bounded-writes',full)
 def continued():
  m=History();raw=b'OLD\r'*500;m.seed(raw);m.open();m.request();m.step()
  for i in range(5):m.step();m.receive(b'LIVE\r\n')
  m.finish();assert bytes(m.files['HISTORY.TXT'])==raw.replace(b'\r',b'\r\n')
  assert not m.get('uart_rx_dropped');m.key(27)
  assert any(b'LIVE' in m.text(i) for i in range(25)) and not m.tx
  return 1
 check('incoming-native-UART-parser-history-update-during-frozen-export',continued)
 def simultaneous_capture():
  m=History();assert m.begin()==0;raw=b'FROZEN\r'*100
  m.seed(raw);m.open();m.request();m.step();m.step()
  assert len(m.handles)==2
  m.receive(b'LIVE\r\n');assert m.call('_capture_session_flush')==0
  assert m.contents()==b'LIVE\r\n'
  m.finish();assert bytes(m.files['HISTORY.TXT'])==raw.replace(b'\r',b'\r\n')
  assert len(m.handles)==1 and m.get('terminal_sink_398a_enabled')
  assert m.call('_capture_session_shutdown')==0 and not m.handles
  return 1
 check('distinct-active-capture-and-history-handles-receive-independent-exact-bytes',simultaneous_capture)
 def cancellation():
  m=History();m.seed(b'X'*2000);m.open();m.request();m.key(27)
  assert not m.capture_calls and m.get('_redisplay_active') and not m.get('_redisplay_export_pending')
  for close_key in (27,0x2d00):
   m=History();m.seed(b'X'*2000);m.open();m.request();m.step();m.step();assert len(m.files['HISTORY.TXT'])==128
   m.key(close_key);assert not m.get('_redisplay_export_pending') and not m.handles
   assert bytes(m.files['HISTORY.TXT'])==b'X'*128
   assert len([x for x in m.capture_calls if x[0]==0x3e])==1
   if close_key==27:
    assert m.get('_redisplay_active') and b'Export canceled' in m.text(24);m.key(27)
   else:assert m.get('terminal_quit') and not m.get('_redisplay_active')
  return 3
 check('cancel-before-open-mid-append-and-AltX-preserve-accepted-prefix-close-once',cancellation)
 def failures():
  for reason in ('write','short','close'):
   m=History(fault=reason);m.seed(b'ABC\r');m.open();m.request();m.finish()
   assert b'Export failed' in m.text(24)
   assert bytes(m.files['HISTORY.TXT'])==({'write':b'','short':b'A','close':b'ABC\r\n'}[reason])
   assert len([x for x in m.capture_calls if x[0]==0x3e])==1
   before=list(m.capture_calls);m.key(27)
   if reason=='close':
    m.open();m.request();m.finish();assert m.capture_calls==before;m.key(27)
    assert m.queue(b'ECHO CHILD')==0;m.safe();assert not m.children
   assert not m.get('terminal_exit_code')
  return 3
 check('disk-error-short-write-ambiguous-close-sticky-owner-and-child-inheritance-refusal',failures)
 def paths():
  for path in (b'CON',b'..\\BAD.TXT',b'BAD*.TXT',b'LONGFILENAME.TXT'):
   m=History();m.seed(b'X');m.open();m.request(path);m.finish()
   assert not m.capture_calls and not m.files and b'Cannot open' in m.text(24)
  m=History();m.files['HISTORY.TXT']=bytearray(b'LOCKED');m.attributes['HISTORY.TXT']=1
  m.seed(b'X');m.open();m.request();m.finish();assert bytes(m.files['HISTORY.TXT'])==b'LOCKED' and not m.handles
  m=History();m.seed(b'');m.open();m.key(ord('w'));assert not m.capture_calls and b'no file was created' in m.text(24)
  m=History();m.seed(b'X');m.open();m.request(b'');assert not m.get('_redisplay_export_pending') and not m.capture_calls
  return 7
 check('device-traversal-wildcard-overlong-readonly-empty-history-and-empty-prompt',paths)
 def conflicts():
  for owner in ('capture','snapshot','monitor'):
   m=History();path=m.stage_near(b'HISTORY.TXT\0')
   if owner=='capture':assert m.begin(b'HISTORY.TXT')==0
   else:
    assert m.call('_'+owner+'_file_initialize')==0
    assert m.call('_'+owner+'_file_begin',[path,1])==0
   held=bytes(m.uc.mem_read(m.symbols['_'+owner+'_file_result'],96))
   m.seed(b'X');m.open();m.request();m.finish()
   assert bytes(m.uc.mem_read(m.symbols['_'+owner+'_file_result'],96))==held
   assert bytes(m.files['HISTORY.TXT'])==b'' and b'Cannot open' in m.text(24)
  # The history owner also excludes later capture/monitor/snapshot aliases.
  m=History();m.seed(b'X'*2000);m.open();m.request();m.step()
  for owner in ('capture','snapshot','monitor'):
   if owner!='capture':assert m.call('_'+owner+'_file_initialize')==0
   path=m.stage_near(b'C:\\HISTORY.TXT\0')
   assert m.call('_'+owner+'_file_begin',[path,2])==2
  m.key(27);return 4
 check('four-owner-canonical-exclusion-both-directions-without-resetting-other-handles',conflicts)
 def aliases():
  m=History();m.seed(b'X'*1000);m.open();m.request();m.step()
  assert m.begin(b'OTHER.LOG')==0
  held=m.result();before=list(m.capture_calls);pointer=m.offset('_history_file_result')
  assert m.call('_history_file_event',[1,pointer,1])==1
  assert m.result()==held and m.capture_calls==before
  assert m.call('_capture_file_append',[pointer,1])==1
  assert m.result()==held and m.capture_calls==before
  assert m.call('_history_file_event',[3,0,0])==1 and m.result()==held
  m.key(27);return 3
 check('protected-history-result-input-aliases-and-invalid-operation-have-no-kernel-effect',aliases)
 sources=['standalone/check_history_export_live.py','standalone/check_redisplay_live.py','standalone/check_terminal_capture_live.py','standalone/check_program_actions_live.py','src/redisplay/redisplay.c','src/capture/capture_file.c','src/capture/capture_reservation.c','src/capture/capture_reservation.h','src/capture/capture_file.h','src/terminal/config_abi.inc','src/terminal/capture.asm']
 result=dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),inputs=sum(c['inputs'] for c in cases),cases=cases,sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},scope='Actual maintained viewer, far near-cdecl file callback, fourth independent checked DOS owner, native receive/parser and PROGRAM refusal. Kernel/BIOS/UART boundaries modeled; no physical disk or full original clipboard/UI claim.')
 (ROOT/'build/terminal/history-export-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('History export:',result['inputs'],'inputs passed')
if __name__=='__main__':main()
