#!/usr/bin/env python3
"""Execute actual child lease/parser/ISR/ASIO publication; model DOS/IO only."""
import hashlib,json,struct
from pathlib import Path
import check_uart as uart
from unicorn.x86_const import *
ROOT=uart.ROOT;OUT=ROOT/'build/aspect-serial'
uart.BINARY=OUT/'SERIAL.EXE';uart.MAP=OUT/'serial.map'
class Serial(uart.Machine):
 def __init__(self):
  super().__init__();self.uc.mem_write(0x400,struct.pack('<4H',0x3f8,0x2f8,0x3e8,0x2e8));self.tick=0;self.port_base=0x3f8;self.physical_writes=[];self.vectors[11]=(0x4321,0xf000)
  self.child_psp=0x8000;self.parent_psp=0xff0;self.target=0x19000
  self.uc.mem_write(self.child_psp*16+0x16,struct.pack('<H',self.parent_psp))
  self.uc.mem_write((self.parent_psp-1)*16,b'M'+struct.pack('<HH',self.parent_psp,0x2000))
  self.argument=self.symbols['_aspect_serial_test_buffer']-self.data_base
  self.initial=(dict(self.registers),list(self.divisor),dict(self.vectors))
 def _interrupt(self,u,n,d):
  if n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x62:u.reg_write(UC_X86_REG_BX,self.child_psp);return
  return super()._interrupt(u,n,d)
 def _code(self,u,a,s,d):
  super()._code(u,a,s,d)
  if a==self.symbols['_aspect_serial_ticks']:
   self.tick+=1;self.uc.mem_write(0x46c,struct.pack('<I',self.tick%1573040))
 def _input(self,u,p,s,d):
  return super()._input(u,0x3f8+p-self.port_base if self.port_base<=p<self.port_base+8 else p,s,d)
 def _output(self,u,p,s,v,d):
  self.physical_writes.append((p,v));return super()._output(u,0x3f8+p-self.port_base if self.port_base<=p<self.port_base+8 else p,s,v,d)
 def open(self,flag=b'/S1:0003:03:N'):
  if len(flag)>2 and flag[2] in b'1234':self.port_base=[0x3f8,0x2f8,0x3e8,0x2e8][flag[2]-49]
  self.uc.mem_write(self.data_base+self.argument,flag+b'\0')
  return self.call('_aspect_serial_open',[self.argument])
 def descriptor(self):
  psp=self.parent_psp;ds=0x1800;ring=0x1000;off=0x100
  data=struct.pack('<I12H',0x4f495341,1,28,psp,ds,ring,4096,0,0,psp^ds^ring^0xa510,0,0,0)
  self.uc.mem_write(ds*16+off,data);self.desc=ds*16+off
  return b':1800:0100'
 def restored(self):
  regs,divisor,vectors=self.initial
  for port in [0x21,0x3fb,0x3fc,0x3f9]:assert self.registers[port]==regs[port],(hex(port),self.registers,regs)
  assert self.divisor==divisor and self.vectors==vectors

def main():
 cases=[]
 def done(n,count):cases.append(dict(case=n,inputs=count,passed=True));print(n,count,flush=True)
 for flag in [b'',b'S1:0003:03:N',b'/S0:0003:03:N',b'/S5:0003:03:N',b'/S1:0000:03:N',b'/S1:GGGG:03:N',b'/S1:0003:83:N',b'/S1:0003:43:N',b'/S1:0003:00:N',b'/S1:0003:03:X',b'/S1:0003:03:Nextra',b'/S1:0003:03:N:0000:0000']:
  m=Serial();assert m.open(flag)==1 and not m.writes and not m.get('_aspect_serial_active')
 done('strict-com-divisor-format-flow-descriptor-before-port-IO',12)
 for port in range(1,5):
  m=Serial();assert m.open(('/S%d:0003:03:N'%port).encode())==0
  mask=0x10 if port in [1,3] else 8
  assert m.registers[0x21]==255-mask
  assert m.vectors[12 if port in [1,3] else 11]!=(0x1234,0xf000)
  m.receive_irq(b'X');assert m.call('_aspect_serial_read')==ord('X')
  assert m.call('_aspect_serial_close')==0;m.restored()
 done('all-four-standard-COM-physical-port-IRQ4or3-PIC-masks-and-actual-ISR',4)
 for flow in [b'N',b'S',b'H',b'B']:
  m=Serial();assert m.open(b'/S1:0003:03:'+flow)==0
  assert m.divisor==[3,0] and m.registers[0x3fc]&1 and m.get('_aspect_serial_active')
  m.call('_aspect_serial_poll');m.tx.clear()
  payload=b'\0\x1a\x80\xffABC'+(b'\x11\x13' if flow not in [b'S',b'B'] else b'')
  m.receive_irq(payload);assert m.call('_aspect_serial_available')==len(payload)
  assert bytes(m.call('_aspect_serial_read') for _ in payload)==payload
  assert m.call('_aspect_serial_read')==0xffff
  assert m.call('_aspect_serial_try_write',[0x1ff])==0 and m.tx[-1]==255
  assert m.call('_aspect_serial_close')==0;m.restored()
  writes=len(m.writes);assert m.call('_aspect_serial_close')==0 and len(m.writes)==writes
 done('real-ISR-binary-poll-read-lowbyte-write-closeonce-and-register-vector-PIC-restore',4)
 m=Serial();assert m.open()==0;m.receive_irq(b'UNREAD');assert m.call('_aspect_serial_close')==6;m.restored()
 done('standalone-unread-return-is-explicit-failure',1)
 for size,start in [(0,0),(9,0),(4096,1),(1539,4000)]:
  m=Serial();suffix=m.descriptor();assert m.open(b'/S1:0003:03:N'+suffix)==0
  base=m.symbols['uart_rx_buffer']-m.data_base;m.put('uart_rx_read',base+start);m.put('uart_rx_write',base+start)
  data=bytes((i*37)&255 for i in range(size))
  if data:m.receive_irq(data)
  assert m.call('_aspect_serial_close')==0;m.restored()
  d=struct.unpack('<I12H',m.uc.mem_read(m.desc,28))
  assert d[7]==size and d[8]==0 and d[10]==1,d
  assert bytes(m.uc.mem_read(m.target,size))==data
 done('ASIOvalidated-parent-allocation-wrap-full-ring-exact-publication-after-restore',4)
 for offset,value in [(0,0),(4,2),(6,26),(8,123),(14,4095),(16,1),(18,1),(20,0),(22,1),(24,1),(26,1)]:
  m=Serial();suffix=m.descriptor();m.uc.mem_write(m.desc+offset,struct.pack('<H',value));before=bytes(m.uc.mem_read(m.target,4096))
  assert m.open(b'/S1:0003:03:N'+suffix)==1 and not m.writes and bytes(m.uc.mem_read(m.target,4096))==before
 done('ASIOidentity-version-count-status-publication-reserved-guard-reject-before-IO',11)
 m=Serial();assert m.open(b'/S1:0003:03:S')==0;assert m.call('_aspect_serial_try_write',[65])==1;m.call('_aspect_serial_poll');assert m.tx==[0x11];m.receive_irq(b'\x13');assert m.call('_aspect_serial_try_write',[65])==1
 m.receive_irq(b'\x11');assert m.call('_aspect_serial_try_write',[65])==0;m.call('_aspect_serial_close');m.restored()
 m=Serial();assert m.open(b'/S1:0003:03:H')==0;m.registers[0x3fe]&=~16;assert m.call('_aspect_serial_try_write',[65])==1;m.call('_aspect_serial_close');m.restored()
 done('real-ISR-XOFF-XON-and-CTS-stalls-never-busywait-data-write',2)
 for initial in [0,1573037]:
  m=Serial();m.tick=initial;assert m.open()==0;m.registers[0x3fd]=0x20
  assert m.call('_aspect_serial_close')==7;m.restored()
  assert m.tick-initial<=40
 done('36-BIOS-tick-TEMT-stall-bounded-at-normal-and-midnight-close',2)
 m=Serial();assert m.open()==0;m.receive_irq(b'A'*4096+b'B');assert m.call('_aspect_serial_poll')==5
 assert m.get('uart_rx_count')==4096 and m.get('uart_rx_dropped')==1
 assert m.call('_aspect_serial_close')==5;m.restored()
 done('full-ring-overflow-never-overwrites-unread-and-close-retains-fatal-status',1)
 m=Serial();assert m.open(b'/S1:0003:03:S')==0;m.call('_aspect_serial_poll');m.tx.clear()
 m.receive_irq(b'X'*3073);assert not m.tx and m.get('uart_flow_pending',1)==0x13
 m.call('_aspect_serial_poll');assert m.tx==[0x13]
 for _ in range(3073):assert m.call('_aspect_serial_read')==ord('X')
 assert m.get('uart_flow_pending',1)==0x11;m.call('_aspect_serial_poll');assert m.tx==[0x13,0x11]
 assert m.call('_aspect_serial_close')==0;m.restored()
 done('actual-ISR-SOFT3073-highwater-128-lowwater-foreground-XOFF-XON',1)
 for kind in ['owner','signature','short-extent','ring-wrap','descriptor-overlap']:
  m=Serial();suffix=m.descriptor()
  if kind=='owner':m.uc.mem_write((m.parent_psp-1)*16+1,b'\0\0')
  if kind=='signature':m.uc.mem_write((m.parent_psp-1)*16,b'!')
  if kind=='short-extent':m.uc.mem_write((m.parent_psp-1)*16+3,b'\x10\0')
  if kind in ['ring-wrap','descriptor-overlap']:
   ring=0xff00 if kind=='ring-wrap' else 0x100
   m.uc.mem_write(m.desc+12,struct.pack('<H',ring));m.uc.mem_write(m.desc+20,struct.pack('<H',m.parent_psp^0x1800^ring^0xa510))
  assert m.open(b'/S1:0003:03:N'+suffix)==1 and not m.writes
 done('parent-MCB-owner-identity-extent-near-wrap-descriptor-ring-disjoint-guards',5)
 m=Serial();assert m.open(b'/S1:0003:03:B')==0
 assert m.get('uart_software_flow')==m.get('uart_hardware_flow')==1
 m.registers[0x3fe]&=~16
 assert m.call('_aspect_serial_try_write',[65])==1 and not m.tx
 m.call('_aspect_serial_poll');assert m.tx==[0x11]
 assert m.call('_aspect_serial_try_write',[65])==1
 m.registers[0x3fe]|=16;m.receive_irq(b'\x13')
 assert m.call('_aspect_serial_try_write',[65])==1
 m.receive_irq(b'\x11');assert m.call('_aspect_serial_try_write',[65])==0
 assert m.tx==[0x11,65] and m.get('uart_rx_count')==0
 assert m.call('_aspect_serial_close')==0;m.restored()
 done('combined-B-XON-bypasses-CTS-but-data-requires-both-CTS-and-peer-XON',1)
 result=dict(passed=True,groups=cases,inputs=sum(x['inputs'] for x in cases),binary_sha256=hashlib.sha256(uart.BINARY.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest(),limitations=['Kernel/ports modeled; actualDOS loopback test separately required.','Standard COM1..4 ports/IRQ masks are modeled; separate actual DOS backend tests use COM1 only.'],original_inputs=[])
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
