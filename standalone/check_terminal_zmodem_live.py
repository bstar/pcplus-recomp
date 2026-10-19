#!/usr/bin/env python3
"""Linked ZMODEM adapter/engine, real UART ISR and checked file owners.
Only BIOS/UART/ticks and DOS kernel boundaries are modeled; peer wire is Python.
"""
import hashlib,json,struct
from collections import deque
from pathlib import Path
from unicorn.x86_const import *
from check_terminal_ymodem_live import LiveYmodem
from check_terminal_transfer_live import LiveTransfer,ROOT,BINARY
from check_zmodem import h,meta,offer,payload
from check_zmodem_wire import packet
from zmodem_window_vectors import vectors
from check_zmodem_progress_live import run_case as progress_case

class LiveZmodem(LiveYmodem):
 def __init__(self,*,sending=False,source=b'ABC\0\x1a\xff@\r',fault=None,fmt=67,resume=0,receive_block=1024):
  self.script=deque();self.pending=bytearray();self.script_enabled=False;self.respect_rts=False;self.fifo_left=0;self.foreground_gap=0
  super().__init__(sending=sending,source=source,fault=fault,peer=False)
  self.initial_offered=True;self.put('terminal_transfer_protocol',2);self.script_enabled=True;self.strict=fault is None
  self.filename=b'SEND.BIN' if sending else b'D:\\RECV\\'
  if sending:
   self.script.append((h(0),h(1,0x22000000 if fmt==67 else 0x02000000)))
   self.script.append((h(4,0x01000000,fmt)+packet(meta('SEND.BIN',len(source)).ljust(128,b'\0'),fmt,107,0),h(9,resume)))
   for off in range(resume,len(source),1024):self.script.append((payload(source[off:off+1024],off,fmt),h(3,min(off+1024,len(source)))))
   self.script.append((h(11,len(source),fmt),h(1,0x22000000 if fmt==67 else 0x02000000)))
   self.script.append((h(8),h(8)));self.script.append((b'OO',b'APP'))
  else:
   self.script.append((h(1,0x23000000),offer('ONE.BIN',len(source)+123,fmt)))
   reply=payload(source[:receive_block],0,fmt) if source else h(11,0,fmt)
   self.script.append((h(9),reply))
   for off in range(0,len(source),receive_block):
    nextoff=min(off+receive_block,len(source));reply=payload(source[nextoff:nextoff+receive_block],nextoff,fmt) if nextoff<len(source) else h(11,len(source),fmt)
    self.script.append((h(3,nextoff),reply))
   self.script.append((h(1,0x23000000),h(8)));self.script.append((h(8),b'OOAPP'))
 def tick_hook(self,u,address,size,data):
  # Physical HARD-flow peer honors the actual driver's RTS output. No product
  # instruction/return is skipped; BIOS clock scaling is separately declared.
  if self.respect_rts:
   # Model bounded hardware FIFO bursts and foreground execution between IRQs.
   # An infinite FIFO delivered in one ISR can incorrectly refill3072 bytes
   # between RTS's OUT and the following lowered-flag clear (three instructions).
   if not self.irq_in_service and u.reg_read(UC_X86_REG_EFLAGS)&0x200:self.foreground_gap+=1
   deliver=bool(self.mcr&2 and not self.irq_in_service and self.foreground_gap>=8)
   if deliver:self.fifo_left=16;self.foreground_gap=0
  else:deliver=True
  if not deliver:
   pending=self.rx;self.rx=deque()
   try:super().tick_hook(u,address,size,data)
   finally:self.rx=pending
  else:super().tick_hook(u,address,size,data)
 def input_port(self,u,port,size,data):
  if self.respect_rts and (not self.mcr&2 or not self.fifo_left) and not self.lcr&0x80:
   # Pending peer bytes are not an infinitely deep hardware FIFO. Once RTS
   # drops, this modeled peer stops delivery; the ISR may drain its real ring.
   pending=self.rx;self.rx=deque()
   try:return super().input_port(u,port,size,data)
   finally:self.rx=pending
  value=super().input_port(u,port,size,data)
  if self.respect_rts and port==self.get('uart_port_rbr') and not self.lcr&0x80:self.fifo_left-=1
  return value
 def interrupt(self,u,n,data):
  ax=u.reg_read(UC_X86_REG_AX)
  if n==0x21 and ax==0x4200 and self.direction:
   at=(u.reg_read(UC_X86_REG_CX)<<16)|u.reg_read(UC_X86_REG_DX)
   assert at<=len(self.source)
   error=5 if self.upload_fault=='seek' else 0
   if not error:self.position=at
   u.reg_write(UC_X86_REG_AX,error or (at&65535));u.reg_write(UC_X86_REG_DX,at>>16);self.set_carry(bool(error))
   self.fs_calls.append(dict(ah=0x42,error=error,count=at,tx_bytes=len(self.tx)));return
  return super().interrupt(u,n,data)
 def output_port(self,u,port,size,value,data):
  wire=port==self.get('uart_port_thr') and not self.lcr&0x80
  LiveTransfer.output_port(self,u,port,size,value,data)
  if not wire or not self.script_enabled:return
  self.pending.append(value&255)
  if not self.script:
   assert not self.strict,('Unexpected final wire',bytes(self.pending));return
  want,reply=self.script[0]
  if not want.startswith(self.pending):
   if self.strict:raise AssertionError(('Independent wire mismatch',len(self.script),bytes(self.pending),want))
   self.script_enabled=False;return
  if len(self.pending)==len(want):
   self.script.popleft();self.pending.clear()
   if not self.direction and not self.script and self.strict:
    assert bytes(self.files['D:\\RECV\\ONE.BIN'])==self.source,'ZFIN before checked install'
   self.rx.extend(reply)
 def run(self,owner=False):
  if owner:
   self.waiting_ui=True;self.call('terminal_upload_start' if self.direction else 'terminal_transfer_start')
   self.call('terminal_transfer_poll',limit=100000000);result=self.get('terminal_transfer_fault')
   assert not self.get('terminal_transfer_pending') and not self.get('terminal_transfer_active')
  else:
   self.uc.mem_write(self.symbols['terminal_transfer_filename'],self.filename+b'\0')
   result=self.call('_terminal_zmodem_store',[int(self.direction)],limit=100000000)
  return result

def main():
 cases=[];digest=hashlib.sha256(BINARY.read_bytes()).hexdigest()
 for sending in (False,True):
  for fmt in (65,67):
   for size in (0,1,1023,1024,1025,65539):
    source=(bytes(range(256))*257)[:size]
    m=LiveZmodem(sending=sending,source=source,fmt=fmt)
    assert m.run()==0,(sending,fmt,size,m.get('terminal_transfer_fault'),len(m.script))
    assert not m.script and not m.pending and not m.handles and m.get('_terminal_zmodem_files',4)==1
    assert bytes(m.files['SEND.BIN' if sending else 'D:\\RECV\\ONE.BIN'])==source
    assert bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP'
    cases.append(dict(case=f'bridge-{sending}-{fmt}-{size}',passed=True))
  m=LiveZmodem(sending=sending);assert m.run(owner=True)==0 and not m.script
  assert b'complete' in bytes(m.uc.mem_read(0xb8000,4000))[::2]
  cases.append(dict(case=f'foreground-owner-{sending}',passed=True))
 for offset in (0,3,8):
  m=LiveZmodem(sending=True,resume=offset);assert m.run()==0 and not m.script and not m.handles
  cases.append(dict(case=f'checked-source-resume-{offset}',passed=True))
 for sending,faults in ((False,('write','short','close','install')),(True,('open','seek','read','short','close'))):
  for fault in faults:
   m=LiveZmodem(sending=sending,fault=fault);assert m.run()==1
   assert m.get('terminal_transfer_fault')==7,(sending,fault,m.get('terminal_transfer_fault'))
   assert 'D:\\RECV\\ONE.BIN' not in m.files
   if fault=='close':assert m.get('terminal_transfer_cleanup_status')==1
   else:assert not m.handles
   cases.append(dict(case=f'file-fault-{sending}-{fault}',passed=True))
 for fmt in (65,67):
  for n in (2048,4096,8192,16385):
   source=(bytes(range(256))*65)[:n];m=LiveZmodem(source=source,fmt=fmt,receive_block=8192)
   m.advance_ticks=False;m.respect_rts=True;m.put('uart_hardware_flow',1)
   assert m.run()==0 and not m.script and not m.handles and bytes(m.files['D:\\RECV\\ONE.BIN'])==source
   cases.append(dict(case=f'ZedZap-HARD-CRC-{fmt}-length-{n}',passed=True,clock='Frozen BIOS ticks isolate packet memory/RTS behavior; separate real DOS tests use actual BIOS time.'))
 for fmt in (65,67):
  for v in vectors(fmt,'SEND.BIN'):
   m=LiveZmodem(sending=True,source=v['body'],fmt=fmt);m.script=deque(v['script']);m.script[-1]=(b'OO',b'APP')
   assert m.run()==0 and not m.script and not m.pending and not m.handles
   assert bytes(m.files['SEND.BIN'])==v['body'] and m.get('_terminal_zmodem_files',4)==1
   assert bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP'
   cases.append(dict(case=f'windowed-{fmt}-'+v['label'],passed=True))
 cases.append(progress_case(LiveZmodem))
 for protocol in (0,1,2):
  for baud in (300,600,1200,2400,4800,9600,19200,115200):
   m=LiveZmodem();m.put('terminal_transfer_protocol',protocol);m.put('terminal_baud_low',baud&65535);m.put('terminal_baud_high',baud>>16)
   m.call('terminal_transfer_set_budget')
   seconds=30 if baud>=9600 else 60 if baud>=4800 else 120 if baud>=2400 else 240 if baud>=1200 else 480 if baud>=600 else 960
   expected=seconds*18 if protocol==2 else 540 if baud>=1200 else 2160
   assert m.get('transfer_progress_budget')==expected
   cases.append(dict(case=f'accepted-progress-budget-{protocol}-{baud}',passed=True))
 m=LiveZmodem();m.script[-1]=(h(8),b'');assert m.run(owner=True)==0
 assert b'RX files saved; finish unconfirmed' in bytes(m.uc.mem_read(0xb8000,4000))[::2]
 assert bytes(m.files['D:\\RECV\\ONE.BIN'])==m.source and not m.handles
 cases.append(dict(case='saved-receive-with-missing-OO-honest-footer',passed=True))
 result=dict(passed=True,binary_sha256=digest,inputs=len(cases),cases=cases,
  test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  scope='Actual linked CONFIG_CODE engine/codec/far callback table, checked batch storage/source seek, serviced physical UART ISR and foreground owner. Independent exact Python wire scripts; only hardware/BIOS/DOS kernel boundaries modeled. Not actual DOS/BBS or physical modem evidence.')
 (ROOT/'build/terminal/terminal-zmodem-live-checks.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Passed',len(cases),'linked ZMODEM workflows',digest)
if __name__=='__main__':main()
