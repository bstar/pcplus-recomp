#!/usr/bin/env python3
"""Verify fixed-DTE/slow-carrier deadlines in the linked receiver.

No product callback is replaced. UART/BIOS/DOS are modeled by LiveZmodem;
delivered wire bytes advance the modeled clock at 1200 bps, 8N1. This is a
retained counterexample with --counterexample, or the corrected modem policy.
"""
import argparse,hashlib,json
from pathlib import Path
from check_terminal_zmodem_live import LiveZmodem

ROOT=Path(__file__).resolve().parents[1]


class SlowCarrier(LiveZmodem):
 def __init__(self,dte,*,direct=False,body=None,block=4096,carrier=1200):
  self.wire_bytes=0;self.idle_ticks=0;self.idle_polls=0;self.carrier_bps=carrier
  super().__init__(source=bytes(range(256))*16 if body is None else body,receive_block=block)
  self.advance_ticks=False;self.respect_rts=True;self.wire_bytes=0
  self.put('uart_hardware_flow',1)
  self.put('terminal_baud_low',dte);self.put('terminal_baud_high',0)
  self.put('connection_state',6);self.put('terminal_directory_mode',1 if direct else 0)
  self.strict=False

 def tick_hook(self,u,address,size,data):
  if address==self.symbols.get('terminal_clock_ticks') and not self.rx:
   self.idle_polls+=1
   if self.idle_polls%32==0:self.idle_ticks+=1
  self.tick=self.wire_bytes*10*1193182//(self.carrier_bps*65536)+self.idle_ticks
  return super().tick_hook(u,address,size,data)

 def input_port(self,u,port,size,data):
  delivered=(port==self.get('uart_port_rbr') and not self.lcr&128
             and self.rx and self.mcr&2 and self.fifo_left)
  value=super().input_port(u,port,size,data)
  if delivered:
   self.wire_bytes+=1
   # Exact BIOS frequency 1193182/65536, ten serial bits per octet.
   self.tick=self.wire_bytes*10*1193182//(self.carrier_bps*65536)+self.idle_ticks
  return value


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--counterexample',action='store_true');a=parser.parse_args()
 import check_transport
 if a.counterexample:
  check_transport.BINARY=ROOT/'build/terminal/carrier-deadline-baseline/TERMINAL.EXE'
  check_transport.MAP=ROOT/'build/terminal/carrier-deadline-baseline/terminal.map'
 rows=[]
 for dte in (38400,1200):
  m=SlowCarrier(dte);fault=m.run(owner=True)
  installed=m.files.get('D:\\RECV\\ONE.BIN')
  rows.append(dict(DTE_bps=dte,modeled_carrier_bps=1200,
   deadline_ticks=m.get('transfer_progress_budget'),fault=fault,
   installed_exact=installed is not None and bytes(installed)==m.source,
   delivered_wire_bytes=m.wire_bytes,elapsed_ticks=m.tick,
   handles_closed=not m.handles,remaining_peer_steps=len(m.script)))
 assert rows[0]['fault']==(3 if a.counterexample else 0) and rows[0]['installed_exact']!=a.counterexample,rows
 assert rows[1]['fault']==0 and rows[1]['installed_exact'] and not rows[1]['remaining_peer_steps'],rows
 if not a.counterexample:
  # A modem can deliver a maximally quoted8KiB packet before any CRC confirms
  # progress. Test the supported300bps floor, independent of fixed38400 DTE.
  m=SlowCarrier(38400,body=b'\x18'*8192,block=8192,carrier=300);assert m.run(owner=True)==0
  assert bytes(m.files['D:\\RECV\\ONE.BIN'])==m.source and not m.handles and not m.script
  rows.append(dict(case='fully-quoted8KiB-before-first-confirmed-progress',passed=True,modeled_carrier_bps=300,wire_bytes=m.wire_bytes,elapsed_ticks=m.tick))
  for direct in (False,True):
   for protocol in (0,1,2):
    m=SlowCarrier(38400,direct=direct);m.put('terminal_transfer_protocol',protocol);m.call('terminal_transfer_set_budget')
    assert m.get('transfer_progress_budget')==(540 if direct else 17280 if protocol==2 else 2160)
  # A peer that disappears after metadata still expires through ordinary
  # protocol idle reads/retries, well before the slow-packet outer ceiling.
  m=SlowCarrier(38400);want,_=m.script[1];m.script[1]=(want,b'')
  assert m.run(owner=True)==3 and not m.handles
  assert 'D:\\RECV\\ONE.BIN' not in m.files and m.tick<17280
  rows.append(dict(case='direct-budget-preserved-and-peer-silence-bounded',passed=True,elapsed_ticks=m.tick))
 result=dict(counterexample_reproduced=a.counterexample,passed=not a.counterexample,cases=rows,
  binary_sha256=hashlib.sha256(check_transport.BINARY.read_bytes()).hexdigest(),
  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  scope='Linked production receiver, watchdog, UART ISR and storage. Hardware/kernel boundaries modeled. Quantized1200/300-bps wire time plus idle clock, not audio or physical acceptance. Fixed DTE remains unchanged; unknown modem carrier uses bounded300bps packet allowance, direct sessions retain UART allowance. Historical failure retained separately.')
 out=ROOT/'build/terminal'/('carrier-transfer-deadline-counterexample.json' if a.counterexample else 'carrier-transfer-deadline-checks.json')
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
