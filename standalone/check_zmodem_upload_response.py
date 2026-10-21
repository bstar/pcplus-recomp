#!/usr/bin/env python3
"""Retain the linked sender's premature-replay counterexample.

Only BIOS time, UART peer input and DOS kernel boundaries are modeled. The
production engine, far adapter, watchdog, file owner and UART ISR all execute.
This is deliberately not an upload acceptance test or a cleanup test for the
interrupted failing case.
"""
from collections import deque
import hashlib,json
from pathlib import Path
from check_terminal_zmodem_live import LiveZmodem
from check_zmodem import h,send_meta
from check_zmodem_wire import packet

ROOT=Path(__file__).resolve().parents[1]


class EarlyReplay(Exception):
 pass


class DelayedAck(LiveZmodem):
 def __init__(self,delay):
  self.delay=delay;self.due=None;self.packet_tick=None;self.ack_tick=None
  self.idle_reads=0;self.witness=None
  body=bytes(range(256))*4
  super().__init__(sending=True,source=body)
  self.advance_ticks=False
  ready=h(1,0x23002000)
  self.script=deque([(h(0),ready),
   (h(4,0x01000000,67)+packet(send_meta('SEND.BIN',len(body)).ljust(128,b'\0'),67,107,0),h(9)),
   (h(10,0,67),b''),(packet(body,67,107,0),h(3,len(body))),
   (h(11,len(body),67),ready),(h(8),h(8)),(b'OO',b'APP')])
  self.put('terminal_baud_low',38400);self.put('terminal_baud_high',0)
  self.put('connection_state',6);self.put('terminal_directory_mode',0)

 def tick_hook(self,u,address,size,data):
  if address==self.symbols.get('terminal_clock_ticks') and not self.rx:
   self.idle_reads+=1
   if self.idle_reads%32==0:self.tick+=1
  if self.due is not None and self.tick>=self.due:
   self.rx.extend(h(3,1024));self.ack_tick=self.tick;self.due=None
  return super().tick_hook(u,address,size,data)

 def output_port(self,u,port,size,value,data):
  wire=port==self.get('uart_port_thr') and not self.lcr&128
  if wire and self.due is not None and self.script:
   attempted=bytes(self.pending)+bytes([value&255])
   if not self.script[0][0].startswith(attempted):
    self.witness=dict(packet_tick=self.packet_tick,ACK_due_tick=self.due,
     premature_output_tick=self.tick,attempted_prefix_hex=attempted.hex(),
     expected_after_ACK_hex=self.script[0][0].hex())
    raise EarlyReplay()
  current=self.script[0] if self.script else None;before=len(self.script)
  super().output_port(u,port,size,value,data)
  if current and len(self.script)<before and current[1]==h(3,1024):
   self.packet_tick=self.tick
   if self.delay:
    assert bytes(self.rx)==h(3,1024)
    self.rx.clear();self.due=self.tick+self.delay
   else:self.ack_tick=self.tick


def main():
 import check_transport
 rows=[]
 for delay in (0,182):
  m=DelayedAck(delay)
  try:
   status=m.run(owner=True)
  except EarlyReplay:
   assert delay and m.witness and m.ack_tick is None
   assert m.tick-m.packet_tick<delay
   rows.append(dict(case='ten-second-response',counterexample_reproduced=True,
    witness=m.witness,scope='Stopped by test assertion at premature wire output; no cleanup or final transfer claim.'))
  else:
   assert status==0 and not m.script and not m.pending and not m.handles
   assert bytes(m.files['SEND.BIN'])==m.source
   assert bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP'
   rows.append(dict(case='immediate-response' if not delay else 'ten-second-response',
    completed=True,ACK_delay_ticks=delay,ACK_tick=m.ack_tick))
 assert rows[0]['completed'] and rows[1].get('counterexample_reproduced'),rows
 result=dict(passed=False,counterexample_reproduced=True,cases=rows,
  binary_sha256=hashlib.sha256(check_transport.BINARY.read_bytes()).hexdigest(),
  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  scope='Linked original-free DOS sender with fixed38400 DTE and modeled ten-second ACK delivery. Peer accepts exact CRC-framed source; no product instruction/callback patched. BIOS timing model is not an audio or physical test. Current response policy remains defective.')
 out=ROOT/'build/terminal/zmodem-upload-response-counterexample.json'
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
