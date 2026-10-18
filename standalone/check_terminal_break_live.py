#!/usr/bin/env python3
"""Actual linked BREAK/transport/IRQ/API; model UART registers, BIOS and ticks only."""
import hashlib,json,struct
from unicorn.x86_const import *
from check_meta_actions_live import Meta,ROOT,BINARY,DAY
from terminal_config_fixtures import BASES
class Break(Meta):
 def __init__(self,*,port=1,line=3):
  super().__init__();self.lcr=line;self.temt=True;self.lcr_writes=[]
  self.put('hardware_active',1,1);self.put('vector_active',1,1)
  for name,delta in [('rbr',0),('thr',0),('ier',1),('lcr',3),('mcr',4),('lsr',5),('msr',6)]:self.put('uart_port_'+name,BASES[port-1]+delta)
 def input_port(self,u,port,size,data):
  if port==self.get('uart_port_lcr'):return self.lcr
  if port==self.get('uart_port_lsr'):return (0x20 if self.thre else 0)|(0x40 if self.temt else 0)|(1 if self.rx else 0)
  return super().input_port(u,port,size,data)
 def output_port(self,u,port,size,value,data):
  if port==self.get('uart_port_lcr'):
   self.lcr=value&255;self.lcr_writes.append((port,value&255,self.tick));return
  if port==self.get('uart_port_thr'):assert not self.get('uart_break_hold') and not self.lcr&0x40,'THR write during owned BREAK'
  return super().output_port(u,port,size,value,data)
 def pulse(self,units=350):self.put('terminal_break_delay_units',units);self.call('terminal_break_start')
 def state(self):return self.get('terminal_break_state')
 def status(self):return self.get('terminal_break_status')
 def service(self,tick):self.tick=tick%DAY;self.call('terminal_break_poll')
 def key(self,key):self.keys.append(key);self.call('terminal_poll_io')

def main():
 groups=[]
 def check(name,fn):
  count=fn();groups.append(dict(case=name,inputs=count,passed=True));print(name,'PASS',count,flush=True)
 def abi():
  registers={UC_X86_REG_AX:0x4444,UC_X86_REG_BX:0x1111,UC_X86_REG_CX:0x2222,UC_X86_REG_DX:0x3333,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678,UC_X86_REG_ES:0xb800}
  for entry in ('terminal_break_start','terminal_break_poll','terminal_break_cancel'):
   m=Break();m.pulse()
   for reg,value in registers.items():m.uc.reg_write(reg,value)
   m.call(entry,ax=0x4444)
   for reg,value in registers.items():assert m.uc.reg_read(reg)==value,(entry,reg)
   assert m.uc.reg_read(UC_X86_REG_EFLAGS)&0xffff==0x202
  return 3
 check('public-register-FLAGS-IF-and-near-stack-ABI',abi)
 def ports():
  for port in range(1,5):
   for line in (0,3,7,0x1b,0x3f):
    for initial in (0,0xfffc,DAY-4):
     m=Break(port=port,line=line);m.tick=initial;m.pulse()
     assert m.state()==2 and m.lcr==line|0x40 and not m.tx
     assert m.get('uart_break_hold')==1
     for delta in range(8):m.service(initial+delta);assert m.state()==2 and m.lcr==line|0x40
     m.service(initial+8);assert m.state()==0 and m.status()==6 and m.lcr==line and not m.tx
     assert len(m.lcr_writes)==2 and all(w[0]==BASES[port-1]+3 for w in m.lcr_writes)
  return 60
 check('four-configured-ports-five-framings-default-duration-lowword-midnight',ports)
 def units():
  for units in (0,1,54,55,56,350,65535):
   m=Break();m.pulse(units)
   if not units:assert m.state()==0 and m.status()==6 and [v for p,v,t in m.lcr_writes]==[0x43,3]
   else:
    duration=(units+54)//55+1;m.service(duration-1);assert m.state()==2;m.service(duration);assert m.state()==0
   assert not m.tx
  m=Break();m.temt=False;m.pulse(350);m.put('terminal_break_delay_units',0);m.temt=True;m.service(1)
  assert m.state()==2;m.service(8);assert m.state()==2;m.service(9);assert m.state()==0
  return 8
 check('full-word-delay-domain-zero-immediate-and-duration-snapshot',units)
 def drain():
  for initial in (0,0xfffa,DAY-5):
   m=Break();m.tick=initial;m.temt=False;m.pulse();assert m.state()==1 and not m.lcr_writes
   m.put('uart_flow_pending',0x13,1);m.enqueue(b'QUEUED')
   for delta in (0,1,18):m.tick=(initial+delta)%DAY;m.call('terminal_poll_serial');assert m.state()==1 and not m.tx
   m.service(initial+19);assert m.state()==0 and m.status()==5 and not m.lcr_writes
  m=Break();m.temt=False;m.pulse();m.service(18);m.temt=True;m.service(19)
  assert m.state()==2;m.service(26);assert m.state()==2;m.service(27);assert m.state()==0 and m.status()==6
  return 4
 check('THRE-is-insufficient-TEMT-drain-deadline-and-fresh-pulse-clock',drain)
 def flow_rx():
  m=Break();m.pulse();m.put('uart_hardware_flow',1);m.cts=False
  m.receive_irq(bytes(range(256))*5);assert m.get('uart_rx_count')==1280
  for byte in bytes(range(256))*5:assert m.call('uart_receive_byte')==byte
  m.put('uart_software_flow',1);m.receive_irq(b'X'*3074)
  assert m.get('uart_rx_count')==3074 and m.get('uart_flow_pending',1)==0x13
  m.enqueue(b'REPLY');m.call('terminal_poll_serial');assert not m.tx and m.get('uart_flow_pending',1)==0x13
  for _ in range(3074):assert m.call('uart_receive_byte')==ord('X')
  assert m.get('uart_rx_count')==0 and m.get('uart_flow_pending',1)==0x11
  m.key(0x1e61);m.call('terminal_poll_serial');assert not m.tx and m.get('terminal_tx_count')==6
  m.service(8);m.call('terminal_poll_serial');assert m.tx==[0x11] and not m.get('uart_flow_pending',1)
  m.cts=True;m.drain();assert bytes(m.tx)==b'\x11REPLYa'
  return 1280+3074+2
 check('real-IRQ-binary-RX-watermarks-flow-and-keyboard-queue-while-all-TX-held',flow_rx)
 def gates():
  for name in ('terminal_macro_active','terminal_program_pending','terminal_program_active','terminal_transfer_pending','terminal_transfer_active','terminal_ansi_wait_active'):
   m=Break();m.put(name,1);m.pulse();assert not m.state() and m.status()==2 and not m.lcr_writes and not m.tx
  for state in (1,2,5,7,8,9):
   m=Break();m.put('connection_state',state);m.pulse();assert not m.state() and m.status()==2 and not m.lcr_writes
  for name in ('hardware_active','vector_active'):
   m=Break();m.put(name,0,1);m.pulse();assert not m.state() and m.status()==4 and not m.lcr_writes
  for line in (0x43,0x83,0xc3):
   m=Break(line=line);m.pulse();m.call('terminal_break_cancel');assert not m.state() and m.status()==3 and m.lcr==line and not m.lcr_writes
  for controller in (0,1):
   m=Break();m.put('terminal_controller_active',controller);m.key(0x3000);assert m.state()==2 and not m.get('terminal_quit')
  m=Break();m.put('terminal_monitor_active',1);m.key(0x3000);assert m.state()==2
  for controller in (2,3):
   m=Break();m.put('terminal_controller_active',controller);m.pulse();assert not m.state() and not m.lcr_writes
  m=Break();m.pulse();m.service(4);m.pulse();assert m.state()==2 and len(m.lcr_writes)==1;m.service(8);assert not m.state()
  m=Break();m.pulse();m.record(0,b'UNSENT');assert m.start()==4 and not m.get('terminal_macro_active')
  pointer=m.stage_near(b'ECHO CHILD\0');assert m.call('terminal_program_start',ax=pointer)==2 and not m.get('terminal_program_pending')
  for command in ('terminal_transfer_start','terminal_upload_start'):m.call(command);assert not m.get('terminal_transfer_pending')
  return 27
 check('owner-admission-foreign-LCR-real-AltB-normal-raw-monitor-repeat-and-handoff',gates)
 def cancel():
  for draining in (False,True):
   for name in ('terminal_break_cancel','terminal_connection_cancel','terminal_connection_exit','terminal_connection_start'):
    m=Break();m.temt=not draining;m.pulse();m.call(name,ax=1)
    assert not m.state() and not m.get('uart_break_hold') and not m.lcr&0x40 and not m.tx
    before=list(m.lcr_writes);m.call('terminal_break_cancel');assert m.lcr_writes==before
   for key in (0x2d00,0x2300,0x2000):
    m=Break();m.temt=not draining;m.pulse();m.key(key);assert not m.state() and not m.lcr&0x40
  m=Break();m.put('connection_enabled',1,1);m.put('connection_state',6);m.call('terminal_connection_poll');m.pulse();m.carrier=False;m.call('terminal_poll_serial')
  assert not m.state() and not m.lcr&0x40 and m.get('connection_state')==0
  for flag in ('terminal_quit','connection_state'):
   m=Break();m.pulse();m.put(flag,1);m.call('terminal_break_poll');assert not m.state() and m.status()==7 and not m.lcr&0x40
  m=Break();m.pulse();m.lcr=0x5b;m.call('terminal_break_poll');assert m.status()==8 and m.lcr==0x1b
  m=Break();m.temt=False;m.pulse();m.lcr|=0x40;m.call('terminal_break_poll');assert not m.state() and m.status()==3 and m.lcr==0x43 and not m.lcr_writes
  return 19
 check('cancel-exit-hangup-redial-carrier-and-LCR-changes-no-stale-restore',cancel)
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),groups=groups,inputs=sum(g['inputs'] for g in groups),scope='Actual linked serviced BREAK owner, BIOS key route, recovered UART ISR and maintained TX/flow APIs. Only registers/BIOS clock/keyboard modeled; no replaced runtime callbacks, fake THR byte, physical serial BREAK timing or modem acknowledgement claim.')
 (ROOT/'build/terminal/break-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
