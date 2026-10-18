#!/usr/bin/env python3
"""Actual linked maintained RIS/startup snapshot; only hardware is modeled."""
import hashlib,json,re,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_CX,UC_X86_REG_ES,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI
from check_line_edit_live import Live as BaseLive,Abort
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'src/terminal/terminal_reset.asm').read_text()
WORDS=re.findall(r'^ dw (\w+)$',SOURCE.split('reset_word_addresses:\n',1)[1].split('RESET_WORD_COUNT equ',1)[0],re.M)
BYTES=re.findall(r'^ dw (\w+)$',SOURCE.split('reset_byte_addresses:\n',1)[1].split('RESET_BYTE_COUNT equ',1)[0],re.M)
class Live(BaseLive):
 def interrupt(self,u,n,unused):
  if n==0x10 and u.reg_read(UC_X86_REG_AX)>>8==1:
   self.cursor_shape=u.reg_read(UC_X86_REG_CX);return
  return super().interrupt(u,n,unused)
def read(t,name,n):return bytes(t.uc.mem_read(t.symbols[name],n))
def write(t,name,data):t.uc.mem_write(t.symbols[name],bytes(data))
def prepare(profile=6,explicit=False):
 t=Live();t.put('csi_terminal_id',profile);t.put('attributes_monochrome',int(profile==6))
 t.call('csi_clear_tabs',[1]);t.call('terminal_clear_home')
 if explicit:
  mapping=bytearray((i*37+17)%256 for i in range(948))
  for slot,last in zip(range(72,76),b'ABDC'):mapping[slot*12:slot*12+4]=bytes([27,91,last,0])
  write(t,'terminal_keymap',mapping)
 assert t.call('terminal_reset_capture')==0
 return t

def run():
 cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def reset_dirty():
  for profile in (4,6):
   t=prepare(profile);baseline={x:t.get(x) for x in WORDS};basebytes={x:read(t,x,1) for x in BYTES};tabs=read(t,'terminal_tab_stops',30)
   for name in WORDS:t.put(name,0xffff)
   for name in BYTES:write(t,name,b'\xff')
   for name,size in [('screen_attribute_cells',4096),('erase_attribute_values',4096),('erase_shadow_cells',8192),('screen_line_flags',128)]:write(t,name,b'\xff'*size)
   write(t,'ansi_parameters',b'\xff'*32);write(t,'terminal_tab_stops',b'\xff'*30)
   t.call('csi_reset_terminal',[1],limit=1000000)
   for name,value in baseline.items():assert t.get(name)==value,(profile,name,t.get(name),value)
   for name,value in basebytes.items():assert read(t,name,1)==value,(profile,name)
   for name,size in [('screen_attribute_cells',4096),('erase_attribute_values',4096),('erase_shadow_cells',8192),('screen_line_flags',128),('ansi_parameters',32)]:assert read(t,name,size)==bytes(size),(profile,name)
   assert read(t,'terminal_tab_stops',30)==tabs and t.cells()==[0x0720]*2000
   assert t.get('ansi_parameter_canary')==0xa55a and t.cursor_shape==0x060f
 check('both-profiles-all-named-state-dirty-margins-pointers-protection-and-full-metadata',reset_dirty)
 def parser():
  for profile in (4,6):
   t=prepare(profile);t.feed(b'\x1b[3;12r\x1b[?6h\x1b[31;1;5m\x1b[?7l\x1b[?25l\x1bcOK')
   assert t.get('csi_terminal_id')==profile and t.get('attributes_current')==7
   assert not t.get('csi_origin_mode') and t.get('screen_first_row')==0 and t.get('screen_last_row')==24
   assert t.get('cursor_state_value_1d20')==1 and t.get('cursor_shape_visibility_state')==1
   assert t.cells()[:2]==[0x074f,0x074b] and t.get('screen_cursor_column')==2
 check('real-UART-parser-RIS-after-margins-origin-SGR-wrap-and-hidden-cursor',parser)
 def keymap():
  for explicit in (False,True):
   t=prepare(explicit=explicit);base=read(t,'terminal_keymap',948);flag=t.get('terminal_dec_keys')
   t.feed(b'\x1b[?1h');assert read(t,'terminal_keymap',948)!=base
   t.feed(b'\x1bc');assert read(t,'terminal_keymap',948)==base and t.get('terminal_dec_keys')==flag
   t.feed(b'\x1b[?1l\x1bc');assert read(t,'terminal_keymap',948)==base
 check('DECCKM-then-RIS-restores-all79-slots-including-explicit-binary-KBD-baseline',keymap)
 def configured():
  for profile in (4,6):
   t=prepare(profile,True)
   for name,value in [('attributes_normal_value',0x1e),('attributes_bold_value',0x2f),('attributes_reverse_value',0x61),('attributes_preset_value',0x35),('attributes_underline_value',0x48),('cursor_state_value_1d20',0),('scroll_enabled',0)]:t.put(name,value)
   write(t,'csi_erase_attribute',b'\x1e');t.call('terminal_clear_home');assert t.call('terminal_reset_capture')==0
   base={name:t.get(name) for name in ['attributes_normal_value','attributes_bold_value','attributes_reverse_value','attributes_preset_value','attributes_underline_value','cursor_state_value_1d20','scroll_enabled']}
   t.feed(b'\x1b[3;12r\x1b[?7h\x1b[31;1;5m\x1bc')
   assert all(t.get(name)==value for name,value in base.items()) and t.cells()==[0x1e20]*2000
 check('nondefault-imported-palette-wrap-scroll-restored-as-configured-not-hardcoded',configured)
 def preserve():
  t=prepare();names=['uart_software_flow','uart_hardware_flow','uart_tx_paused','uart_rx_count','uart_rx_read','uart_rx_write','terminal_option_mask','terminal_directory_entry','terminal_keyboard_bios_selection','terminal_ansi_m_policy','terminal_tx_head','terminal_tx_tail','terminal_tx_count','terminal_port_number','terminal_baud_low','terminal_baud_high','terminal_parity','terminal_data_bits','terminal_stop_bits','terminal_quit','terminal_exit_code','connection_state','terminal_sink_3988_enabled','terminal_sink_398a_enabled','terminal_sink_398c_disabled','terminal_sink_handle','terminal_sink_error_state','render_translation_enabled','terminal_history_wrapped']
  for i,name in enumerate(names):t.put(name,0x120+i)
  before={name:t.get(name) for name in names}
  write(t,'terminal_tx_buffer',bytes(i%256 for i in range(1024)));tx=read(t,'terminal_tx_buffer',1024)
  write(t,'terminal_history_buffer',bytes(i%256 for i in range(4096)));history=read(t,'terminal_history_buffer',4096)
  t.call('csi_reset_terminal',limit=1000000)
  assert before=={name:t.get(name) for name in names} and read(t,'terminal_tx_buffer',1024)==tx and read(t,'terminal_history_buffer',4096)==history and not t.tx
 check('UART-flow-TX-source-settings-connection-sinks-translation-and-history-preserved',preserve)
 def abi():
  t=prepare()
  for entry in ('terminal_reset_capture','csi_reset_terminal'):
   t.uc.reg_write(UC_X86_REG_ES,0x4321);DosImage.call(t,entry,limit=1000000)
   for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0x4321)]:assert t.uc.reg_read(reg)==value,(entry,reg)
 check('cdecl-argument-not-consumed-and-near-BP-SI-DI-arbitrary-ES-preserved',abi)
 def no_capture():
  t=Live()
  try:t.call('csi_reset_terminal')
  except Abort as e:assert e.args==(0x20a4,)
  else:raise AssertionError('Reset without startup baseline silently succeeded')
  for profile in (0,5,32,65535):
   t=Live();t.put('csi_terminal_id',profile);assert t.call('terminal_reset_capture')==1
 check('unsupported-profile-or-uncaptured-baseline-remains-explicit',no_capture)
 result={'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Maintained current-profile RIS policy, actual linked input/ESC/clear-home/erase/cursor/UART code, hardware-only video/keyboard/UART oracle. Startup baseline restored without file IO. No native20a4 equivalence or full profile-loader claim.'}
 (ROOT/'build/terminal/terminal-reset-live-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Maintained RIS:',len(cases),'groups passed')
if __name__=='__main__':run()
