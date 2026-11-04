#!/usr/bin/env python3
"""Actual keyboard/menu Ctrl-] dispatch and offline status transaction.
Linked instructions execute; BIOS/UART/DOS boundaries modeled, no physical claim.
"""
import argparse,hashlib,json,struct
from unicorn.x86_const import *
from pathlib import Path
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_status_control'];assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from check_status_transition_live import Transaction
 from check_recording_rx_live import ordinary
 cases=[]
 def done(name,count):cases.append(dict(case=name,inputs=count,passed=True));print(name,count,'PASS',flush=True)
 def state(m,hidden):
  assert m.get('ui_flow_suppressed')==hidden and m.get('csi_row_count')==24+hidden
  assert m.get('csi_last_row')==23+hidden and m.get('erase_cell_count')==(24+hidden)*80
  assert m.get('terminal_local_control_status')==0 and not m.get('_redisplay_active') and not m.get('_command_menu_active')
  assert not m.get('terminal_quit') and not m.tx
 for key in [0x1b1d,0x001d,0xe01d]:
  m=Transaction();ordinary(m,b'LIVE');history=bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'],63000))
  m.key(key);state(m,1);m.key(key);state(m,0)
  assert bytes(m.uc.mem_read(m.symbols['terminal_history_buffer'],63000))==history
 done('normalized-direct-status-keys-toggle-once-each-and-retain-history',6)
 for origin in ['reference','browser']:
  m=Transaction();ordinary(m,b'LIVE');m.key(0x2c00)
  if origin=='reference':
   m.key(0x1b1d)
  else:
   m.key(0x2960);m.key(0x4d00);m.key(0x4d00);m.key(ord('S'))
  state(m,1);assert m.text().startswith(b'LIVE')
  m.key(0x2c00);m.key(0x1b1d);state(m,0)
 done('reference-and-browser-release-frame-before-status-transaction',4)
 m=Transaction();m.key(0x2c00);m.key(0x1b1d) # Dispatch from reference.
 state(m,1);ordinary(m,b'\x1b[25;80H\x1b[6n');m.drain();assert bytes(m.tx)==b'\x1b[25;80R'
 m.tx.clear();m.key(0x1b1d);state(m,0);ordinary(m,b'\x1b[25;80H\x1b[6n');m.drain();assert bytes(m.tx)==b'\x1b[24;80R'
 done('genuine-CPR-uses-accepted-area-after-key-and-menu',2)
 for connection in [1,2,3,4,5,6]:
  m=Transaction();m.put('connection_state',connection);before=m.snapshot();m.key(0x1b1d)
  if connection==6:
   assert m.get('terminal_local_control_status')==3 and m.snapshot()==before
  else:
   assert m.get('terminal_local_control_status')==1 and m.get('terminal_deferred_count')==1
  assert not m.get('_redisplay_active') and not m.tx and not m.get('terminal_quit')
 done('connecting-defers-and-online-status-change-refuses-without-wire-or-view',6)
 for field in ['terminal_parser_active','terminal_macro_active','terminal_program_pending','terminal_program_active','terminal_transfer_pending','terminal_transfer_active','terminal_aspect_active','terminal_ansi_wait_active','terminal_snapshot_active','uart_break_hold']:
  m=Transaction();m.put(field,1);before=m.get('ui_flow_suppressed')
  # Exercise the real shared far owner. Synthetic busy flags are not a valid
  # running macro/program fixture for the outer scheduler to service.
  u=m.uc;sp=m.offset('terminal_stack_top')-4
  cs=m.base_segment+next(c['relative_segment'] for c in manifest['memory_layout']['code_segments'] if c['name']=='CONFIG_CODE')
  u.mem_write(m.data_base+sp,struct.pack('<HH',m.return_offset,m.code_segment))
  for reg,value in [(UC_X86_REG_CS,cs),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds),(UC_X86_REG_SP,sp),(UC_X86_REG_AX,0x1b1d)]:u.reg_write(reg,value)
  m.returned=False;u.emu_start(m.symbols['terminal_local_control_key'],0,count=100000)
  assert m.returned and u.reg_read(UC_X86_REG_EFLAGS)&1 and u.reg_read(UC_X86_REG_AX)==0x1b1d
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==m.ds
  assert m.get('terminal_deferred_count')==1 and m.get('ui_flow_suppressed')==before and not m.tx,field
  m.put(field,0);m.call('terminal_poll_io',limit=1000000);state(m,1)
  assert not m.get('terminal_deferred_count'),field
 done('busy-owner-keys-defer-and-execute-once-after-release',10)
 for field,value in [('ui_window_rows',43),('screen_attribute_row_bytes',132),('screen_viewport_enabled',1),('reset_ready',0)]:
  m=Transaction();m.put(field,value);before=m.snapshot();m.key(0x1b1d)
  assert m.get('terminal_local_control_status')==(2 if field=='reset_ready' else 3)
  assert m.snapshot()==before and not m.tx and not m.get('_redisplay_active')
 done('unsupported-geometry-and-missing-baseline-refuse-without-mutation',4)
 class WithClock(Transaction):
  def interrupt(self,u,n,d):
   if n==0x21 and u.reg_read(UC_X86_REG_AX)==0x2a00:
    u.reg_write(UC_X86_REG_CX,1993);u.reg_write(UC_X86_REG_DX,0x0307);u.reg_write(UC_X86_REG_AX,0);return
   if n==0x21 and u.reg_read(UC_X86_REG_AX)==0x2c00:
    u.reg_write(UC_X86_REG_CX,0x0c00);u.reg_write(UC_X86_REG_DX,0);return
   return super().interrupt(u,n,d)
 for key in [0x2c00,0x8400,0x8300,0x1400]:
  m=WithClock() if key==0x1400 else Transaction();m.key(key);assert m.get('_redisplay_active')
  m.key(27);assert not m.get('_redisplay_active') and not m.get('_clipboard_ui_visible')
  m.key(0x1b1d);state(m,1)
 done('closed-menu-history-clipboard-and-elapsed-release-visibility-before-next-command',4)
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 report=dict(passed=True,cases=cases,inputs=sum(c['inputs'] for c in cases),terminal_sha256=sha(binary),source_inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'standalone/check_status_transition_live.py',ROOT/'standalone/check_recording_rx_live.py',ROOT/'standalone/check_recording_ui_live.py']},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
