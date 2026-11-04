#!/usr/bin/env python3
"""Execute linked local commands through BIOS keys and the actual Alt-Z owner."""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
a.output.mkdir(parents=True,exist_ok=False);binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_local_controls']
transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
from check_recording_ui_live import UI as BaseUI
from check_recording_rx_live import ordinary
class UI(BaseUI):
 def interrupt(self,u,n,d):
  if n==0x10 and u.reg_read(UC_X86_REG_AX)>>8==1:return
  super().interrupt(u,n,d)
cases=[]
def done(name,inputs):cases.append(dict(case=name,inputs=inputs,passed=True));print(name,inputs,'PASS')
def snapshot(m):return bytes(m.uc.mem_read(0xb8000,4000))
for key in (0x2e00,0x1600):
 m=UI();ordinary(m,b'BEFORE');m.put('modes_value_1d1a',1)
 history=bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'],63000));pointer=m.get('terminal_history_pointer')
 m.key(key);assert m.get('screen_cursor_column')==0 and m.get('screen_cursor_row')==0
 assert b'BEFORE' not in m.text() and not m.tx and not m.get('terminal_quit')
 assert not m.get('_redisplay_active') and m.get('connection_state')==0
 assert bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'],63000))==history and m.get('terminal_history_pointer')==pointer
 assert m.get('modes_value_1d1a')==(0 if key==0x1600 else 1)
 done('direct-clear-reset-keeps-history-serial-and-no-wire-'+hex(key),1)
for initial in (0,1,2,0xffff):
 m=UI();m.put('modes_value_1d1a',initial);screen=snapshot(m);m.key(0x1200)
 assert m.get('modes_value_1d1a')==int(initial==0) and snapshot(m)==screen and not m.tx
 m.key(ord('x'));m.drain();assert bytes(m.tx)==b'x'
 assert m.text().startswith(b'x')==(initial==0)
 done('duplex-native-word-policy-and-ordinary-echo-'+str(initial),1)
# Each unsafe foreground owner must defer once without executing or sending.
for field in ('terminal_parser_active','terminal_macro_active','terminal_program_pending','terminal_program_active','terminal_transfer_pending','terminal_transfer_active','terminal_aspect_active','terminal_ansi_wait_active','terminal_snapshot_active','uart_break_hold','_redisplay_active','_command_menu_active','terminal_monitor_active','terminal_controller_active'):
 m=UI();ordinary(m,b'KEPT');before=snapshot(m);m.put(field,1)
 # Directly exercise the far key service: owner-specific BIOS dispatch remains
 # tested separately; do not fake the service's admission or its queue call.
 u=m.uc;sp=m.offset('terminal_stack_top')-4;entry=m.symbols['terminal_local_control_key'];u.mem_write(m.data_base+sp,struct.pack('<HH',m.return_offset,m.code_segment))
 for reg,value in [(UC_X86_REG_CS,m.base_segment+next(c['relative_segment'] for c in manifest['memory_layout']['code_segments'] if c['name']=='CONFIG_CODE')),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_AX,0x2e00)]:u.reg_write(reg,value)
 m.returned=False;u.emu_start(entry,0,count=100000)
 assert m.returned and u.reg_read(UC_X86_REG_EFLAGS)&1 and m.get('terminal_local_control_status')==1
 assert snapshot(m)==before and not m.tx and m.get('terminal_deferred_count')==1
 m.put(field,0);m.call('terminal_poll_io',limit=1000000)
 assert not m.get('terminal_deferred_count') and b'KEPT' not in m.text() and not m.tx
 done('defer-and-run-once-after-'+field,1)
for field in ('terminal_browser_screen_owned','terminal_editor_screen_owned'):
 m=UI();ordinary(m,b'KEPT');before=snapshot(m);m.put(field,1,1)
 u=m.uc;sp=m.offset('terminal_stack_top')-4;entry=m.symbols['terminal_local_control_key'];u.mem_write(m.data_base+sp,struct.pack('<HH',m.return_offset,m.code_segment))
 for reg,value in [(UC_X86_REG_CS,m.base_segment+next(c['relative_segment'] for c in manifest['memory_layout']['code_segments'] if c['name']=='CONFIG_CODE')),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_AX,0x2e00)]:u.reg_write(reg,value)
 m.returned=False;u.emu_start(entry,0,count=100000)
 assert m.returned and m.get('terminal_local_control_status')==1 and snapshot(m)==before and m.get('terminal_deferred_count')==1
 m.put(field,0,1);m.call('terminal_poll_io',limit=1000000)
 assert not m.get('terminal_deferred_count') and b'KEPT' not in m.text() and not m.tx
 done('byte-owner-defer-and-run-once-after-'+field,1)
m=UI();ordinary(m,b'KEPT');before=snapshot(m);m.put('reset_ready',0);m.key(0x1600)
assert m.get('terminal_local_control_status')==2 and snapshot(m)==before and not m.tx and not m.get('terminal_quit')
done('missing-reset-baseline-refuses-without-mutation',1)
for key in (0x2e00,0x1600,0x1200):
 m=UI();ordinary(m,b'LIVE');m.key(0x2c00);assert m.get('_command_menu_active')
 m.key(key);assert not m.get('_redisplay_active') and not m.get('_command_menu_active')
 assert not m.tx and not m.get('terminal_quit')
 if key==0x1200:assert m.get('modes_value_1d1a')==1 and m.text().startswith(b'LIVE')
 else:assert m.get('screen_cursor_column')==0 and b'LIVE' not in m.text()
 ordinary(m,b'AFTER\x1b[6n');m.drain();assert bytes(m.tx).endswith(b'R')
 done('reference-action-restores-frame-before-dispatch-'+hex(key),1)
report=dict(passed=True,terminal_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),cases=cases,scope='Actual linked parent keyboard/menu/control/renderer/deferred FIFO code. Only BIOS/UART/DOS boundaries modeled. Not actual DOS/hardware acceptance.')
(a.output/'result.json').write_text(json.dumps(report,indent=2)+'\n')
