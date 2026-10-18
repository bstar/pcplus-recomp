#!/usr/bin/env python3
"""Linked clipboard UI/transport tests: only BIOS/video/UART boundaries modeled."""
import hashlib,json,struct
from pathlib import Path
from check_redisplay_live import Redisplay
ROOT=Path(__file__).resolve().parents[1]
class Clipboard(Redisplay):
 def open_clip(self):
  self.key(0x8300);assert self.get('_redisplay_active') and self.get('_clipboard_ui_active')
 def state(self):return bytes(self.uc.mem_read(self.symbols['_clipboard_list'],214))
 def names(self):
  s=self.state();return [s[4+i*13:17+i*13].split(b'\0')[0] for i in range(int.from_bytes(s[:2],'little'))]
 def type(self,data):
  for c in data:self.key(c)
 def add(self,name):self.key(ord('a'));self.type(name);self.key(13)
 def idle(self):self.call('terminal_redisplay_idle',limit=3000000)
 def complete(self):self.drain();self.idle();assert not self.get('_clipboard_paste_pending')
def main():
 groups=[]
 def check(name,fn):
  n=fn();groups.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 def listing():
  m=Clipboard();before=bytes(m.uc.mem_read(0xb8000,4000));m.open_clip();m.add(b'one.zip');m.add(b'two.zip');assert m.names()==[b'ONE.ZIP',b'TWO.ZIP']
  m.add(b'one.zip');assert len(m.names())==2
  m.key(ord('e'));m.type(b'\b'*7+b'lower.zip');m.key(13);assert m.names()[0]==b'lower.zip'
  m.key(0x5000);m.key(ord(' '));assert m.state()[200]==16
  m.key(ord('d'));assert m.names()==[b'lower.zip']
  m.key(27);assert not m.get('_redisplay_active') and bytes(m.uc.mem_read(0xb8000,4000))==before and not m.tx
  m.open_clip();assert m.names()==[b'lower.zip'];m.key(ord('u'));m.key(ord('n'));assert m.names()
  m.key(ord('u'));m.key(ord('y'));assert not m.names()
  return 9
 check('direct-AltEquals-add-duplicate-edit-case-tags-delete-purge-confirm-and-persistence',listing)
 def paste():
  m=Clipboard();m.open_clip();m.add(b'one.zip');m.add(b'two.zip');m.key(ord(' '));m.key(ord('r'));m.type(b'32');m.key(13)
  m.key(ord('p'));assert m.get('_clipboard_paste_pending');assert not m.tx;m.complete()
  assert bytes(m.tx)==b'ONE.ZIP TWO.ZIP \r' and len(m.names())==2
  m.tx.clear();m.key(ord('t'));m.complete();assert bytes(m.tx)==b'ONE.ZIP \r'
  m.tx.clear();m.key(ord('s'));assert len(m.names())==2;m.complete();assert bytes(m.tx)==b'ONE.ZIP\r' and m.names()==[b'TWO.ZIP']
  m.tx.clear();m.key(ord('s'));m.complete();assert bytes(m.tx)==b'TWO.ZIP\r' and not m.names()
  m.key(ord('p'));assert not m.get('_clipboard_paste_pending')
  return 5
 check('one-all-tagged-raw-separator-and-Single-deletion-after-actual-UART-writes',paste)
 def cancellation():
  for sent in (0,3,7):
   m=Clipboard();m.open_clip();m.add(b'one.zip');m.key(ord('s'))
   for _ in range(sent):m.call('terminal_poll_serial')
   assert len(m.names())==1
   # Real parser response follows the clipboard prefix; cancel preserves it.
   m.enqueue(b'REPLY');m.thre=False;m.key(27);assert not m.get('_clipboard_paste_pending') and m.names()==[b'ONE.ZIP']
   assert m.get('terminal_clipboard_remaining')==0 and m.get('terminal_tx_count')==5
   m.thre=True;m.complete();assert bytes(m.tx)==b'ONE.ZIP\r'[:sent]+b'REPLY'
  return 3
 check('cancel-unsent-owned-prefix-retains-Single-and-preserves-later-parser-response',cancellation)
 def flow():
  for hardware in (False,True):
   m=Clipboard();m.open_clip();m.add(b'one.zip');m.key(ord('s'))
   if hardware:m.put('uart_hardware_flow',1);m.cts=False
   else:m.thre=False
   for _ in range(5):m.call('terminal_poll_serial');m.idle()
   assert not m.tx and m.get('terminal_clipboard_remaining')==8 and m.names()==[b'ONE.ZIP']
   m.key(27);assert not m.get('_clipboard_paste_pending') and not m.get('terminal_tx_count') and m.names()==[b'ONE.ZIP']
  m=Clipboard();m.open_clip();m.add(b'one.zip');m.thre=False;m.enqueue(b'busy');m.key(ord('s'))
  assert not m.get('_clipboard_paste_pending') and m.names()==[b'ONE.ZIP'] and m.get('terminal_tx_count')==4
  return 3
 check('CTS-transmitter-stalls-serviced-cancel-and-busy-queue-preflight',flow)
 def interrupted():
  m=Clipboard();m.open_clip();m.add(b'one.zip');m.key(ord('s'));m.call('terminal_poll_serial')
  m.call('terminal_clipboard_abort');m.put('terminal_tx_count',0);m.put('terminal_tx_head',0);m.put('terminal_tx_tail',0);m.idle()
  assert m.names()==[b'ONE.ZIP'] and not m.get('_clipboard_paste_pending')
  m.tx.clear();m.key(ord('s'));m.complete();assert bytes(m.tx)==b'ONE.ZIP\r' and not m.names()
  m=Clipboard();m.open_clip();m.add(b'one.zip');m.key(ord('s'));m.thre=False;m.key(0x2d00)
  assert m.get('terminal_quit') and not m.get('_redisplay_active') and not m.get('_clipboard_paste_pending') and not m.get('terminal_tx_count') and m.names()==[b'ONE.ZIP']
  m=Clipboard();m.open_clip();m.add(b'one.zip');m.key(ord('s'))
  m.put('connection_enabled',1,1);m.put('connection_state',6);m.put('terminal_directory_mode',1)
  m.call('terminal_connection_cancel',limit=3000000);m.idle()
  assert m.names()==[b'ONE.ZIP'] and not m.get('_clipboard_paste_pending') and not m.get('terminal_tx_count')
  return 4
 check('connection-queue-reset-is-failure-retry-and-AltX-cancels-without-deletion',interrupted)
 def cut():
  m=Clipboard();m.uc.mem_write(0xb8000,b''.join(bytes([c,7]) for c in b' one.zip [two.arj] '+b' '*(2000-19)))
  # Ensure a full view extent regardless of the fixture text length.
  m.open_clip();m.key(ord('c'));m.key(13);assert m.names()==[b'ONE.ZIP']
  m.key(13);assert m.names()==[b'ONE.ZIP',b'TWO.ARJ'];m.key(27);m.key(27)
  m=Clipboard();m.seed(b'old.zip\r');m.open();m.key(ord('c'));assert m.get('_clipboard_ui_active')
  m.key(ord('c'));m.key(13);assert m.names()==[b'OLD.ZIP'];m.key(27);m.key(27)
  assert m.get('_redisplay_active') and not m.get('_clipboard_ui_active');m.key(27);assert not m.get('_redisplay_active')
  return 3
 check('screen-extraction-cycle-and-redisplay-submenu-nesting-preserve-underlay',cut)
 def incoming():
  m=Clipboard();m.open_clip();m.add(b'one.zip');m.key(ord('s'));m.thre=False
  m.receive(b'BACKGROUND\r\nNEXT');assert m.get('_clipboard_ui_active') and m.names()==[b'ONE.ZIP'] and not m.get('uart_rx_dropped')
  m.key(27);m.key(27);assert not m.get('_redisplay_active') and m.text(0)==b'BACKGROUND' and m.text(1)==b'NEXT'
  # Nested keyboard service during an active parser must not paint over live.
  m=Clipboard();m.open_clip();m.call('terminal_redisplay_before',limit=3000000)
  live=bytes(m.uc.mem_read(0xb8000,4000));m.key(ord('a'));m.type(b'foo.zip')
  assert bytes(m.uc.mem_read(0xb8000,4000))==live
  m.key(13);m.idle();assert m.names()==[b'FOO.ZIP']
  return 2
 check('incoming-UART-parser-continues-and-nested-keyboard-defers-paint-until-idle',incoming)
 def queue_guards():
  count=0
  for head in (0,1000,1023):
   m=Clipboard();m.put('terminal_tx_head',head);m.put('terminal_tx_tail',head)
   payload=bytes(range(196));pointer=m.stage_near(payload)
   assert m.call('_clipboard_transport',[0,pointer,196])==0
   m.enqueue(b'AFTER')
   for _ in range(100):m.call('terminal_poll_serial')
   assert m.call('_clipboard_transport',[1,0,0])==96
   assert m.call('_clipboard_transport',[2,0,0])==0
   assert m.get('terminal_tx_count')==5
   m.drain();assert bytes(m.tx)==payload[:100]+b'AFTER';count+=1
  flags=['terminal_quit','terminal_parser_active','terminal_transfer_pending','terminal_transfer_active','terminal_program_pending','terminal_program_active','terminal_macro_active','terminal_tx_count','terminal_clipboard_remaining']
  for name in flags:
   m=Clipboard();pointer=m.stage_near(b'X');m.put(name,1)
   before=(m.get('terminal_tx_head'),m.get('terminal_tx_tail'),m.get('terminal_tx_count'))
   assert m.call('_clipboard_transport',[0,pointer,1])==65535
   assert before==(m.get('terminal_tx_head'),m.get('terminal_tx_tail'),m.get('terminal_tx_count'));count+=1
  for args in ([99,0,0],[0,0,1],[0,0xfff0,32],[0,1,0],[0,1,197]):
   m=Clipboard();assert m.call('_clipboard_transport',args)==65535 and not m.get('terminal_tx_count');count+=1
  return count
 check('binary196-byte-packets-ring-wrap-cancel-prefix-and-commit-time-ownership-pointer-guards',queue_guards)
 result=dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),groups=groups,inputs=sum(g['inputs'] for g in groups),scope='Actual linked maintained UI, core, far-cdecl transport, queue and recovered UART instructions. BIOS/video/UART hardware modeled; no original binary dependency or physical/remote delivery claim.')
 (ROOT/'build/terminal/clipboard-live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Clipboard live:',result['inputs'],'inputs passed')
if __name__=='__main__':main()
