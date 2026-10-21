#!/usr/bin/env python3
"""Buffered modem sender timing through the linked production DOS program."""
import argparse,hashlib,json
from collections import deque
from pathlib import Path
from check_terminal_zmodem_live import LiveZmodem
from check_zmodem import h,send_meta
from check_zmodem_wire import packet

ROOT=Path(__file__).resolve().parents[1]
DAY=0x1800b0


class PrematureReply(Exception):
 pass


class BufferedReply(LiveZmodem):
 def __init__(self,delay,*,window=False,phase='data',direct=False,connected=True,
              stopwait=False,interrupt=None,noise=False,initial=0):
  self.delay=delay;self.wait_start=None;self.delivered=None;self.witness=None
  self.fault_tick=None
  self.interrupt_kind=interrupt;self.injected=False;self.noise=noise;self.noise_bytes=0
  self.deferred=None;self.phase=phase
  body=b'\x18'*(9216 if window else 1024)
  super().__init__(sending=True,source=body)
  if noise:
   # IRQ injection before an instruction resumes at that same instruction
   # after IRET. Require actual foreground instructions between FIFO bursts,
   # otherwise an endlessly reinjected byte can starve the modeled CPU.
   self.respect_rts=True;self.put('uart_hardware_flow',1)
  self.advance_ticks=False;self.tick=initial
  ready=h(1,0x22000000 if stopwait else 0x23002000)
  self.held_reply=h(9) if phase=='offer' else ready if phase=='EOF' else h(3,len(body))
  self.script=deque([(h(0),ready),
   (h(4,0x01000000,67)+packet(send_meta('SEND.BIN',len(body)).ljust(128,b'\0'),67,107,0),h(9)),
   (h(10,0,67),b''),(packet(body[:1024],67,107,0),h(3,1024))])
  if window:
   self.script.append((h(10,1024,67),b''))
   # Hold all advisory quarter-window ACKs, then ACK the full8KiB credit.
   for i,end in enumerate((105,106,105,106,105,106,105,107)):
    off=1024+i*1024
    self.script.append((packet(body[off:off+1024],67,end,0),h(3,len(body)) if end==107 else b''))
  self.script.extend([(h(11,len(body),67),ready),(h(8),h(8)),(b'OO',b'APP')])
  self.held_output=self.script[1][0] if phase=='offer' else h(11,len(body),67) if phase=='EOF' else packet(body[-1024:],67,107,0)
  self.put('terminal_baud_low',38400);self.put('terminal_baud_high',0)
  self.put('connection_state',6 if connected else 0)
  self.put('terminal_directory_mode',1 if direct else 0)

 def tick_hook(self,u,address,size,data):
  if address==self.symbols.get('terminal_clock_ticks') and self.get('terminal_transfer_fault') and self.fault_tick is None:
   self.fault_tick=self.tick
  # Model reply latency after DTE handoff, then normal cleanup time.
  # Freeze output execution time: a fast-DTE burst must not itself consume
  # the slow-carrier wait being tested. Every product instruction runs.
  if address==self.symbols.get('terminal_clock_ticks') and not self.rx and (self.deferred is not None or self.get('terminal_transfer_fault')):
   self.tick=(self.tick+1)%DAY
  if self.deferred is not None:
   elapsed=(self.tick-self.wait_start)%DAY
   if self.interrupt_kind and not self.injected and elapsed>=182:
    self.injected=True;self.deferred=None;self.script_enabled=False;self.strict=False
    if self.interrupt_kind=='escape':self.keys.append(0x011b)
    else:self.carrier=False
   elif self.delay is not None and elapsed>=self.delay:
    self.rx.extend(self.deferred);self.deferred=None;self.delivered=self.tick
   elif self.noise and not self.rx and address==self.symbols.get('terminal_clock_ticks'):
    self.rx.append(ord('?'));self.noise_bytes+=1
  return super().tick_hook(u,address,size,data)

 def output_port(self,u,port,size,value,data):
  wire=port==self.get('uart_port_thr') and not self.lcr&128
  # Do not admit replay before a delayed valid reply. Silence/noise cases
  # instead run the native retry, timeout and cleanup paths to completion.
  if wire and self.deferred is not None and self.delay is not None and self.script:
   attempted=bytes(self.pending)+bytes([value&255])
   if not self.script[0][0].startswith(attempted):
    self.witness=dict(wait_start_tick=self.wait_start,ACK_delay_ticks=self.delay,
     premature_elapsed_ticks=(self.tick-self.wait_start)%DAY,attempted_prefix_hex=attempted.hex())
    raise PrematureReply()
  current=self.script[0] if self.script else None;before=len(self.script)
  super().output_port(u,port,size,value,data)
  if current and len(self.script)<before and current==(self.held_output,self.held_reply) and self.wait_start is None:
   self.wait_start=self.tick
   if self.delay==0:self.delivered=self.tick
   else:
    assert bytes(self.rx)==self.held_reply
    self.rx.clear();self.deferred=self.held_reply
    if self.delay is None:self.strict=False


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--counterexample',action='store_true');a=p.parse_args()
 import check_transport
 helpers=None
 if a.counterexample:
  check_transport.BINARY=ROOT/'build/terminal/upload-response-baseline/TERMINAL.EXE'
  check_transport.MAP=ROOT/'build/terminal/upload-response-baseline/terminal.map'
 else:
  from omf_imports import rename_imports
  before=(ROOT/'build/terminal/zmodem-compiler.obj').read_bytes()
  after=(ROOT/'build/terminal/zmodem.obj').read_bytes()
  names={'__U4D':'config_u4div_service_','__U4M':'config_u4mul_service_'}
  normalized,counts=rename_imports(before,names)
  assert normalized==after and counts=={'__U4D':1,'__U4M':1}
  restored,_=rename_imports(after,{v:k for k,v in names.items()});assert restored==before
  helpers=dict(import_counts=counts,compiler_object_sha256=hashlib.sha256(before).hexdigest(),
   normalized_object_sha256=hashlib.sha256(after).hexdigest(),exact_OMF_roundtrip=True)
 cases=[('immediate',0,{}),('ten-second-data-ACK',182,{})]
 if not a.counterexample:
  cases += [('metadata-reply',200,{'phase':'offer'}),('EOF-reply',100,{'phase':'EOF'}),
   ('stopwait-reply',182,{'stopwait':True}),('over-thirty-second-read',1092,{}),
   ('fully-quoted8KiB-at300bps',10000,{'window':True}),
   ('midnight',182,{'initial':DAY-80}),('direct-policy-unchanged',182,{'direct':True}),
   ('disconnected-policy-unchanged',182,{'connected':False}),
   ('silent-peer',None,{}),('noise-without-accepted-progress',None,{'noise':True}),
   ('escape-during-extended-wait',None,{'interrupt':'escape'}),
   ('carrier-loss-during-extended-wait',None,{'interrupt':'carrier'})]
 rows=[]
 for name,delay,kw in cases:
  m=BufferedReply(delay,**kw);early=False
  try:status=m.run(owner=True)
  except PrematureReply:
   assert (a.counterexample and delay) or kw.get('direct') or kw.get('connected') is False,(name,m.witness)
   assert m.delivered is None and m.witness['premature_elapsed_ticks']<delay
   early=True;status=None
  else:
   assert not (a.counterexample and delay) and not kw.get('direct') and kw.get('connected') is not False
   wanted=2 if kw.get('interrupt')=='escape' else 4 if kw.get('interrupt')=='carrier' else 3 if delay is None else 0
   assert status==wanted,(name,status,m.get('terminal_transfer_fault'),m.tick)
   assert not m.handles and not m.get('terminal_transfer_pending') and not m.get('terminal_transfer_active')
   assert {k:bytes(v) for k,v in m.files.items()}=={'SEND.BIN':m.source}
   assert m.get('terminal_transfer_cleanup_status')==0
   if not status:
    assert not m.script and not m.pending and m.get('_terminal_zmodem_files',4)==1
    assert bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP'
   else:
    assert m.get('_terminal_zmodem_files',4)==0
    elapsed=(m.tick-m.wait_start)%DAY
    # The watchdog is independent of the bounded18-byte cancel writer and
    #180-tick drain. Include their existing per-byte36-tick limits and a
    #64-query allowance for this deliberately accelerated clock model.
    assert elapsed<17280+18*36+180+64,(name,elapsed)
    if kw.get('interrupt'):assert m.injected and elapsed<220
    if kw.get('noise'):
     assert m.noise_bytes>100 and 17280<=(m.fault_tick-m.wait_start)%DAY<=17282
     assert m.get('terminal_quit')==1 and m.get('terminal_exit_code')==14
  row=dict(case=name,status=status,expected_early_replay=early,witness=m.witness,
   wait_start=m.wait_start,reply_delivered=m.delivered,final_tick=m.tick,
   delay_ticks=delay,noise_bytes=m.noise_bytes,
   first_fault_tick=m.fault_tick,
   scope='Assertion stops expected premature-output cases; only completed native runs prove cleanup.')
  rows.append(row);print(name,'passed',flush=True)
 source_base=ROOT/'build/terminal/upload-response-baseline' if a.counterexample else ROOT
 source_names=['zmodem.c','zmodem.h','terminal_zmodem.c','ymodem_actions.asm'] if a.counterexample else ['src/transfer/zmodem.c','src/transfer/zmodem.h','src/transfer/terminal_zmodem.c','src/terminal/ymodem_actions.asm']
 result=dict(passed=not a.counterexample,counterexample_reproduced=a.counterexample,cases=rows,
  compiler_helpers=helpers,
  binary_sha256=hashlib.sha256(check_transport.BINARY.read_bytes()).hexdigest(),
  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  source_sha256={str((source_base/n).relative_to(ROOT)):hashlib.sha256((source_base/n).read_bytes()).hexdigest() for n in source_names},
  scope='Actual linked DOS engine/adapter/file owner/watchdog/UART ISR with modeled BIOS clock, serial peer and DOS kernel. Fixed38400 DTE; no instruction/callback replacement. Immediate, delayed, quoted full-window, direct, cancellation, loss and no-progress bounds. Not an actual audio, BBS or physical acceptance.')
 out=ROOT/'build/terminal'/('zmodem-upload-response-counterexample-recheck.json' if a.counterexample else 'zmodem-upload-response-checks.json')
 out.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
