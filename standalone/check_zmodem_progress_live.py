#!/usr/bin/env python3
"""Paced confirmed-prefix replay through the linked UART and progress watchdog."""
from collections import deque
import hashlib,json
from pathlib import Path
from check_zmodem import h,send_meta
from check_zmodem_wire import packet

ROOT=Path(__file__).resolve().parents[1]
def run_case(factory):
 W,Q,E=107,106,104;size=8193;body=(bytes(range(256))*33)[:size];ready=h(1,0x23000800)
 one=[(h(10,0,67),b''),(packet(body[:1024],67,W,0),h(3,1024))]
 for start in (1024,3072,5120):
  one.extend([(h(10,start,67),b''),(packet(body[start:start+1024],67,Q,0),h(3,start+1024)),(packet(body[start+1024:start+2048],67,W,0),h(3,start+2048))])
 one.extend([(h(10,7168,67),b''),(packet(body[7168:8192],67,Q,0),h(3,8192)),(packet(body[8192:],67,E,0),b'')])
 script=[(h(0),ready),(h(4,0x01000000,67)+packet(send_meta('SEND.BIN',size).ljust(128,b'\0'),67,W,0),h(9)),*one,(h(11,size,67),h(9)),*one,(h(11,size,67),ready),(h(8),h(8)),(b'OO',b'APP')]
 acks={h(3,pos) for pos in range(1024,8193,1024)}
 class Paced(factory):
  def __init__(self):
   self.replay_start=None;self.replay_clocks=[];self.refreshes=[]
   super().__init__(sending=True,source=body);self.advance_ticks=False;self.script=deque(script)
  def tick_hook(self,u,address,size,data):
   if address==self.symbols.get('terminal_transfer_accepted_progress'):
    self.refreshes.append(dict(tick=self.tick,kbytes=self.get('_terminal_zmodem_kbytes'),replay=self.replay_start is not None))
   return super().tick_hook(u,address,size,data)
  def output_port(self,u,port,size,value,data):
   before=len(self.script);current=self.script[0] if self.script else None
   super().output_port(u,port,size,value,data)
   if current and len(self.script)<before:
    want,reply=current
    if want==h(11,8193,67) and reply==h(9):self.replay_start=self.tick
    if reply in acks:
     self.tick+=100
     if self.replay_start is not None:self.replay_clocks.append(self.tick)
 m=Paced()
 try:status=m.run(owner=True)
 except AssertionError:
  if m.get('terminal_transfer_fault')!=3:raise
  status=3
 passed=status==0 and not m.script and not m.pending and not m.handles and bytes(m.files['SEND.BIN'])==body and m.get('_terminal_zmodem_files',4)==1
 row=dict(case='paced-accepted-prefix-replay',passed=passed,status=status,fault=m.get('terminal_transfer_fault'),budget=540,modeled_ticks_per_ACK=100,replay_start=m.replay_start,replay_ACK_ticks=m.replay_clocks,native_refreshes=m.refreshes,remaining_script=len(m.script),scope='Linked production engine/adapter/UART/watchdog. Only BIOS clock schedule and peer/kernel hardware modeled. Whole replay exceeds inactivity budget; each confirmed-ACK interval is below it. No physical timing claim.')
 assert passed,row
 assert m.replay_clocks[-1]-m.replay_start>=800 and all(b-a<=100 for a,b in zip([m.replay_start]+m.replay_clocks,m.replay_clocks))
 assert len([r for r in m.refreshes if r['replay'] and r['kbytes']==1])==1,row
 assert bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP'
 return row

def main():
 from check_terminal_zmodem_live import LiveZmodem
 row=run_case(LiveZmodem);out=ROOT/'build/terminal/zmodem-progress-live-checks.json'
 out.write_text(json.dumps(dict(passed=True,binary_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),case=row,test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n');print(json.dumps(row))
if __name__=='__main__':main()
