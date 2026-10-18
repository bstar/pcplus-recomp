#!/usr/bin/env python3
"""Execute live transport with actual linked UART/IRQ and keyboard instructions.

Only hardware boundaries (UART registers, BIOS keyboard, tick advance) are modeled.
No UART/keyboard/transport routine is replaced or skipped by this test.
"""
import collections,hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,
 UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_SP,
 UC_X86_REG_EFLAGS,UC_X86_INS_IN,UC_X86_INS_OUT)
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1]
BINARY=ROOT/'build/terminal/TERMINAL.EXE'
MAP=ROOT/'build/terminal/terminal.map'
class Transport(DosImage):
 def __init__(self,keys=()):
  super().__init__(BINARY,MAP)
  self.keys=collections.deque(keys);self.rx=collections.deque();self.tx=[]
  self.cts=True;self.thre=True;self.tick_reads=0;self.keyboard_calls=0
  self.tick=0;self.advance_ticks=True
  self.uc.hook_add(UC_HOOK_CODE,self.tick_hook)
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.uc.hook_add(UC_HOOK_INSN,self.input_port,None,1,0,UC_X86_INS_IN)
  self.uc.hook_add(UC_HOOK_INSN,self.output_port,None,1,0,UC_X86_INS_OUT)
  self.put('uart_software_flow',0);self.put('uart_hardware_flow',0)
  self.put('terminal_quit',0);self.put('terminal_exit_code',0)
 def tick_hook(self,uc,address,size,_):
  if address==self.symbols['terminal_tick_low']:
   self.tick_reads+=1
   if self.advance_ticks:self.tick=(self.tick+1)&0xffff
   uc.mem_write(0x46c,struct.pack('<H',self.tick))
 def interrupt(self,uc,number,_):
  assert number==0x16,('Unexpected BIOS/DOS output from transport',number)
  self.keyboard_calls+=1
  function=uc.reg_read(UC_X86_REG_AX)>>8
  assert function in (0,1,16,17),function
  if function in (0,16):
   assert self.keys,'Transport attempted an unsatisfied blocking keyboard read'
   uc.reg_write(UC_X86_REG_AX,self.keys.popleft())
  else:
   flags=uc.reg_read(UC_X86_REG_EFLAGS)
   uc.reg_write(UC_X86_REG_EFLAGS,(flags&~0x40) if self.keys else flags|0x40)
   if self.keys:uc.reg_write(UC_X86_REG_AX,self.keys[0])
 def input_port(self,uc,port,size,_):
  if port==self.get('uart_port_rbr'):
   assert self.rx,'UART read without supplied RX data'
   return self.rx.popleft()
  if port==self.get('uart_port_rbr')+2:return 4 if self.rx else 1
  if port==self.get('uart_port_lsr'):return (0x60 if self.thre else 0)+(1 if self.rx else 0)
  if port==self.get('uart_port_msr'):return 0x90 if self.cts else 0x80
  return 0
 def output_port(self,uc,port,size,value,_):
  if port==self.get('uart_port_thr'):self.tx.append(value&255)
 def call(self,name,arguments=(),*,ax=0,cleanup=0,irq=False,limit=200000):
  uc=self.uc
  for register,value in [(UC_X86_REG_CS,self.base_segment),(UC_X86_REG_DS,self.ds),
   (UC_X86_REG_SS,self.ds),(UC_X86_REG_ES,0xb800),(UC_X86_REG_EFLAGS,0x202),
   (UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_AX,ax)]:uc.reg_write(register,value)
  words=([0xf000,self.base_segment,0x202] if irq else [0xf000])+list(arguments)
  sp=0xe000-len(words)*2;uc.mem_write(self.data_base+sp,struct.pack('<'+'H'*len(words),*words));uc.reg_write(UC_X86_REG_SP,sp)
  self.returned=False;uc.emu_start(self.symbols[name],self.base+0x10000,count=limit)
  assert self.returned,(name,'did not finish within',limit)
  assert uc.reg_read(UC_X86_REG_SP)==sp+(6 if irq else 2)+cleanup,(name,'stack cleanup')
  if name in ('terminal_poll_io','terminal_enqueue_al','ansi_next_byte','ansi_unread_byte','csi_transmit_byte','csi_transmit_string'):
   for register,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert uc.reg_read(register)==want,(name,'ABI register preservation')
  return uc.reg_read(UC_X86_REG_AX)
 def receive_irq(self,data):
  self.rx.extend(data);self.call('uart_receive_interrupt',irq=True)
  assert not self.rx
 def enqueue(self,data):
  # Caller-owned near test buffer; distinct from live rings and artificial stack.
  assert len(data)<=2048
  pointer=0xf100;self.uc.mem_write(self.data_base+pointer,data+b'\0')
  self.call('csi_transmit_string',[pointer],cleanup=2)
 def drain(self):
  for _ in range(1030):
   if not self.get('terminal_tx_count'):return
   before=len(self.tx);self.call('terminal_poll_io');assert len(self.tx)-before<=1
  raise AssertionError('TX queue did not drain')
def main():
 cases=[]
 def check(name,operation):operation();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def receive():
  m=Transport();m.receive_irq(b'\0\x80\xff')
  assert [m.call('ansi_next_byte') for _ in range(3)]==[0,128,255]
  m.call('ansi_unread_byte');assert m.call('ansi_next_byte')==255
  assert m.get('uart_rx_count')==0 and not m.tx
 check('actual-uart-irq-to-binary-read-and-unreceive',receive)
 def tx_ring():
  m=Transport();first=bytes((i%255)+1 for i in range(600));m.enqueue(first)
  for _ in range(500):
   before=len(m.tx);m.call('terminal_poll_io');assert len(m.tx)==before+1
  second=bytes((i%255)+1 for i in range(924));m.enqueue(second)
  assert m.get('terminal_tx_count')==1024 and m.get('terminal_tx_head')==m.get('terminal_tx_tail')
  m.drain();assert bytes(m.tx)==first+second and m.get('terminal_quit')==0
  m=Transport();m.call('csi_transmit_byte',[0],cleanup=2);m.call('terminal_poll_io');assert m.tx==[0]
 check('ret2-output-abi-binary-byte-and-full-capacity-ring-wrap',tx_ring)
 def overflow():
  m=Transport();m.enqueue(b'x'*1025)
  assert m.get('terminal_tx_count')==1024 and m.get('terminal_tx_tail')==0
  assert (m.get('terminal_quit'),m.get('terminal_exit_code'))==(1,3)
  m.call('terminal_poll_io');assert not m.tx
 check('bounded-string-queue-overflow-exits-without-byte-overwrite',overflow)
 def flow():
  m=Transport();m.enqueue(b'ab');m.put('uart_hardware_flow',1);m.cts=False
  m.call('terminal_poll_io');assert not m.tx and m.get('terminal_tx_count')==2
  m.cts=True;m.call('terminal_poll_io');assert m.tx==[97]
  m.put('uart_software_flow',1);m.receive_irq(b'\x13')
  m.call('terminal_poll_io');assert m.tx==[97] and m.get('terminal_tx_count')==1
  m.receive_irq(b'\x11');m.call('terminal_poll_io');assert m.tx==[97,98]
  m=Transport();m.enqueue(b'z');m.put('uart_tx_paused',1);m.put('uart_flow_pending',0x11,1)
  m.call('terminal_poll_io');assert m.tx==[0x11] and m.get('terminal_tx_count')==1
  m.put('uart_tx_paused',0);m.call('terminal_poll_io');assert m.tx==[0x11,ord('z')]
  m=Transport();m.enqueue(b'x');m.thre=False;m.call('terminal_poll_io');assert not m.tx
  m.thre=True;m.call('terminal_poll_io');assert m.tx==[ord('x')]
 check('actual-flow-priority-CTS-XOFF-XON-and-transmitter-busy',flow)
 def keys():
  m=Transport([0x1e61,0x1c0d,0x0e08,0x011b])
  for _ in range(5):m.call('terminal_poll_io')
  assert bytes(m.tx)==b'a\r\b\x1b' and not m.keys
  for application in (False,True):
   m=Transport([0x4800,0x5000,0x4d00,0x4b00])
   if application:
    m.put('terminal_dec_keys',1);m.call('terminal_keyboard_mode',[ord('O')])
   for _ in range(4):m.call('terminal_poll_io')
   m.drain();prefix=b'O' if application else b'['
   assert bytes(m.tx)==b''.join(b'\x1b'+prefix+suffix for suffix in [b'A',b'B',b'C',b'D'])
  m=Transport([0x3b00]);m.call('terminal_poll_io');assert m.get('terminal_tx_count')==0 and not m.get('terminal_quit')
  m=Transport([0x4800]);m.uc.mem_write(m.symbols['terminal_keymap'],b'x'*12);m.call('terminal_poll_io')
  assert (m.get('terminal_quit'),m.get('terminal_exit_code'),m.get('terminal_tx_count'))==(1,4,0)
 check('actual-BIOS-ASCII-arrows-DECCKM-and-bounded-binding-validation',keys)
 def deadlines():
  for initial in (0,0xfff0):
   m=Transport();m.tick=initial
   assert m.call('ansi_next_byte')==0xffff and m.tick_reads==37
   assert not m.get('terminal_quit') and m.keyboard_calls==36
  m=Transport([0x2d00]);m.put('uart_hardware_flow',1);m.cts=False;m.enqueue(b'blocked')
  assert m.call('ansi_next_byte')==0xffff
  assert m.get('terminal_quit')==1 and m.get('terminal_exit_code')==0 and m.tick_reads==1
  assert not m.tx and not m.keys
 check('36-BIOS-tick-timeout-wrap-and-immediate-AltX-during-CTS-stall',deadlines)
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked live transport, recovered UART IRQ/foreground APIs and recovered BIOS keyboard routines. Hardware ports/BIOS keyboard/tick advances are modeled; no runtime routine is mocked. No physical modem proof.'}
 (ROOT/'build/terminal/transport-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
