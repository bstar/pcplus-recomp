#!/usr/bin/env python3
"""Real linked connection/sender/decoder/UART instructions; hardware modeled only."""
import hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_ES,UC_X86_REG_EFLAGS
from dos_image import DosImage
from check_transport import Transport
from terminal_config_fixtures import image,RATES
ROOT=Path(__file__).resolve().parents[1]

from modem_fixtures import fixture

class Connection(Transport):
 def __init__(self,**settings):
  super().__init__();self.advance_ticks=False;self.carrier=True;self.mcr=0xb;self.lcr=3;self.controls=[]
  self.put('uart_hardware_flow',1)
  payload=fixture(**settings);pointer=self.offset('screen_attribute_cells')
  self.uc.mem_write(self.data_base+pointer,payload);self.uc.reg_write(UC_X86_REG_ES,self.ds)
  assert DosImage.call(self,'_modem_import_decode',[pointer,self.offset('terminal_modem_settings')])==0
  self.put('terminal_option_mask',48)
  self.uc.mem_write(self.symbols['terminal_dial_target'],b'Local.Example:2323\0')
  assert self.call('terminal_connection_prepare')==0 and not self.flags()
  assert not self.tx and not self.controls
 def flags(self):return self.uc.reg_read(UC_X86_REG_EFLAGS)&1
 def tick_hook(self,uc,address,size,data):
  if address in (self.symbols['terminal_tick_low'],self.symbols['terminal_clock_ticks']):
   self.tick_reads+=1
   if self.advance_ticks:self.tick=(self.tick+1)%0x1800b0
   uc.mem_write(0x46c,struct.pack('<I',self.tick))
 def input_port(self,uc,port,size,data):
  if port==self.get('uart_port_msr'):return (0x80 if self.carrier else 0)|(0x10 if self.cts else 0)
  if port==self.get('uart_port_mcr'):return self.mcr
  if port==self.get('uart_port_lcr'):return self.lcr
  return super().input_port(uc,port,size,data)
 def output_port(self,uc,port,size,value,data):
  if port==self.get('uart_port_lcr'):self.lcr=value;return
  if port==self.get('uart_port_mcr'):self.mcr=value;self.controls.append(value);return
  if port==self.get('uart_port_thr') and self.lcr&0x80:return
  super().output_port(uc,port,size,value,data)
 def poll(self,count=1):
  for _ in range(count):self.tick=(self.tick+1)%0x1800b0;self.call('terminal_poll_io')
 def state(self):return self.get('connection_state')
 def start(self):self.call('terminal_connection_start')
 def waiting(self):
  for _ in range(500):
   if self.state()==5:return
   self.poll()
  raise AssertionError(('No response wait',self.state(),bytes(self.tx)))
 def receive(self,data):
  self.receive_irq(data)
  while self.get('uart_rx_count'):
   value=self.call('uart_receive_byte');self.call('terminal_connection_receive',ax=value)
 def connect(self,response=b'CONNECT'):
  self.start();self.waiting();self.receive(response);self.poll();assert self.state()==6

def main():
 cases=[]
 def check(name,fn):count=fn();cases.append({'case':name,'passed':True,'inputs':count});print(name,'passed',count,flush=True)
 def commands():
  m=Connection();m.start();m.waiting()
  assert bytes(m.tx)==b'ATZ\rATDLocal.Example:2323\r'
  assert m.get('connection_deadline',4)==55 and m.get('terminal_tx_count')==0
  m.receive(b'noise CONNE');assert m.get('connection_result')==65535
  m.receive(b'CT');m.poll();assert m.state()==6 and m.get('connection_status')==1
  m.poll();m.carrier=False;m.poll();assert m.state()==0 and m.get('connection_status')==6
  m=Connection(initialize=0);m.start();m.waiting();assert bytes(m.tx)==b'ATDLocal.Example:2323\r'
  return 2
 check('actual-port-command-wire-partial-connect-and-DCD-transition',commands)
 def failures():
  for response in (b'BUSY',b'NO CARRIER',b'VOICE',b'TIMEOUT'):
   m=Connection();m.start();m.waiting();m.receive(response);m.poll(25)
   assert m.state()==0 and m.get('connection_status')==2 and m.controls==[10,11]
  m=Connection();m.start();m.poll(90);assert m.state()==0 and m.get('connection_status')==3
  m=Connection();m.cts=False;m.start();m.poll(100)
  assert m.state()==0 and m.get('connection_status')==3 and not m.tx and m.controls==[10,11]
  return 6
 check('four-failure-responses-timeout-and-CTS-stalled-bounded-cleanup',failures)
 def cancellation():
  for state in ('initialization','waiting','online','hangup'):
   m=Connection();m.start()
   if state!='initialization':m.waiting()
   if state in ('online','hangup'):m.receive(b'CONNECT');m.poll()
   if state=='hangup':m.keys.append(0x2300);m.poll();assert m.state()==9
   m.cts=False;m.keys.append(0x2d00);m.poll(40)
   assert m.state()==0 and m.get('terminal_quit')==1 and m.controls==[10,11],state
  m=Connection();m.start();m.cts=False;m.keys.append(0x011b);m.poll(40)
  assert m.state()==0 and m.get('connection_status')==4 and not m.get('terminal_quit')
  m.keys.append(0x2000);m.cts=True;m.poll();assert m.state()==1
  m=Connection(timeout=1);m.cts=False;m.start();m.keys.append(0x011b);m.poll()
  m.tick+=30;m.poll();assert m.state()==8
  m.poll(20);assert m.state()==0
  m=Connection();m.cts=False;m.start();m.keys.append(0x2d00);m.call('terminal_poll_io')
  assert m.state()==7 and not m.get('terminal_quit')
  for _ in range(10):m.call('terminal_poll_io')
  m.keys.append(0x2d00);m.call('terminal_poll_io');assert m.get('terminal_quit')==1
  return 8
 check('actual-BIOS-Escape-AltX-AltH-AltD-through-stalled-sender-and-hangup',cancellation)
 def autobaud():
  labels=[b'CONNECT',b'CON1200',b'CON2400',b'CON4800',b'CON9600',b'CON19200',b'CON38400']
  for auto in (0,1):
   for i,label in enumerate(labels):
    m=Connection(autobaud=auto);m.connect(label)
    rate=m.get('terminal_baud_low')+65536*m.get('terminal_baud_high')
    assert rate==(RATES[i] if auto else 38400),(auto,i,rate)
  m=Connection(autobaud=1);m.connect(b'CONNECT');assert m.get('connection_baud_index')==0
  m.call('terminal_connection_cancel',ax=1);m.poll(50);assert m.state()==0
  m.start();m.waiting();m.receive(b'CON38400');m.poll()
  assert m.state()==6 and m.get('terminal_baud_low')==38400 and m.get('connection_baud_index')==6
  return 15
 check('original-response-autobaud-policy-and-actual-UART-divisor-setter',autobaud)
 def queue():
  m=Connection();m.enqueue(b'OLD');m.start();assert m.get('terminal_tx_count')==0
  m.enqueue(b'FOREIGN');m.poll(3);assert b'FOREIGN' not in bytes(m.tx)
  m=Connection();m.cts=False;m.start();m.poll(3);assert not m.tx
  m.cts=True;m.poll(3);assert bytes(m.tx)==b'ATZ'
  m=Connection();m.put('uart_software_flow',1);m.start();m.receive_irq(b'\x13');m.poll(3);assert not m.tx
  m.receive_irq(b'\x11');m.poll(3);assert bytes(m.tx)==b'ATZ'
  return 4
 check('TX-ownership-and-real-recovered-XOFF-CTS-backpressure',queue)
 def sender_rules():
  for pause,text,wanted in ((ord('~'),b'AT~X^@^M^^^',b'ATX\x00\r^'),(255,b'^@X^M',b'X\r'),(ord('~'),b'AB^`IGNORED',b'AB')):
   m=Connection();at=m.symbols['terminal_modem_settings'];m.uc.mem_write(at+18,text+b'\0');m.uc.mem_write(at+14,struct.pack('<H',pause))
   assert m.call('terminal_connection_prepare')==0
   m.start();m.waiting();assert bytes(m.tx)==wanted+b'ATDLocal.Example:2323\r'
  m=Connection();m.thre=False;m.start();m.poll(100)
  assert not m.tx and m.state()==0 and m.get('connection_status')==3
  return 4
 check('live-pause-sentinel-expanded-zero-and-THRE-deadline',sender_rules)
 def ticks():
  for seconds in (1,3,60,3600,32767):
   m=Connection(timeout=seconds);m.tick=65530;m.start()
   assert m.get('connection_deadline',4)==(seconds*1193182+65535)//65536
   m.poll(10);assert m.get('connection_elapsed',4)==10
  m=Connection();m.tick=0x1800b0-5;m.start();m.poll(10)
  assert m.get('connection_elapsed',4)==10 and m.state()!=7
  return 6
 check('full-32bit-PIT-derived-deadlines-and-low-tick-wrap',ticks)
 def ui_and_parser():
  m=Connection();pattern=bytes(i%256 for i in range(4000));m.uc.mem_write(0xb8000,pattern)
  names=('screen_cursor_row','screen_cursor_column','attributes_current','csi_saved_row','csi_saved_column')
  logical={name:m.get(name) for name in names}
  m.start();video=bytes(m.uc.mem_read(0xb8000,4000))
  assert video[:3840]==pattern[:3840] and video[3870:]==pattern[3870:]
  assert video[3842:3866:2]==b'Initializing'
  m.receive_irq(b'OK');assert m.call('ansi_next_byte')==65535 and m.get('uart_rx_count')==2
  m.waiting();m.receive(b'CONNECT');m.poll();assert m.state()==6
  assert bytes(m.uc.mem_read(0xb8000,4000))==pattern
  assert {name:m.get(name) for name in names}==logical
  return 1
 check('notice-exact-cell-restore-and-partial-parser-yields-modem-RX',ui_and_parser)
 result={'passed':True,'binary_sha256':hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),'cases':cases,'scope':'Actual linked connection state machine, decoder, expansion, matcher, keyboard and UART instructions; only port/BIOS clock/keyboard hardware boundaries modeled. Live main/RX/postmatch behavior additionally needs real DOS tests.'}
 (ROOT/'build/terminal/connection-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
