#!/usr/bin/env python3
"""Live native history + serviced redisplay; only BIOS/UART are modeled."""
import hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE
from check_terminal_reset_live import Live
from check_line_edit_live import Live as NativeLive
ROOT=Path(__file__).resolve().parents[1]
class Redisplay(Live):
 def __init__(self):
  super().__init__();self.bios_position=0;self.cursor_shape=0x0607
  self.call('csi_clear_tabs',[1]);self.call('terminal_clear_home');assert self.call('terminal_reset_capture')==0
 def interrupt(self,u,n,d):
  ax=u.reg_read(UC_X86_REG_AX)
  if n==0x10:
   if ax>>8==0x0f:u.reg_write(UC_X86_REG_AX,0x5003);u.reg_write(UC_X86_REG_BX,0);return
   if ax>>8==3:u.reg_write(UC_X86_REG_DX,self.bios_position);u.reg_write(UC_X86_REG_CX,self.cursor_shape);return
   if ax>>8==2:self.bios_position=u.reg_read(UC_X86_REG_DX);return
  return super().interrupt(u,n,d)
 def key(self,key):
  self.keys.append(key);self.call('terminal_poll_io',limit=30000000)
  for _ in range(1000):
   if not self.get('_redisplay_search_pending'):break
   self.call('terminal_redisplay_idle',limit=1000000)
  else:raise AssertionError('Search did not finish within1000 bounded turns')
 def text(self,row):return bytes(self.uc.mem_read(0xb8000+row*160,160))[::2].rstrip()
 def seed(self,data,wrapped=False,head=0):
  assert len(data)<=63000
  start=self.get('terminal_history_start')
  if wrapped:
   assert len(data)==63000
   raw=data[-head:]+data[:-head] if head else data
  else:raw=data
  self.uc.mem_write(self.symbols['terminal_history_buffer'],raw)
  self.put('terminal_history_pointer',start+(head if wrapped else len(data)))
  self.put('terminal_history_wrapped',int(wrapped))
 def open(self):self.key(0x8400);assert self.get('_redisplay_active')==1
 def receive(self,data):
  self.call('terminal_redisplay_before',limit=1000000)
  NativeLive.feed(self,data)
  self.call('terminal_redisplay_idle',limit=1000000)

def main():
 cases=[]
 def check(name,fn):
  count=fn();cases.append(dict(case=name,inputs=count,passed=True));print(name,count,flush=True)
 def navigation():
  m=Redisplay();m.seed(b''.join(f'Line {i:03d}\r'.encode() for i in range(100)))
  old=bytes(m.uc.mem_read(0xb8000,4000));m.bios_position=0x0405;m.open()
  assert m.text(1)==b'Line 077',m.text(1)
  for key,want in [(0x4700,b'Line 000'),(0x5000,b'Line 001'),(0x5100,b'Line 024'),(0x4900,b'Line 001'),(0x4800,b'Line 000'),(0x4f00,b'Line 077')]:
   m.key(key);assert m.text(1)==want,(key,m.text(1),want)
  m.key(27);assert not m.get('_redisplay_active') and bytes(m.uc.mem_read(0xb8000,4000))==old
  assert m.bios_position==0x0405 and m.cursor_shape==0x0607 and not m.tx
  return 8
 check('actual-transport-key-entry-line-page-home-end-cursor-full-screen-return',navigation)
 def search():
  m=Redisplay();m.seed(b'First MATCH\rsecond match\rthird\r');m.open();m.key(ord('/'))
  for c in b'mAtCh':m.key(c)
  m.key(13);assert m.text(1)==b'First MATCH'
  m.key(0x3d00);assert m.text(1)==b'second match',m.text(1)
  m.key(0x3d00);assert m.text(1)==b'First MATCH'
  m.key(ord('/'));m.key(ord('z'));m.key(13);assert b'No match' in m.text(24)
  m.key(ord('/'));m.key(27);assert m.get('_redisplay_active')
  m.key(27);assert not m.get('_redisplay_active')
  m=Redisplay();m.seed(b'');m.open();m.key(ord('/'));m.key(ord('z'));m.key(13);m.key(27)
  assert not m.get('terminal_quit') and not m.tx
  return 7
 check('ASCII-case-insensitive-search-F3-wrap-no-match-search-escape-empty-input',search)
 def ring():
  for head in [0,1,31499,62999]:
   m=Redisplay();raw=(b'BEGIN\r'+b'A'*62988+b'\rEND!!')
   assert len(raw)==63000
   m.seed(raw,True,head);m.open();m.key(0x4700);assert m.text(1)==b'BEGIN',m.text(1)
   snapshot=bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'],63000));assert snapshot==raw
   m.key(0x4f00);assert any(b'END!!' in m.text(i) for i in range(1,24))
   m.key(27)
  return 4
 check('all63000-snapshot-bytes-independent-of-four-physical-ring-origins',ring)
 def continued():
  m=Redisplay();m.seed(b'OLD\r');m.open();view=bytes(m.uc.mem_read(0xb8000,4000))
  m.receive(b'NEW\x1b[31m RED\x1b[0m\r\nNEXT')
  assert bytes(m.uc.mem_read(0xb8000,4000))==view
  assert bytes(m.uc.mem_read(m.symbols['redisplay_snapshot'],4))==b'OLD\r'
  m.key(27)
  assert m.text(0)==b'NEW RED' and m.text(1)==b'NEXT',(m.text(0),m.text(1))
  assert not m.get('uart_rx_dropped') and not m.get('terminal_quit')
  assert m.get('screen_cursor_row')==1 and m.get('screen_cursor_column')==4
  m.open();m.key(0x4700);assert m.text(1).startswith(b'OLD'),m.text(1);m.key(27)
  return 2
 check('incoming-real-UART-parser-SGR-CRLF-live-view-history-and-cursor-continue',continued)
 def unsafe():
  flags=['terminal_parser_active','terminal_transfer_pending','terminal_transfer_active','terminal_program_pending','terminal_program_active','terminal_macro_active','terminal_monitor_active','terminal_controller_active','terminal_ansi_wait_active','terminal_snapshot_active','uart_break_hold','screen_viewport_enabled','text_cga_status_port']
  for name in flags:
   m=Redisplay();m.put(name,1);m.call('terminal_redisplay_key',ax=0x8400)
   assert not m.get('_redisplay_active') and not m.get('terminal_quit'),name
  m=Redisplay();m.seed(b'one\r');m.open();m.key(0x7100);assert m.get('_redisplay_active') and not m.get('terminal_program_pending')
  m.key(0x2d00);assert not m.get('_redisplay_active') and m.get('terminal_quit')
  return len(flags)+2
 check('ownership-refusal-does-not-exit-intercepted-settings-and-AltX-clean-return',unsafe)
 def incremental():
  m=Redisplay();m.seed(b'A'*63000,True,17);m.open()
  m.key(ord('/'))
  for c in b'A'*38+b'Z':m.key(c)
  m.keys.append(13);m.call('terminal_poll_io',limit=1000000)
  assert m.get('_redisplay_search_pending')
  for _ in range(10):
   m.receive(b'LIVE')
   assert m.get('_redisplay_search_pending') and not m.get('uart_rx_dropped')
  m.key(27);assert not m.get('_redisplay_active') and not m.get('_redisplay_search_pending')
  assert b'LIVE' in m.text(0) and not m.get('terminal_quit')
  m=Redisplay();m.uc.mem_write(0x484,b'\x31');m.key(0x8400)
  assert not m.get('_redisplay_active') and not m.get('terminal_quit')
  return 2
 check('worst-repeated-prefix-search-yields-to-UART-cancels-and-refuses50-row-video',incremental)
 def notice():
  m=Redisplay();m.seed(b'OLD\r');live=bytes(m.uc.mem_read(0xb8000,4000));m.open()
  pointer=m.stage_near(b'Line idle\0')
  # Marshal the resident register-ABI SI input at entry. Every product
  # instruction still runs; this is caller argument setup, not a fake service.
  def argument(u,address,size,data):
   if address==m.symbols['terminal_connection_notice']:u.reg_write(UC_X86_REG_SI,pointer)
  hook=m.uc.hook_add(UC_HOOK_CODE,argument)
  m.call('terminal_connection_notice',limit=1000000);m.uc.hook_del(hook)
  assert not m.get('_redisplay_active')
  assert bytes(m.uc.mem_read(0xb8000,3840))==live[:3840]
  assert b'Line idle' in m.text(24)
  m.call('terminal_connection_notice_restore')
  assert bytes(m.uc.mem_read(0xb8000,4000))==live
  return 1
 check('foreground-notice-closes-history-and-restores-live-underlay',notice)
 result=dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),cases=cases,
  inputs=sum(c['inputs'] for c in cases),sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['src/redisplay/redisplay.c','src/terminal/redisplay.asm','standalone/check_redisplay_live.py']},scope='Actual transport-key dispatch, far C viewer, native history and UART/parser. BIOS/video and UART hardware modeled; no product function skipped. Actual DOS workflow separate.')
 (ROOT/'build/terminal/redisplay-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
