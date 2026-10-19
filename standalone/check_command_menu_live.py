#!/usr/bin/env python3
"""Run the linked menu, normal command dispatch and frame owner; hardware only is modeled."""
import hashlib,json
from pathlib import Path
from check_redisplay_live import Redisplay
from check_terminal_printer_live import Printer
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX
ROOT=Path(__file__).resolve().parents[1]

class Menu(Redisplay):
 def open_menu(self):
  self.key(0x2c00)
  assert self.get('_command_menu_active') and self.get('_redisplay_active')
 def choose(self,group,index):
  self.open_menu()
  for _ in range(group):self.key(0x4d00)
  for _ in range(index):self.key(0x5000)
  self.key(13)

class MenuPrinter(Printer):
 def __init__(self):
  self.bios_position=0;self.cursor_shape=0x0607;super().__init__()
 def interrupt(self,u,n,d):
  ax=u.reg_read(UC_X86_REG_AX)
  if n==0x10:
   if ax>>8==0x0f:u.reg_write(UC_X86_REG_AX,0x5003);u.reg_write(UC_X86_REG_BX,0);return
   if ax>>8==3:u.reg_write(UC_X86_REG_DX,self.bios_position);u.reg_write(UC_X86_REG_CX,self.cursor_shape);return
   if ax>>8==2:self.bios_position=u.reg_read(UC_X86_REG_DX);return
   if ax>>8==1:self.cursor_shape=u.reg_read(UC_X86_REG_CX);return
  return super().interrupt(u,n,d)
 key=Menu.key
 open_menu=Menu.open_menu
 choose=Menu.choose

def main():
 rows=[]
 def check(name,fn):
  count=fn();rows.append(dict(case=name,inputs=count,passed=True));print(name,count,flush=True)
 def navigation():
  m=Menu();before=bytes(m.uc.mem_read(0xb8000,4000));m.bios_position=0x0405;m.open_menu()
  assert b'Receive files' in m.text(5)
  for key,want in [(0x4d00,b'Dial selected'),(9,b'Redisplay history'),(0x4d00,b'Edit saved'),(0x4d00,b'Using the'),(0x4d00,b'Receive files'),(0x4b00,b'Using the'),(0x0f00,b'Edit saved')]:
   m.key(key);assert want in m.text(5),(key,m.text(5))
  m.key(27);assert not m.get('_redisplay_active') and not m.get('_command_menu_active')
  assert bytes(m.uc.mem_read(0xb8000,4000))==before and m.bios_position==0x0405 and m.cursor_shape==0x0607
  assert not m.tx and not m.get('terminal_quit') and not m.get('_command_menu_action')
  return 9
 check('five-groups-arrow-tab-shift-tab-wrap-and-full-screen-cursor-return',navigation)
 def help_search():
  m=Menu();m.open_menu();m.key(0x3b00);assert b'Receive into' in m.text(7)
  m.key(0x5000);assert b'Choose a local' in m.text(7)
  m.key(0x4900);assert b'Receive into' in m.text(7)
  m.key(27);assert m.get('_command_menu_active') and b'Receive files' in m.text(5)
  m.key(ord('/'))
  for c in b'InTeRvAl':m.key(c)
  m.key(13);assert b'Send BREAK' in m.text(5) and b'Drain outgoing' in m.text(7)
  m.key(27);m.key(ord('/'))
  for _ in range(80):m.key(ord('z'))
  assert m.text(22).endswith(b'z'*31)
  m.key(13);assert b'No matching topic' in m.text(24)
  m.key(ord('/'));m.key(27);assert m.get('_command_menu_active')
  m.key(27);assert not m.get('_redisplay_active') and not m.tx
  return 99
 check('context-help-topic-navigation-case-insensitive-prose-search-no-match-and-bounded-query',help_search)
 def handoff():
  # Every instruction of the real dispatcher and selected owner runs.
  for group,index,key,state,want in [(0,0,0x1300,'terminal_transfer_pending',1),
   (0,1,0x1f00,'terminal_transfer_pending',1),(0,5,0x6900,'terminal_quit',0),
   (0,6,0x6a00,'terminal_cr_adds_lf',1),(1,0,0x2000,'connection_state',0),
   (1,1,0x2300,'connection_state',0),(1,2,0x3000,'uart_break_hold',1),
   (2,0,0x8400,'_redisplay_active',1),(2,1,0x8300,'_clipboard_ui_active',1),
   (2,2,0x2b1c,'terminal_monitor_active',2),(0,7,0x2d00,'terminal_quit',1),
   (3,1,0x7000,'terminal_translation_reload_status',4),(3,2,0x6f00,'terminal_translation_edit_status',4)]:
   m=Menu();direct=Menu()
   if key==0x3000:
    for model in (m,direct):
     model.put('hardware_active',1,1);model.put('vector_active',1,1)
     model.put('uart_port_lcr',0x3fb);model.put('uart_port_lsr',0x3fd)
   m.choose(group,index);direct.key(key)
   assert m.get(state)==direct.get(state)==want,(group,index,state,m.get(state),direct.get(state))
   assert not m.get('_command_menu_active') and not m.get('_command_menu_action')
   assert m.tx==direct.tx and not m.tx
   if key not in (0x8400,0x8300):assert not m.get('_redisplay_active')
  m=Menu();m.open_menu();m.key(ord('t'));assert m.get('terminal_cr_adds_lf') and not m.get('_redisplay_active')
  m=Menu();m.choose(4,0);assert m.get('_command_menu_active') and b'Alt-Z opens' in m.text(7)
  m=MenuPrinter();m.choose(2,3);assert m.device_live and not m.get('_redisplay_active')
  m.choose(2,3);assert m.get('terminal_printer_closing') and not m.get('terminal_sink_3988_enabled')
  m.call('terminal_printer_poll');assert not m.device_live and not m.get('_command_menu_action')
  m=MenuPrinter();assert m.begin()==0
  m.choose(0,5);m.log(b'HELD');m.choose(0,5);m.log(b'LIVE');m.choose(0,4)
  assert m.contents()==b'LIVE' and not m.get('terminal_sink_398a_enabled')
  return 20
 check('normal-transfer-capture-break-monitor-viewer-clipboard-exit-dispatch-and-mnemonics',handoff)
 def incoming():
  m=Menu();m.open_menu();m.key(0x3b00);screen=bytes(m.uc.mem_read(0xb8000,4000))
  m.receive(b'BACKGROUND\x1b[31m RED\x1b[0m\r\nNEXT\x1b[6n');m.drain()
  assert bytes(m.uc.mem_read(0xb8000,4000))==screen and bytes(m.tx)==b'\x1b[2;5R'
  assert not m.get('uart_rx_dropped')
  m.key(27);m.key(27);assert m.text(0)==b'BACKGROUND RED' and m.text(1)==b'NEXT'
  m=Menu();m.open_menu();m.call('terminal_redisplay_before');m.key(0x3b00)
  assert b'PCPLUS' not in m.text(0)
  m.call('terminal_redisplay_idle');assert b'Receive into' in m.text(7)
  m.call('terminal_redisplay_stop');assert not m.get('_command_menu_active') and not m.get('_redisplay_active')
  assert not m.get('_command_menu_action')
  return 3
 check('incoming-UART-parser-SGR-replies-live-frame-and-hidden-window-restoration',incoming)
 def ownership():
  flags=['terminal_parser_active','terminal_transfer_pending','terminal_transfer_active','terminal_program_pending',
   'terminal_program_active','terminal_macro_active','terminal_monitor_active','terminal_controller_active',
   'terminal_ansi_wait_active','terminal_snapshot_active','uart_break_hold','screen_viewport_enabled','text_cga_status_port']
  for name in flags:
   m=Menu();m.put(name,1);m.call('terminal_redisplay_key',ax=0x2c00)
   assert not m.get('_redisplay_active') and not m.get('_command_menu_active') and not m.get('terminal_quit'),name
  for name,value in [('text_video_segment',0xb000),('screen_attribute_row_bytes',132),('screen_video_row_bytes',264),('connection_state',2)]:
   m=Menu();m.put(name,value);m.call('terminal_redisplay_key',ax=0x2c00);assert not m.get('_command_menu_active')
  m=Menu();m.uc.mem_write(0x484,b'\x31');m.key(0x2c00);assert not m.get('_command_menu_active') and not m.get('terminal_quit')
  m=Menu();m.open_menu();m.key(0x7100);assert m.get('_command_menu_active') and not m.get('terminal_program_pending')
  m.key(0x7000);assert m.get('_command_menu_active') and not m.get('terminal_program_pending')
  m.key(0x6f00);assert m.get('_command_menu_active') and not m.get('terminal_program_pending')
  m.key(0x2d00);assert m.get('terminal_quit') and not m.get('_redisplay_active')
  return len(flags)+9
 check('every-open-owner-geometry-modem-guard-nested-setup-suppression-and-direct-AltX',ownership)
 result=dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),
  cases=rows,inputs=sum(r['inputs'] for r in rows),sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
   ['src/redisplay/command_menu.c','src/redisplay/command_menu.h','src/redisplay/redisplay.c','src/terminal/redisplay.asm','standalone/check_command_menu_live.py','standalone/check_terminal_printer_live.py','standalone/check_terminal_capture_live.py','standalone/check_terminal_monitor_live.py']},
  scope='Actual linked menu/far constants, transport dispatch, frame owner and selected services. BIOS/UART/video and DOS filesystem/PRN kernel boundaries are modeled; no product function is replaced. Actual DOS file/BBS workflows require separate evidence. Maintained UI, not original menu equivalence.')
 (ROOT/'build/terminal/command-menu-checks.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
