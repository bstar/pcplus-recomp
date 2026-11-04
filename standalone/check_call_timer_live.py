#!/usr/bin/env python3
"""Linked original call timer/adapters and real connection transitions; DOS/BIOS/UART modeled."""
import argparse, datetime, hashlib, json, struct
from pathlib import Path
from unicorn.x86_const import *
import check_transport as transport
from check_recording_ui_live import UI
from check_connection import Connection
from dos_image import DosImage
from modem_fixtures import fixture

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
transport.BINARY=a.terminal.resolve();transport.MAP=a.terminal.parent/'terminal.map'
manifest=json.loads((a.terminal.parent/'manifest.json').read_text());assert manifest['experimental_call_timer']
out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)

class Clock(UI):
 def __init__(self,logging=False,**settings):
  self.now=0;self.time_reads=0;self.carrier=True;self.mcr=0xb;self.lcr=3;self.controls=[]
  super().__init__();self.advance_ticks=False
  self.put('uart_hardware_flow',1)
  pointer=self.offset('screen_attribute_cells');self.uc.mem_write(self.data_base+pointer,fixture(**settings))
  self.uc.reg_write(UC_X86_REG_ES,self.ds)
  assert DosImage.call(self,'_modem_import_decode',[pointer,self.offset('terminal_modem_settings')])==0
  self.put('terminal_option_mask',48)
  self.uc.mem_write(self.symbols['terminal_dial_target'],b'Local.Example:2323\0')
  assert self.far('_phone_log_queue_initialize_far')==0
  path=self.stage_near(b'C:\\PCPLUS.FON\0') if logging else 0
  assert self.far('_phone_log_queue_configure_far',[int(logging),path])==0
  assert self.call('terminal_connection_prepare')==0
 def far(self,name,args=(),preserve=False):
  seg,offset=self.entries[name];u=self.uc
  regs={UC_X86_REG_AX:0x1234,UC_X86_REG_BX:0x2345,UC_X86_REG_CX:0x3456,UC_X86_REG_DX:0x4567,
        UC_X86_REG_SI:0x5678,UC_X86_REG_DI:0x6789,UC_X86_REG_BP:0xbabe,UC_X86_REG_ES:0xb800}
  sp=self.offset('terminal_stack_top')-2*(len(args)+2)
  u.mem_write(self.data_base+sp,struct.pack('<'+'H'*(len(args)+2),self.return_offset,self.code_segment,*args))
  for r,v in {**regs,UC_X86_REG_CS:self.base_segment+seg,UC_X86_REG_DS:self.ds,UC_X86_REG_SS:self.ds,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:0x246}.items():u.reg_write(r,v)
  self.returned=False;u.emu_start(self.symbols[name],0,count=1000000)
  assert self.returned and u.reg_read(UC_X86_REG_SP)==sp+4
  assert u.reg_read(UC_X86_REG_DS)==u.reg_read(UC_X86_REG_SS)==self.ds
  if preserve:
   assert all(u.reg_read(r)==v for r,v in regs.items()) and u.reg_read(UC_X86_REG_EFLAGS)==0x246
  return u.reg_read(UC_X86_REG_AX)
 def timer(self,operation):return self.far('terminal_call_timer_'+operation+'_far',preserve=True)
 def duration(self):return bytes(self.uc.mem_read(self.symbols['elapsed_duration'],9)).split(b'\0')[0].decode()
 def interrupt(self,u,n,d):
  ah=u.reg_read(UC_X86_REG_AX)>>8
  if n==0x21 and ah==0x2c:
   self.time_reads+=1;t=self.now%86400
   u.reg_write(UC_X86_REG_CX,(t//3600)<<8|t//60%60);u.reg_write(UC_X86_REG_DX,(t%60)<<8|99);return
  if n==0x21 and ah==0x2a:
   date=datetime.date(2026,11,3)+datetime.timedelta(days=self.now//86400)
   u.reg_write(UC_X86_REG_CX,date.year);u.reg_write(UC_X86_REG_DX,date.month<<8|date.day);u.reg_write(UC_X86_REG_AX,0x2a02);return
  super().interrupt(u,n,d)
 def tick_hook(self,u,address,size,d):
  if address in (self.symbols['terminal_tick_low'],self.symbols['terminal_clock_ticks']):
   self.tick_reads+=1
   if self.advance_ticks:self.tick=(self.tick+1)%0x1800b0
   u.mem_write(0x46c,struct.pack('<I',self.tick))
 def input_port(self,u,port,size,d):
  if port==self.get('uart_port_msr'):return (0x80 if self.carrier else 0)|(0x10 if self.cts else 0)
  if port==self.get('uart_port_mcr'):return self.mcr
  if port==self.get('uart_port_lcr'):return self.lcr
  return super().input_port(u,port,size,d)
 def output_port(self,u,port,size,value,d):
  if port==self.get('uart_port_lcr'):self.lcr=value;return
  if port==self.get('uart_port_mcr'):self.mcr=value;self.controls.append(value);return
  if port==self.get('uart_port_thr') and self.lcr&0x80:return
  super().output_port(u,port,size,value,d)
 state=Connection.state;start=Connection.start;waiting=Connection.waiting;receive=Connection.receive;connect=Connection.connect;poll=Connection.poll

cases=[]
def check(name,fn):fn();cases.append(dict(case=name,passed=True));print(name,'PASS',flush=True)
def lifecycle(logging):
 m=Clock(logging);assert m.duration()=='00:00:00' and not m.get('terminal_call_timer_valid')
 m.timer('refresh');m.timer('stop');assert not m.time_reads
 m.now=86395;m.connect(b'CONNECT\r\n');assert m.state()==6 and m.get('terminal_call_timer_running')==1 and m.get('terminal_call_timer_epoch')==1
 anchor=m.get('elapsed_start_seconds',4);assert anchor==86395
 m.now=86403;m.timer('refresh');assert m.duration()=='00:00:08'
 before=m.time_reads;m.timer('start');assert m.time_reads==before and m.get('elapsed_start_seconds',4)==anchor
 m.carrier=False;m.poll(8);assert m.state()==0 and not m.get('terminal_call_timer_running') and m.duration()=='00:00:08'
 m.now=86410;m.timer('refresh');m.timer('stop');assert m.duration()=='00:00:08'
 m.carrier=True;m.start();m.waiting();m.receive(b'BUSY\r\n');m.poll(100)
 assert not m.get('terminal_call_timer_running') and m.duration()=='00:00:08' and m.get('terminal_call_timer_epoch')==1
 m.now=86420;m.connect(b'CONNECT\r\n');m.now=86422;m.timer('refresh');assert m.duration()=='00:00:02' and m.get('terminal_call_timer_epoch')==2
 m.carrier=False;m.poll(8);assert m.state()==0 and m.duration()=='00:00:02'
check('modem-midnight-loss-BUSY-redial-logging-disabled',lambda:lifecycle(False))
check('modem-midnight-loss-BUSY-redial-logging-enabled',lambda:lifecycle(True))
def direct():
 m=Clock();m.put('terminal_directory_mode',1);m.now=100;m.start();assert m.state()==6 and m.get('terminal_call_timer_running')
 m.now=125;m.call('terminal_connection_cancel',ax=1);assert m.state()==0 and m.duration()=='00:00:25' and not m.get('terminal_call_timer_running')
check('direct-confirmed-start-and-direct-hangup-freeze',direct)
def clock_boundaries():
 m=Clock()
 for start,now in [(0,0),(65535,65536),(3600,3599),(86399,0),(32767,32768),(0,86399)]:
  m.now=start;m.timer('start');m.now=now;m.timer('refresh')
  delta=(now-start)%86400;assert m.duration()=='%02d:%02d:%02d'%(delta//3600,delta//60%60,delta%60)
  m.timer('stop');before=m.duration();reads=m.time_reads;m.now=now+100;m.timer('refresh');assert m.duration()==before and reads==m.time_reads
check('actual-linked-adapters-rollback-carry-and-idempotent-freeze',clock_boundaries)
def failed_attempts():
 m=Clock();m.now=100;m.connect(b'CONNECT\r\n');m.now=105;m.carrier=False;m.poll(8)
 assert m.state()==0 and m.duration()=='00:00:05'
 reads=m.time_reads;m.carrier=True;m.now=110;m.start();m.waiting();m.poll(1000)
 assert m.state()==0 and m.duration()=='00:00:05' and m.time_reads==reads
 m.start();m.waiting();m.call('terminal_connection_cancel',ax=0);m.poll(1000)
 assert m.state()==0 and m.duration()=='00:00:05' and m.time_reads==reads
 assert m.get('terminal_call_timer_epoch')==1 and m.get('elapsed_start_seconds',4)==100
check('timeout-and-cancel-before-CONNECT-preserve-last-call',failed_attempts)
def failed_hangup():
 m=Clock(drop=0);m.now=10;m.connect(b'CONNECT\r\n');m.now=20;m.thre=False;m.cts=False;m.call('terminal_connection_cancel',ax=1)
 for _ in range(1000):
  if m.state()==6:break
  m.poll()
 assert m.state()==6 and m.get('connection_status')==8 and m.get('terminal_call_timer_running')
 m.now=30;m.timer('refresh');assert m.duration()=='00:00:20'
 m.carrier=False;m.poll(8);assert m.state()==0 and m.duration()=='00:00:20' and not m.get('terminal_call_timer_running')
check('failed-online-hangup-retains-clock-until-qualified-carrier-loss',failed_hangup)
result=dict(passed=True,cases=cases,binary_sha256=hashlib.sha256(a.terminal.read_bytes()).hexdigest(),sources={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in [Path(__file__).resolve(),ROOT/'src/terminal/call_timer.asm',ROOT/'src/terminal/connection.asm']},scope=__doc__+' Actual linked220 recovered bytes plus real DOS-time adapter, narrow division/formatter and confirmed connection callbacks. Kernel time/date, BIOS, UART/PIC and filesystem boundaries modeled. No Alt-T view, actual DOS/SIP/analog/physical acceptance or deployment.')
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS live call timer:',len(cases),'groups')
