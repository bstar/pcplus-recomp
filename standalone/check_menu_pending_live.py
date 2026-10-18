#!/usr/bin/env python3
"""Linked parser-safe menu entry, shared typeahead, cancellation and revalidation."""
import hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_SS,UC_X86_REG_SP
from check_command_menu_live import Menu
ROOT=Path(__file__).resolve().parents[1]

def main():
 cases=[]
 def check(name,fn):
  count=fn();cases.append(dict(case=name,inputs=count,passed=True));print(name,count,flush=True)
 def pending():
  m=Menu();m.put('terminal_parser_active',1);m.key(0x2c00)
  assert m.get('terminal_menu_pending') and not m.get('_redisplay_active') and not m.tx
  m.key(0x4d00);m.key(0x4de0);m.key(0x3b00)
  assert m.get('terminal_deferred_count')==3 and not m.get('_command_menu_active') and not m.tx
  m.put('terminal_parser_active',0)
  for _ in range(3):m.call('terminal_poll_io',limit=3000000)
  assert not m.get('terminal_menu_pending') and not m.get('terminal_deferred_count')
  assert m.get('_command_menu_active') and b'Browse a frozen' in m.text(7)
  m.key(27);m.key(27);assert not m.get('_redisplay_active') and not m.tx
  m=Menu();m.put('terminal_parser_active',1);m.key(0x2c00);m.put('terminal_parser_active',0)
  m.call('terminal_poll_io',limit=3000000)
  assert m.get('_command_menu_active') and not m.get('terminal_menu_pending') and not m.tx
  return 2
 check('single-request-opens-after-parser-with-or-without-FIFO-navigation-and-help',pending)
 def older_keys():
  m=Menu();m.put('terminal_parser_active',1)
  for key in (0x2c00,0x4d00):m.call('terminal_defer_key',ax=key)
  m.call('terminal_poll_io');assert m.get('terminal_menu_pending') and m.get('terminal_deferred_count')==1
  m.key(0x4de0);assert m.get('terminal_deferred_count')==2
  m.put('terminal_parser_active',0)
  m.call('terminal_poll_io',limit=3000000);assert b'Dial selected' in m.text(5)
  m.call('terminal_poll_io',limit=3000000);assert b'Redisplay history' in m.text(5)
  assert not m.tx and not m.get('terminal_deferred_count')
  return 1
 check('existing-macro-typeahead-prefix-precedes-new-BIOS-keys-without-reordering',older_keys)
 def cancel():
  for key in (27,0x2d00,0x2300):
   m=Menu();m.put('terminal_parser_active',1);m.key(0x2c00);m.key(0x4d00)
   m.key(key)
   assert not m.get('terminal_menu_pending') and not m.get('terminal_deferred_count')
   assert not m.get('_redisplay_active') and not m.get('_command_menu_active')
   assert bool(m.get('terminal_quit'))==(key==0x2d00) and not m.tx
   if key==27:
    m.put('terminal_parser_active',0);m.call('terminal_poll_io');assert not m.get('_command_menu_active')
  m=Menu();m.put('terminal_parser_active',1);m.key(0x2c00);m.key(ord('x'))
  m.call('terminal_redisplay_stop');assert not m.get('terminal_menu_pending') and not m.get('terminal_deferred_count')
  m.put('terminal_parser_active',0);m.call('terminal_poll_io');assert not m.get('terminal_quit') and not m.tx
  return 4
 check('Escape-local-cancel-AltX-exit-AltH-hangup-and-foreground-stop-drop-owned-typeahead',cancel)
 def invalidated():
  flags=['terminal_transfer_pending','terminal_transfer_active','terminal_program_pending','terminal_program_active',
   'terminal_macro_active','terminal_monitor_active','terminal_controller_active','terminal_ansi_wait_active',
   'terminal_snapshot_active','uart_break_hold','screen_viewport_enabled','text_cga_status_port']
  values=[(n,1) for n in flags]+[('text_video_segment',0xb000),('screen_attribute_row_bytes',132),
   ('screen_video_row_bytes',264),('connection_state',2)]
  for name,value in values:
   m=Menu();m.put('terminal_parser_active',1);m.key(0x2c00);m.key(0x4d00)
   m.put('terminal_parser_active',0);m.put(name,value);m.call('terminal_menu_pending_poll',limit=3000000)
   assert not m.get('terminal_menu_pending') and not m.get('terminal_deferred_count'),name
   assert not m.get('_command_menu_active') and not m.get('_redisplay_active') and not m.tx,name
  for kind in ('height','history'):
   m=Menu();m.put('terminal_parser_active',1);m.key(0x2c00);m.key(0x4d00);m.put('terminal_parser_active',0)
   if kind=='height':m.uc.mem_write(0x484,b'\x31')
   else:m.put('terminal_history_pointer',m.get('terminal_history_end'))
   m.call('terminal_menu_pending_poll',limit=3000000)
   assert not m.get('terminal_menu_pending') and not m.get('terminal_deferred_count')
   assert not m.get('_redisplay_active') and not m.tx
  m=Menu();m.put('terminal_parser_active',1);m.key(0x2c00);m.key(0x4d00)
  m.put('terminal_parser_active',0);m.put('_redisplay_active',1)
  m.call('terminal_menu_pending_poll')
  assert m.get('_redisplay_active')==1 and not m.get('_command_menu_active')
  assert not m.get('terminal_menu_pending') and not m.get('terminal_deferred_count') and not m.tx
  return len(values)+3
 check('all-owners-modem-and-geometry-rechecked-including-C-rejection-without-key-leak',invalidated)
 def capacity():
  m=Menu();m.put('terminal_parser_active',1);m.key(0x2c00)
  for _ in range(32):m.key(ord('a'))
  assert m.get('terminal_deferred_count')==32 and not m.get('terminal_quit') and not m.tx
  m.key(ord('a'));assert m.get('terminal_quit') and m.get('terminal_exit_code')==3
  assert not m.get('terminal_menu_pending') and not m.get('terminal_deferred_count') and not m.tx
  return 2
 check('full32-key-queue-retained-and-33rd-key-stops-explicitly-with-existing-overflow-policy',capacity)
 def repeats():
  m=Menu();m.put('terminal_parser_active',1);m.key(0x2c00)
  for _ in range(64):m.key(0x2c00)
  assert m.get('terminal_menu_pending') and not m.get('terminal_deferred_count') and not m.get('terminal_quit')
  m.put('terminal_parser_active',0);m.call('terminal_poll_io',limit=3000000)
  assert m.get('_command_menu_active') and not m.tx
  return 1
 check('repeated-AltZ-coalesces-without-exhausting-typeahead',repeats)
 def unchanged():
  for key in (0x8300,0x8400,0x84e0):
   m=Menu();m.put('terminal_parser_active',1);m.key(key)
   assert not m.get('terminal_menu_pending') and not m.get('terminal_deferred_count') and not m.get('_redisplay_active')
  m=Menu();m.open_menu();before=bytes(m.uc.mem_read(0xb8000,4000))
  for _ in range(10):m.call('terminal_poll_io')
  assert bytes(m.uc.mem_read(0xb8000,4000))==before and m.get('_command_menu_active') and not m.tx
  for value in (0,1,0xffff,0x2c00):assert m.call('terminal_menu_pending_poll',ax=value)==value
  def zero_key(view):
   seen=[]
   def entry(u,address,size,data):
    if address==view.symbols['_redisplay_event_impl']:
     at=(u.reg_read(UC_X86_REG_SS)<<4)+u.reg_read(UC_X86_REG_SP)+2
     seen.append(struct.unpack('<2H',u.mem_read(at,4)))
   hook=view.uc.hook_add(UC_HOOK_CODE,entry)
   view.key(0);view.uc.hook_del(hook)
   assert seen==[(1,0)],seen
   assert view.get('_redisplay_active') and not view.tx and not view.get('terminal_quit')
  zero_key(m);assert m.get('_command_menu_active')
  for key in (0x8300,0x8400):
   m=Menu();m.key(key);assert m.get('_redisplay_active');zero_key(m)
  return 7
 check('other-viewer-policy-unchanged-and-real-zero-keys-stay-owned-with-distinct-request-service',unchanged)
 result=dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),
  cases=cases,inputs=sum(c['inputs'] for c in cases),sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
   ['standalone/check_menu_pending_live.py','standalone/check_command_menu_live.py','standalone/check_redisplay_live.py','src/terminal/redisplay.asm','src/terminal/transport.asm','src/terminal/meta_actions.asm']},
  scope='Actual linked menu request/transport/typeahead and C frame owner. Hardware/BIOS modeled; no product function replaced. Parser-only Alt-Z deferral, FIFO/cancel/revalidation/overflow and unchanged non-menu policy; real split-CSI DOS evidence is separate.')
 (ROOT/'build/terminal/menu-pending-checks.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
