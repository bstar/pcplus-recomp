#!/usr/bin/env python3
"""Linked native upload startup with real ISR and independent banner/control peer."""
import argparse,hashlib,json
from pathlib import Path
from check_terminal_upload_live import LiveUpload,ROOT,BINARY
from check_terminal_transfer_live import DAY

class Startup(LiveUpload):
 def __init__(self,noise=b'',control=b'C',crc=True,stream=False,fault=None,schedule=()):
  self.startup_noise=noise;self.startup_control=control;self.stream_noise=stream;self.startup_fault=fault;self.injected=False;self.offered_tick=None
  self.schedule=list(schedule);self.handshake_offered=False
  super().__init__(b'STARTUP BANNER\x00\x1a\xff',crc=crc)
 def interrupt(self,u,n,d):
  offered=self.initial_offered;super().interrupt(u,n,d)
  if not offered and self.initial_offered:
   assert self.rx[-1]==(67 if self.crc_mode else 21)
   self.rx.pop();self.rx.extend(self.startup_noise+self.startup_control);self.offered_tick=self.tick
   self.handshake_offered=bool(self.startup_control)
 def tick_hook(self,u,address,size,data):
  super().tick_hook(u,address,size,data)
  if self.offered_tick is None or self.tx:return
  if address not in (self.symbols.get('terminal_clock_ticks'),self.symbols.get('terminal_tick_low')):return
  while self.schedule and (self.tick-self.offered_tick)%DAY>=self.schedule[0][0]:
   _,wire,handshake=self.schedule.pop(0);self.rx.extend(wire)
   self.handshake_offered|=handshake
  if self.stream_noise and not self.rx:self.rx.append(ord('t'))
  if self.startup_fault and not self.injected and (self.tick-self.offered_tick)%DAY>=6:
   self.injected=True
   if self.startup_fault=='escape':self.keys.append(0x011b)
   elif self.startup_fault=='altx':self.keys.append(0x2d00)
   elif self.startup_fault=='carrier':self.carrier=False
   elif self.startup_fault=='overflow':self.rx.extend(b't'*4097)
 def output_port(self,u,port,size,value,data):
  if port==self.get('uart_port_thr') and not self.lcr&0x80 and value&255 in (1,2,4):
   assert self.handshake_offered,'Sender transmitted before independent receiver handshake'
  super().output_port(u,port,size,value,data)

def main():
 global BINARY
 canonical=ROOT/'build/terminal/terminal-upload-startup.json'
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=canonical);p.add_argument('--baseline',action='store_true');p.add_argument('--binary',type=Path);a=p.parse_args()
 if a.binary:
  import check_transport
  BINARY=a.binary.resolve();assert BINARY.is_relative_to(ROOT/'build')
  check_transport.BINARY=BINARY;check_transport.MAP=BINARY.parent/'terminal.map'
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and (out==canonical or not out.exists())
 assert not a.baseline or out!=canonical
 cases=[]
 def run(label,model,want=0,initial=0):
  error=None;model.tick=initial;assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest
  try:
   model.upload();fault=model.get('terminal_transfer_fault')
   checks=dict(expected_fault=fault==want,source_closed=not model.handles,source_unchanged=bytes(model.files['SEND.BIN'])==model.source,
    exact_completion=(model.accepted==len(model.frames)==model.eots==1) if want==0 else not model.tx)
   if model.stream_noise and not model.startup_fault:checks['whole_owner_noise_deadline']=540<=(model.tick-initial)%DAY<650
   if model.startup_fault:checks['real_fault_injected']=model.injected
   if 'terminal_upload_startup_ansi' in model.symbols:checks['ANSI_state_retired']=model.get('terminal_upload_startup_ansi')==0
  except Exception as e:error=repr(e);checks=dict(completed=False);fault=model.get('terminal_transfer_fault')
  cases.append(dict(label=label,passed=all(checks.values()),checks=checks,error=error,fault=fault,physical_TX_bytes=len(model.tx),initial_tick=initial,elapsed_ticks=(model.tick-initial)%DAY))
 banners=[('plain',b'\r\nStart XMODEM-1K/CRC transfer now (Ctrl-X to abort):\r\n'),
  ('ANSI_cursor',b'\x1b[35mWaiting for Upload\x1b[5C\x1b[3G\x1b[0m\r\n'),
  ('OSC_string',b'\x1b]0;Upload C G W U\x07\r\n'),
  ('DCS_string',b'\x1bPbanner C G W U\x1b\\\r\n'),
  ('charset',b'\x1b(G\r\nUpload Waiting CRC\r\n')]
 for crc in (True,False):
  run('quiet_CRC' if crc else 'quiet_checksum',Startup(control=b'C' if crc else b'\x15',crc=crc))
  for label,noise in banners:run(label+('_CRC' if crc else '_checksum'),Startup(noise,control=b'C' if crc else b'\x15',crc=crc))
 run('quiet_G_selects_nonstreaming_CRC',Startup(control=b'G'))
 for control in (b'U',b'W'):run('quiet_'+control.decode()+'_explicit_unsupported',Startup(control=control),want=10)
 run('peer_CAN_pair',Startup(b'waiting\r\n',b'\x18\x18'),want=2)
 if not a.baseline:
  run('peer_CAN_inside_incomplete_CSI',Startup(b'\x1b[31',b'\x18\x18'),want=2)
  m=Startup(b'\x1b]unfinished',b'');run('unclosed_OSC_times_out',m,want=3)
  assert not m.rx and not m.get('uart_rx_count')
  m.startup_noise=b'';m.startup_control=b'C';m.initial_offered=False;m.offered_tick=None;m.handshake_offered=False;m.filename_sent=False
  run('same_instance_after_unclosed_OSC',m,initial=m.tick)
 for initial in (() if a.baseline else (0,0xfff0,DAY-20)):
  run('banner_across_clock_boundary',Startup(banners[0][1]),initial=initial)
  run('CSI_across_read_timeouts',Startup(b'\x1b[',b'',schedule=[(24,b'5C',False),(60,b'\r\nC',True)]),initial=initial)
  run('OSC_across_read_timeouts',Startup(b'\x1b]0;C',b'',schedule=[(24,b'G W U\x1b\\',False),(60,b'C',True)]),initial=initial)
  run('continuous_noise_deadline',Startup(control=b'',stream=True),want=3,initial=initial)
  for why,want in [('escape',2),('altx',2),('carrier',4),('overflow',5)]:
   run(why+'_during_noise',Startup(control=b'',stream=True,fault=why),want=want,initial=initial)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest
 product_files=['src/terminal/upload_actions.asm','src/terminal/transfer_actions.asm','src/terminal/upload_startup.asm','src/terminal/upload_startup_bridge.asm','reconstruction/transfer_send/session.asm','reconstruction/transfer_send/cancel.asm']
 product_inputs={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in product_files} if not a.baseline else {}
 result=dict(passed=all(c['passed'] for c in cases),binary_sha256=digest,cases=cases,product_inputs=product_inputs,
  inputs={str(q.relative_to(ROOT)):hashlib.sha256(q.read_bytes()).hexdigest() for q in [Path(__file__).resolve(),ROOT/'standalone/check_terminal_upload_live.py',ROOT/'standalone/check_terminal_transfer_live.py']},
  scope='Actual linked source-built native sender, maintained adapters, real UART ISR and read-only file owner. Only BIOS/UART/ticks and DOS syscalls modeled. Independent peer supplies banner/ANSI/CRC/checksum/control bytes; no product callback is patched. Quiet controls, supported CRC/checksum, unsupported U/W, peer CAN, continuous noise/deadline and physical/carrier/local cancellation across clock boundaries are distinct gates. Not actual DOS/audio/physical acceptance.')
 with out.open('w' if out==canonical else 'x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=result['passed'],cases=len(cases),failed=[c['label'] for c in cases if not c['passed']],output=str(out))))
 assert not result['passed'] if a.baseline else result['passed']

if __name__=='__main__':main()
