#!/usr/bin/env python3
"""Linked Alt-T/Alt-Z serviced window, native clock, UART/parser and notice owners."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from check_call_timer_live import configure, Clock, ROOT
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();configure(a.terminal)
out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
cases=[]
def check(name,fn):fn();cases.append(dict(case=name,passed=True));print(name,'PASS',flush=True)
def ordinary(m,data):
 m.receive_irq(data)
 while m.get('uart_rx_count'):
  value=m.call('uart_receive_byte');m.call('terminal_receive_input',ax=value,limit=1000000)
def ticks(m,count):
 m.tick=(m.tick+count)%0x1800b0;m.uc.mem_write(0x46c,struct.pack('<I',m.tick))
def screen(m):return bytes(m.uc.mem_read(0xb8000,4000))
def text(m,row,left,count):return screen(m)[row*160+left*2:row*160+(left+count)*2:2]
def live_receive(m,data):
 m.call('terminal_redisplay_before');ordinary(m,data);m.call('terminal_redisplay_idle')
def opened(m,menu=False):
 if menu:m.key(0x2c00);assert m.get('_command_menu_active')
 m.key(0x1400)
 assert m.get('_terminal_elapsed_view_active')==m.get('_redisplay_active')==1
 assert not m.get('_command_menu_active') and not m.get('terminal_quit')
 assert text(m,12,27,23) in (b'ELAPSED TIME LAST CALL:',b'ELAPSED TIME THIS CALL:')
for menu in (False,True):
 for key in (ord('x'),27,0x2d00,0x4800,0x2e00,0x1400):
  def dismiss(menu=menu,key=key):
   m=Clock();ordinary(m,b'LIVE\x1b[31m COLOR\x1b[0m');before=screen(m);shape=m.shape
   opened(m,menu);assert text(m,12,51,8)==b'00:00:00'
   m.key(key)
   assert not m.get('_terminal_elapsed_view_active') and not m.get('_redisplay_active') and not m.get('terminal_quit')
   assert screen(m)==before and m.shape==shape and not m.tx and not m.get('terminal_deferred_count')
  check('one-local-dismiss-'+hex(key)+'-menu-'+str(menu),dismiss)
def received():
 m=Clock();ordinary(m,b'BEFORE');opened(m);m.now=100
 live_receive(m,b'\x1b[2;3HLIVE\x1b[6n');m.drain()
 assert text(m,12,27,23)==b'ELAPSED TIME LAST CALL:' and bytes(m.tx)==b'\x1b[2;7R'
 m.key(27);assert b'LIVE' in m.text() and m.get('screen_cursor_row')==1 and m.get('screen_cursor_column')==6
 assert not m.get('uart_rx_dropped') and not m.get('terminal_parser_active')
check('incoming-parser-CPR-updates-live-underlay-with-window-visible',received)
def rate():
 m=Clock();opened(m);reads=m.time_reads
 for _ in range(50):m.call('terminal_redisplay_idle')
 assert m.time_reads==reads
 ticks(m,18);m.now=3661;m.call('terminal_redisplay_idle')
 assert m.time_reads==reads+1 and text(m,10,30,8)==b'01:01:01'
 m.key(27)
check('idle-refresh-is-bounded-to18-BIOS-ticks',rate)
def loss():
 m=Clock();m.now=100;m.connect(b'CONNECT\r\n');opened(m);assert text(m,12,27,23)==b'ELAPSED TIME THIS CALL:'
 m.now=107;m.carrier=False;m.poll(8)
 assert m.state()==0 and m.get('_terminal_elapsed_view_active') and text(m,12,27,23)==b'ELAPSED TIME THIS CALL:'
 ticks(m,18);m.call('terminal_redisplay_idle');assert text(m,12,51,8)==b'00:00:07'
 m.key(27);assert not m.get('_terminal_elapsed_view_active') and not m.get('_redisplay_active')
 assert b'Carrier lost' in m.text()[1920:1935] and b'ELAPSED TIME' not in m.text()
 opened(m);assert text(m,12,27,23)==b'ELAPSED TIME LAST CALL:' and text(m,12,51,8)==b'00:00:07'
 m.key(27)
check('carrier-loss-freezes-timer-and-defers-notice-until-underlay-release',loss)
def defer():
 m=Clock();m.put('terminal_parser_active',1);m.key(0x1400)
 assert not m.get('_terminal_elapsed_view_active') and m.get('terminal_deferred_count')==1
 m.put('terminal_parser_active',0);m.call('terminal_poll_io');assert m.get('_terminal_elapsed_view_active') and not m.get('terminal_deferred_count')
 m.key(27)
check('partial-parser-defers-one-open-until-owner-release',defer)
def browser():
 m=Clock();m.key(ord('`'));m.key(ord('/'))
 for ch in b'Elapsed Time':m.key(ch)
 m.key(13);m.key(27);m.key(13)
 assert m.get('_terminal_elapsed_view_active') and not m.get('_command_menu_active')
 m.key(27);assert not m.get('_redisplay_active') and not m.tx
check('command-browser-search-selection-opens-same-serviced-window',browser)
for field,value in [('mode',7),('columns',40),('page',1),('height',49)]:
 def unsupported(field=field,value=value):
  m=Clock()
  if field=='height':m.uc.mem_write(0x484,bytes([value]))
  else:setattr(m,field,value)
  before=screen(m);m.key(0x1400)
  assert not m.get('_terminal_elapsed_view_active') and not m.get('_redisplay_active') and screen(m)==before and not m.tx
 check('refuse-unsupported-BIOS-'+field,unsupported)
def stopped():
 m=Clock();before=screen(m);opened(m);m.call('terminal_redisplay_stop')
 assert not m.get('_terminal_elapsed_view_active') and not m.get('_redisplay_active') and screen(m)==before
check('external-view-stop-releases-clock-window-and-underlay',stopped)
result=dict(passed=True,cases=cases,terminal_sha256=hashlib.sha256(a.terminal.read_bytes()).hexdigest(),sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),ROOT/'standalone/check_call_timer_live.py']},scope=__doc__+' Actual linked application; DOS time/date, BIOS, UART/PIC and filesystem modeled. No original pixel equivalence, actual DOS or physical/SIP acceptance.')
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS elapsed view:',len(cases),'cases')
