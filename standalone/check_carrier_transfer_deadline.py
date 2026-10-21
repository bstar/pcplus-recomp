#!/usr/bin/env python3
"""Characterize fixed-DTE/slow-carrier deadlines in the linked receiver.

No product callback is replaced. UART/BIOS/DOS are modeled by LiveZmodem;
delivered wire bytes advance the modeled clock at 1200 bps, 8N1. This is a
retained counterexample, not acceptance of the current deadline policy.
"""
import hashlib,json
from pathlib import Path
from check_terminal_zmodem_live import LiveZmodem

ROOT=Path(__file__).resolve().parents[1]


class SlowCarrier(LiveZmodem):
 def __init__(self,dte):
  self.wire_bytes=0;self.idle_ticks=0;self.idle_polls=0
  super().__init__(source=bytes(range(256))*16,receive_block=4096)
  self.advance_ticks=False;self.respect_rts=True;self.wire_bytes=0
  self.put('uart_hardware_flow',1)
  self.put('terminal_baud_low',dte);self.put('terminal_baud_high',0)
  self.strict=False

 def tick_hook(self,u,address,size,data):
  if address==self.symbols.get('terminal_clock_ticks') and not self.rx:
   self.idle_polls+=1
   if self.idle_polls%32==0:self.idle_ticks+=1
  self.tick=self.wire_bytes*10*1193182//(1200*65536)+self.idle_ticks
  return super().tick_hook(u,address,size,data)

 def input_port(self,u,port,size,data):
  delivered=(port==self.get('uart_port_rbr') and not self.lcr&128
             and self.rx and self.mcr&2 and self.fifo_left)
  value=super().input_port(u,port,size,data)
  if delivered:
   self.wire_bytes+=1
   # Exact BIOS frequency 1193182/65536, ten serial bits per octet.
   self.tick=self.wire_bytes*10*1193182//(1200*65536)+self.idle_ticks
  return value


def main():
 rows=[]
 for dte in (38400,1200):
  m=SlowCarrier(dte);fault=m.run(owner=True)
  installed=m.files.get('D:\\RECV\\ONE.BIN')
  rows.append(dict(DTE_bps=dte,modeled_carrier_bps=1200,
   deadline_ticks=m.get('transfer_progress_budget'),fault=fault,
   installed_exact=installed is not None and bytes(installed)==m.source,
   delivered_wire_bytes=m.wire_bytes,elapsed_ticks=m.tick,
   handles_closed=not m.handles,remaining_peer_steps=len(m.script)))
 assert rows[0]['fault']==3 and not rows[0]['installed_exact'],rows
 assert rows[1]['fault']==0 and rows[1]['installed_exact'] and not rows[1]['remaining_peer_steps'],rows
 result=dict(counterexample_reproduced=True,cases=rows,
  binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),
  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  scope='Linked production receiver, watchdog, UART ISR and storage. Hardware/kernel boundaries modeled. Quantized 1200-bps wire time, not an audio or physical test. High fixed DTE falsely expires before a valid 4KiB carrier packet completes; matched DTE succeeds. Product remains unfixed.')
 out=ROOT/'build/terminal/carrier-transfer-deadline-counterexample.json'
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
