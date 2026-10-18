#!/usr/bin/env python3
"""Linked asynchronous dedicated-print owner, grammar, UART ISR and PRN kernel.
No product callbacks skipped; only DOS device/filesystem, BIOS/UART modeled.
"""
import hashlib,json
from unicorn.x86_const import *
from check_terminal_screen_print_live import ScreenPrint
from check_meta_actions_live import ROOT,BINARY,DAY
class Controller(ScreenPrint):
 def start_controller(self):
  self.preserved('terminal_controller_start')
 def poll_controller(self):
  self.poll_printer();self.preserved('terminal_controller_poll')
 def consume(self,value):
  ax=self.call('terminal_controller_filter',ax=value)
  assert ax==value,'filter must preserve actual received AX'
  assert self.uc.reg_read(UC_X86_REG_EFLAGS)&0x200
  for reg,value in ((UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)):assert self.uc.reg_read(reg)==value
  return bool(self.uc.reg_read(UC_X86_REG_EFLAGS)&1)
 def feed_controller(self,data):
  self.rx.extend(data);consumed=[]
  for _ in range(10000):
   if not self.get('terminal_controller_active'):break
   if self.call('terminal_controller_receive_hold'):
    self.poll_controller();continue
   if not self.rx and not self.get('uart_rx_count'):break
   value=self.call('uart_receive_byte')
   if value==65535:continue
   assert self.consume(value);consumed.append(value)
   self.poll_controller()
  else:raise AssertionError('controller feed failed to progress')
  return bytes(consumed)
 def finish_controller(self):
  for _ in range(32):
   if not self.get('terminal_controller_active'):return
   self.poll_controller()
  raise AssertionError('controller failed to drain')
 def controller_key(self,key):
  result=self.call('terminal_controller_key',ax=key)
  assert result==key
  return bool(self.uc.reg_read(UC_X86_REG_EFLAGS)&1)

def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();groups=[]
 def check(name,fn):
  n=fn();groups.append(dict(case=name,inputs=n,passed=True));print(name,'PASS',n,flush=True)
 def raw():
  m=Controller();assert m.begin()==0;m.log(b'BEFORE');m.call('_capture_session_flush')
  video=bytes(m.uc.mem_read(0xb8000,3840));m.start_controller()
  assert m.get('terminal_controller_active')==1 and m.device_live
  data=bytes(range(256));assert m.feed_controller(data)==data
  assert m.device_bytes==bytes(x for x in data if x not in (0,127))
  assert m.contents()==b'BEFORE' and bytes(m.uc.mem_read(0xb8000,3840))==video
  m.feed_controller(b'\x1b[4iAPP');m.finish_controller()
  assert not m.device_live and m.get('terminal_controller_last_action')==2
  assert m.call('uart_receive_byte')==ord('A') and m.call('uart_receive_byte')==ord('P') and m.call('uart_receive_byte')==ord('P')
  assert m.owner()[10]==1 and not m.get('terminal_sink_3988_enabled')
  assert m.call('_capture_session_stop')==0
  return 256
 check('async-start-UART-all256-DC4-single-NUL-DEL-drop-capture-render-exclusion-postdata',raw)
 def real_csi():
  m=Controller();assert m.begin()==0;m.log(b'BEFORE');m.call('_capture_session_flush')
  raw=bytes(range(256));m.csi(b'\x1b[5i'+raw+b'\x1b[4iAPP')
  assert m.device_bytes==bytes(x for x in raw if x not in (0,127))
  assert not m.get('terminal_controller_active') and not m.device_live and m.owner()[10]==1
  m.call('_capture_session_flush');assert m.contents()==b'BEFOREAPP'
  m=Controller();m.csi(b'\x1b[5;0iRAW\x1b[4i')
  assert m.device_bytes==b'RAW'+m.expected() and m.owner()[10]==1
  assert sum(c[0]>>8==0x3e for c in m.device_calls)==2
  return 2
 check('actual-CSI5-run-wrapper-postdata-normal-parser-and5semicolon0-ordered-screenprint',real_csi)
 def pending_capture_timer():
  m=Controller();assert m.begin()==0;m.log(b'BEFORE');assert m.get('_capture_session_buffered')==6
  m.advance_ticks=True;m.csi(b'\x1b[5i'+bytes(range(256))+b'\x1b[4iAPP')
  assert m.tick>=18 and m.contents()==b'BEFORE' and m.get('_capture_session_buffered')==3
  assert m.device_bytes==bytes(x for x in range(256) if x not in (0,127))
  assert m.call('_capture_session_stop')==0 and m.contents()==b'BEFOREAPP'
  return 1
 check('real-modal-controller-services-pending18tick-textcapture-without-logging-raw',pending_capture_timer)
 def grammar():
  for seq in (b'\x1b[4i',b'\x1b[14i',b'\x1b[4;5i',b'\x1b[\0\x7f4i'):
   m=Controller();m.start_controller()
   for byte in seq:m.feed_controller(bytes([byte]))
   m.finish_controller();assert not m.device_bytes and not m.device_live
  m=Controller();m.start_controller();m.feed_controller(b'A\x1b[5iB\x1b[0iC\x1b[4i');m.finish_controller();assert m.device_bytes==b'ABC'
  for seq in (b'\x1bZ',b'\x1b[Z',b'\x1b\x1b',b'\x1b4iX\x1b[4i'):
   m=Controller();m.start_controller();m.feed_controller(seq)
   if m.get('terminal_controller_buffer_count'):
    m.tick=36;m.poll_controller();m.finish()
   assert m.device_bytes==seq,(seq,bytes(m.device_bytes))
   m.controller_key(27);m.controller_key(27);m.finish_controller()
  for profile,other,seq in [(1,0,b'\x1bX'),(6,1,b'\x1ba'),(31,0,b'\x14')]:
   m=Controller();m.put('csi_terminal_id',profile);m.put('render_linefeed_suppression_enabled',other);m.start_controller();m.feed_controller(seq);m.finish_controller()
   assert not m.device_bytes and not m.device_live
  return 12
 check('fragmented-native-any4-bracket-i-discarded-oncodes-unknown-nested-and-profile-exits',grammar)
 def bounds():
  for initial in (0,0xfff8,DAY-8):
   m=Controller();m.tick=initial;m.start_controller();m.feed_controller(b'\x1b[1')
   assert not m.device_bytes and m.get('terminal_controller_buffer_count')==3
   m.tick=(initial+35)%DAY;m.poll_controller();assert not m.device_bytes
   m.tick=(initial+36)%DAY;m.poll_controller();m.poll_printer()
   assert m.device_bytes==b'\x1b[1' and not m.get('terminal_controller_buffer_count') and m.get('terminal_controller_active')==1
   m.controller_key(27);m.controller_key(27);m.finish_controller()
  m=Controller();m.start_controller();prefix=b'\x1b'+b'1'*31;m.feed_controller(prefix)
  assert m.get('terminal_controller_buffer_count')==32 and not m.device_bytes
  m.feed_controller(b'2');m.poll_printer();m.finish()
  assert m.device_bytes==prefix+b'2' and not m.get('terminal_controller_buffer_count')
  m.controller_key(27);m.controller_key(27);m.finish_controller()
  return 4
 check('32byte-prefix-plus-overflowliteral-and36firstbyte-fulltick-midnight-noFFFF',bounds)
 def queue_hold():
  m=Controller();m.start_controller();m.device_ready=0

  for _ in range(95):m.call('terminal_printer_put_raw',[ord('Q')])
  assert m.call('terminal_controller_receive_hold')==0
  for byte in b'\x1b'+b'1'*31:assert m.consume(byte)
  assert m.consume(ord('2')) and m.get('terminal_printer_count')==128
  assert m.call('terminal_controller_receive_hold')==1 and not m.get('terminal_printer_sticky')
  m.device_ready=255;m.poll_printer();assert m.call('terminal_controller_receive_hold')==1
  m.finish();assert m.device_bytes==b'Q'*95+b'\x1b'+b'1'*31+b'2'
  m.feed_controller(b'\x1b[4iAPP');assert m.get('terminal_controller_active') in (0,2)
  m.finish_controller();assert m.call('uart_receive_byte')==65
  return 2
 check('real-queue95-reserves33-overflow-bytes-and-draining-holds-post-terminator-RX',queue_hold)
 def ownership():
  m=Controller();m.toggle();m.queue(b'BEFORE');m.start_controller()
  assert m.get('terminal_controller_active')==1 and not m.get('terminal_sink_3988_enabled')
  m.feed_controller(b'RAW\x1b[4i');m.finish_controller()
  assert m.device_live and m.get('terminal_sink_3988_enabled') and m.device_bytes==b'BEFORERAW' and m.owner()[10]==0
  m.log(b'AFTER');m.finish();m.toggle();m.finish();assert m.device_bytes==b'BEFORERAWAFTER' and m.owner()[10]==1
  for fault in ('open','write','short','close','close-drop'):
   m=Controller(printer_fault=fault);m.start_controller()
   if fault=='open':assert not m.get('terminal_controller_active') and not m.get('terminal_printer_sticky');continue
   m.feed_controller(b'A\x1b[4i');m.finish_controller()
   assert m.get('terminal_controller_last_action')==4 and m.get('terminal_printer_sticky') in (9,11)
   assert m.owner()[10]==1
   before=list(m.device_calls);m.poll_controller();m.call('terminal_controller_shutdown')
   assert m.device_calls==before
  m=Controller();m.toggle();m.queue(b'X');m.printer_fault='write';m.poll_printer();assert m.get('terminal_printer_sticky')==9
  m.printer_fault=None;m.start_controller();m.feed_controller(b'OK\x1b[4i');m.finish_controller()
  assert m.device_bytes==b'OK' and m.get('terminal_controller_last_action')==2 and m.get('terminal_printer_sticky')==9
  return 7
 check('borrowed-copy-queue-order-restoration-temporary-close-faults-and-priorsticky',ownership)
 def admission_and_flow():
  for software,mask in ((0,127),(1,255)):
   m=Controller();m.put('uart_software_flow',software);m.put('uart_rx_mask',mask);m.start_controller()
   data=bytes(range(256));m.feed_controller(data)
   assert m.device_bytes==bytes(x&mask for x in data if (not software or x not in (17,19)) and (x&mask) not in (0,127))
   m.feed_controller(b'\x1b[4i');m.finish_controller()
  m=Controller();m.start_controller();m.feed_controller(b'\x1b[1')
  before=list(m.device_calls);assert m.call('terminal_capture_before_program')==1 and m.get('terminal_controller_active')==1
  m.call('terminal_transfer_start');assert not m.get('terminal_transfer_pending') and m.device_calls==before
  m.call('terminal_controller_shutdown');m.finish_controller();assert m.device_bytes==b'\x1b[1' and m.owner()[10]==1
  m=Controller();m.toggle();m.queue(b'QUEUED');m.toggle();assert m.get('terminal_printer_closing')
  m.device_ready=0;m.start_controller();assert m.get('terminal_controller_active')==3 and m.call('terminal_controller_receive_hold')==1
  m.rx.extend(b'WAITING');m.poll_controller();assert bytes(m.rx)==b'' and m.get('uart_rx_count')==7 and m.get('terminal_controller_active')==3
  m.device_ready=255;m.poll_controller();assert m.get('terminal_controller_active')==1 and m.device_bytes==b'QUEUED'
  m.feed_controller(b'\x1b[4i');m.finish_controller();assert m.device_bytes==b'QUEUEDWAITING'
  return 4
 check('UART-mask-flow-native-boundary-PROGRAM-transfer-denial-shutdown-prefix-pending-admission',admission_and_flow)
 def cancellation_and_carrier():
  m=Controller();m.start_controller();m.feed_controller(b'\x1b[1');m.controller_key(27);m.controller_key(27);m.finish_controller()
  assert m.device_bytes==b'\x1b[1' and m.get('terminal_controller_last_action')==5
  before=bytes(m.device_bytes);m.poll_controller();assert m.device_bytes==before
  m=Controller();m.start_controller();m.feed_controller(b'\x1b[2');m.poll_controller();m.carrier=False;m.poll_controller();m.finish_controller()
  assert m.device_bytes==b'\x1b[2' and m.get('terminal_controller_last_action')==5 and not m.device_live
  m=Controller();m.start_controller();m.device_ready=0;m.feed_controller(b'STALLED');m.advance_ticks=True
  m.call('terminal_controller_shutdown',limit=1000000)
  assert not m.get('terminal_controller_active') and m.get('terminal_printer_sticky')==14 and not m.device_live
  m=Controller();m.toggle();m.queue(b'WAIT');m.toggle();m.device_ready=0;m.start_controller();assert m.get('terminal_controller_active')==3
  m.controller_key(27);m.controller_key(27);m.device_ready=255;m.finish_controller()
  assert not m.get('terminal_controller_active') and not m.device_live and m.device_bytes==b'WAIT'
  assert sum(c[0]>>8==0x3e for c in m.device_calls)==1
  return 4
 check('localstop-carrier-replay-prefix-once-shutdown-bound-preadmission-cancel-no-newhandle',cancellation_and_carrier)
 def carrier_entry_race():
  # The real connection owner has already observed a carrier. The dedicated
  # owner starts after DCD falls, before it can observe its own first high.
  m=Controller();m.put('connection_state',6);m.call('terminal_connection_poll')
  m.carrier=False;m.start_controller();assert m.get('terminal_controller_active')==1
  m.rx.extend(b'NO_PRINT');m.call('terminal_poll_serial')
  assert m.get('connection_state')==0 and m.get('uart_rx_count')==8
  before=m.get('uart_rx_count');m.poll_controller();m.finish_controller()
  assert m.get('terminal_controller_last_action')==5 and not m.device_live and not m.device_bytes
  assert m.get('uart_rx_count')==before and m.owner()[10]==1
  assert bytes(m.call('uart_receive_byte') for _ in range(before))==b'NO_PRINT'
  # Stable DIRECT state6 deliberately permits a modem without DCD. Neither
  # owner has observed a high and the connection owner has not changed state.
  m=Controller();m.put('connection_state',6);m.carrier=False;m.start_controller();m.poll_controller()
  assert m.get('terminal_controller_active')==1 and m.device_live
  m.feed_controller(b'DIRECT\x1b[4i');m.finish_controller()
  assert m.device_bytes==b'DIRECT' and m.get('terminal_controller_last_action')==2
  # Raw idle sessions deliberately do not require DCD; preserve that use case.
  m=Controller();m.carrier=False;m.start_controller();m.poll_controller()
  assert m.get('terminal_controller_active')==1 and m.device_live
  m.feed_controller(b'RAW\x1b[4i');m.finish_controller()
  assert m.device_bytes==b'RAW' and m.get('terminal_controller_last_action')==2
  return 3
 check('carrier-connected-entry-race-after-real-connection-poll-preserves-RX-idle-low-stays-valid',carrier_entry_race)
 def keys():
  for key in (27,0x011b):
   m=Controller();m.start_controller();assert m.controller_key(key);m.drain();assert bytes(m.tx)==b'\x1b'
   m.feed_controller(b'RECEIVED');assert m.controller_key(key);m.finish_controller();assert not m.device_live
  for key in (0x2d00,0x2300):
   m=Controller();m.start_controller();assert not m.controller_key(key);m.finish_controller();assert not m.device_live
  m=Controller();m.start_controller()
  for key in (ord('q'),0x4800,0x4b00):assert m.controller_key(key)
  m.drain();assert bytes(m.tx)==b'q\x1b[A\x1b[D'
  before=bytes(m.tx)
  for key in (0x6800,0x2600,0x7800,0x2200,0x2b1c):assert m.controller_key(key)
  assert bytes(m.tx)==before and not m.get('terminal_sink_398a_enabled') and not m.get('terminal_monitor_active') and not m.get('terminal_macro_active') and not m.get('terminal_snapshot_active') and not m.get('terminal_program_pending')
  m.call('terminal_controller_shutdown');m.finish_controller();assert not m.device_live
  return 5
 check('double-BIOS-ASCII-Escape-firstwire-local-blocking-networkkeys-AltX-AltH-handoff',keys)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest
 result=dict(binary_sha256=digest,passed=True,groups=groups,regression_history=[dict(binary_sha256='d6d15a55ac9d7b3758da7c365e9970b1648b3b3b4da03d62db2298bb06f2526b',case='first BIOS Escape011B consumed but not transmitted',observed_wire_hex='',expected_wire_hex='1b',normalized001B_wire_hex='1b',fix='First ASCII Escape bypasses raw-key classifier and enqueues literal1B; both word forms are normative keys-group regressions',verified_current_binary=digest)],scope='Actual source-linked dedicated-print controller, UART ISR, bounded grammar, network key mapping, checked PRN queue/device owner. Only hardware/BIOS/DOS kernel modeled; no physical printer or syscall time bound claimed.')
 path=ROOT/'build/terminal/terminal-print-controller-live-checks.json';path.write_text(json.dumps(result,indent=2)+'\n');print(path)
if __name__=='__main__':main()
