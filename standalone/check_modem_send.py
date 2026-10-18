#!/usr/bin/env python3
"""Actual sender, expansion, delays and UART instructions; modeled hardware only."""
import hashlib,json,struct,sys
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_INTR,UC_HOOK_INSN,UC_HOOK_MEM_READ
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_SP,UC_X86_REG_EFLAGS,UC_X86_REG_ES,UC_X86_INS_IN,UC_X86_INS_OUT
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/config'))
from prm import modem_command_events,expand_modem_command
BINARY=ROOT/'build/modem-send/MODEMSND.EXE'
class Send(DosImage):
 def __init__(self):
  super().__init__(BINARY,BINARY.parent/'modem_send.map');self.tx=[];self.echo=[];self.delay=[];self.pause=[];self.events=[];self.bios_changes=0;self.loop_iterations=0;self.tick=0;self.thre=True;self.cts=True;self.lsr_reads=0;self.escape=False;self.keyboard_checks=0;self.advance_ticks=True
  self.uc.hook_add(UC_HOOK_CODE,self.hook);self.uc.hook_add(UC_HOOK_INTR,self.interrupt);self.uc.hook_add(UC_HOOK_MEM_READ,self.read_tick,begin=0x46c,end=0x46d)
  self.uc.hook_add(UC_HOOK_INSN,self.input_port,None,1,0,UC_X86_INS_IN);self.uc.hook_add(UC_HOOK_INSN,self.output_port,None,1,0,UC_X86_INS_OUT)
 def read_tick(self,u,access,address,size,value,_):
  if self.advance_ticks:self.tick=(self.tick+1)&65535
  u.mem_write(0x46c,struct.pack('<H',self.tick))
 def hook(self,u,address,size,_):
  if address in (self.symbols['modem_send_delay_calibrated'],self.symbols['modem_send_delay_bios']):
   arg=struct.unpack('<H',u.mem_read(self.data_base+u.reg_read(UC_X86_REG_SP)+2,2))[0]
   if address==self.symbols['modem_send_delay_calibrated']:self.delay.append(arg);self.events.append(('character_delay_units',arg))
   else:self.pause.append(arg);self.events.append(('pause_bios_tick_changes',(arg+1)&65535))
  if address==self.symbols['modem_send_delay_bios']+0x16:self.bios_changes+=1
  if address==self.symbols['modem_send_delay_calibrated']+0x15:self.loop_iterations+=1
 def interrupt(self,u,number,_):
  if number==0x16:
   self.keyboard_checks+=1;function=u.reg_read(UC_X86_REG_AX)>>8
   if function==1:
    flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,(flags&~64) if self.escape else flags|64);u.reg_write(UC_X86_REG_AX,27 if self.escape else 0)
   else:assert function==0 and self.escape;self.escape=False;u.reg_write(UC_X86_REG_AX,27)
   return
  assert number==0x10,('unexpected BIOS/DOS/presentation boundary',number)
  ax=u.reg_read(UC_X86_REG_AX);assert ax>>8==0x0e;self.echo.append(ax&255)
 def input_port(self,u,port,size,_):
  if port==self.get('uart_port_lsr'):self.lsr_reads+=1;return 0x60 if self.thre else 0
  if port==self.get('uart_port_msr'):return 0x10 if self.cts else 0
  return 0
 def output_port(self,u,port,size,value,_):
  assert port==self.get('uart_port_thr'),('unexpected port output',port,value)
  self.tx.append(value&255);self.events.append(('transmit',value&255))
 def send(self,command,pause=126,pacing=2,echo=1):
  expand_modem_command(command) # Declared safe test input; raw sender has no bounds checks.
  source=0x7000;self.uc.mem_write(self.data_base+source,command+b'\0');self.put('modem_send_pause_marker',pause,1);self.put('modem_send_pacing_units',pacing);self.put('modem_send_local_echo',echo)
  self.call('modem_send_original',[source],limit=500000)

def main():
 cases=[]
 def check(name,fn):n=fn();cases.append({'case':name,'inputs':n,'passed':True});print(name,'passed',n)
 def semantics():
  inputs=[(b'AT~X^@^M^^^',126),(b'^@',255),(b'A^`B',126),(b'^^',126),(b'',126),(b'~^^^~',126),(b'^MZ',13)]
  for command,marker in inputs:
   s=Send();s.send(command,marker);expected=modem_command_events(command,marker,2)
   assert tuple(s.events)==expected,(command,s.events,expected)
   assert s.bios_changes==10*len(s.pause) and all(x==9 for x in s.pause)
   assert s.loop_iterations==sum(s.delay),(s.loop_iterations,s.delay)
  return len(inputs)
 check('actual-uart-byte-order-sentinel-pause-priority-and-calibrated-delay',semantics)
 def echo():
  for enabled in (0,1):
   s=Send();s.send(b'AT~^@^M',echo=enabled)
   assert bytes(s.tx)==b'AT\0\r' and bytes(s.echo)==(b'AT\r' if enabled else b'')
  return 2
 check('local-echo-only-ordinary-bytes-not-pause-or-sentinel',echo)
 def controls():
  n=0
  for value in range(1,256):
   if value==94:continue
   s=Send();command=b'^'+bytes([value]);s.send(command,pause=126,pacing=0,echo=0)
   assert tuple(s.events)==modem_command_events(command,126,0);n+=1
  return n
 check('all-caret-control-values-through-recovered-expander-and-real-uart',controls)
 def clocks():
  s=Send();s.tick=65530;s.send(b'~',pacing=0,echo=0);assert s.bios_changes==10
  s=Send();s.put('modem_send_delay_count',4);s.put('modem_send_delay_floor',1);s.send(b'X',pacing=2,echo=0);assert s.loop_iterations==6 and s.uc.reg_read(UC_X86_REG_ES)==s.ds
  s=Send();s.send(b'X',pacing=0,echo=0);assert s.loop_iterations==0
  return 3
 check('actual-bios-tick-wrap-and-explicit-calibration-loop-counts',clocks)
 def blocked():
  s=Send();s.thre=False
  try:s.send(b'X',pacing=0,echo=0)
  except AssertionError as error:assert 'failed to return within' in str(error)
  else:raise AssertionError('raw original sender unexpectedly has a THRE timeout')
  assert not s.tx and s.lsr_reads>1000
  return 1
 check('original-transmitter-not-ready-remains-blocking',blocked)
 def cancellation():
  s=Send();s.cts=False;s.escape=True;s.put('uart_hardware_flow',1);s.send(b'X',pacing=0,echo=0)
  assert bytes(s.tx)==b'X' and s.keyboard_checks==2 # Escape bypasses CTS wait, not sending.
  s=Send();s.escape=True;s.send(b'~',pacing=0,echo=0);assert s.bios_changes==10 and s.keyboard_checks==0
  s=Send();s.escape=True;s.advance_ticks=False
  try:s.send(b'~',pacing=0,echo=0)
  except AssertionError as error:assert 'failed to return within' in str(error)
  else:raise AssertionError('original BIOS pause unexpectedly has a stalled-clock deadline')
  assert not s.tx and s.keyboard_checks==0
  return 3
 check('cts-escape-bypasses-wait-and-pause-has-no-cancel-or-stalled-clock-deadline',cancellation)

 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual recovered sender+expansion+delays+UART instructions with port/BIOS echo/tick hardware modeled. No UART routine or delay routine skipped; original echo renderer replaced by explicit diagnostic BIOS service.'};(BINARY.parent/'cpu-results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
