#!/usr/bin/env python3
"""Actual reused UART instructions and exact clock, modeled ports/DOS/BIOS only."""
import argparse,hashlib,itertools,json,re,struct
from pathlib import Path
from unicorn.x86_const import *
import check_uart
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/transfer-uart'
for name in ['BP','SI','DI']:setattr(check_uart,'UC_X86_REG_'+name,globals()['UC_X86_REG_'+name])
check_uart.BINARY=OUT/'TUART.EXE';check_uart.MAP=OUT/'transfer_uart.map'
class Machine(check_uart.Machine):
 def __init__(self,original=None):
  super().__init__();self.tick=0;self.native=original is not None
  if original:
   self.uc.mem_write(self.base,original[0x1200:0xe2d0]);self.ds=0x4000;self.data_base=0x40000
   self.symbols={n:self.data_base+int(a,16) for a,n in json.loads((ROOT/'docs/uart-layout.json').read_text())['state'].items()}
   self.symbols.update({n:self.base+a for n,a in {'uart_receive_byte':0xaa65,'uart_available':0xaad9,'uart_transmit_byte':0xab0b,'uart_transmit_buffer':0xab92,'uart_clear_receive_buffer':0xabca,'transfer_uart_header_byte':0x5ca0,'pcplus_seconds':0x3323,'transfer_dos_time':0x778c,'pcplus_escape_pressed':0x3f4b}.items()})
   for n,v in [('uart_rx_count',0),('uart_rx_write',0x7e20),('uart_rx_read',0x7e20),('uart_rx_last',0x8e1f),('uart_rx_mask',255),('uart_port_index',0),('uart_software_flow',0),('uart_hardware_flow',0),('uart_tx_paused',0),('uart_port_lcr',0x3fb),('uart_port_mcr',0x3fc),('uart_port_msr',0x3fe),('uart_port_lsr',0x3fd),('uart_port_thr',0x3f8),('uart_port_ier',0x3f9),('uart_port_rbr',0x3f8)]:self.put(n,v)
 def _code(self,u,at,size,data):
  super()._code(u,at,size,data)
  if self.symbols['transfer_uart_header_byte']<=at<self.symbols['transfer_uart_header_byte']+46:
   self.tick=(self.tick+1)&65535;u.mem_write(0x46c,struct.pack('<H',self.tick))
 def _interrupt(self,u,number,data):
  assert number==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x2c,('Unexpected DOSboundary',number)
  sec=next(self.seconds)%60;self.clock_calls+=1;u.reg_write(UC_X86_REG_CX,0x0c22);u.reg_write(UC_X86_REG_DX,sec*256+56)
 def ring(self,data):
  p=self.symbols['uart_rx_buffer']-self.data_base;self.uc.mem_write(self.data_base+p,data)
  self.put('uart_rx_read',p);self.put('uart_rx_write',p+len(data));self.put('uart_rx_count',len(data))
 def invoke(self,name,args=(),limit=2000000):
  result=self.call(name,args,limit=limit,bp=0xbabe,si=0x1234,di=0x5678)
  for reg,value in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert self.uc.reg_read(reg)==value,(name,'ABI')
  expected=0xf000-2*(len(args)+1)+2+(2 if name in ('uart_available','uart_transmit_byte') else 4 if name=='uart_transmit_buffer' else 0)
  assert self.uc.reg_read(UC_X86_REG_SP)==expected,(name,'cleanup')
  return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();image=None
 if a.original:
  image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==json.loads((ROOT/'reconstruction/transfer_uart/provenance.json').read_text())['source_sha256']
 rows=[]
 def compare(name,fn):
  value=fn(Machine());
  if image:assert fn(Machine(image))==value,(name,'original mismatch')
  rows.append(name)
 for timeout in [0,1,2,3,10]:
  for initial in [0,58,59]:
   for repeat in [1,3]:
    def timed(m,timeout=timeout,initial=initial,repeat=repeat):
     m.seconds=(v%60 for v in itertools.chain.from_iterable(itertools.repeat(v,repeat) for v in range(initial,initial+100)))
     assert m.invoke('uart_available',[timeout])==65535
     expected=1 if timeout==0 else timeout*repeat+1
     assert m.clock_calls==expected,(timeout,repeat,m.clock_calls)
     return m.clock_calls,m.get('uart_rx_count')
    compare(f'timeout-{timeout}-{initial}-{repeat}',timed)
 for byte in [0,1,0x13,0x18,0x80,0xff]:
  for timeout in [0,10]:
   def immediate(m,byte=byte,timeout=timeout):
    m.ring(bytes([byte]));assert m.invoke('uart_available',[timeout])==byte and m.clock_calls==0
    assert m.invoke('uart_receive_byte')==65535
    return m.get('uart_rx_count')
   compare(f'queued-immediate-{byte}-{timeout}',immediate)
 for count in [1,2,128,1024]:
  for hard in [0,1]:
   def bulk(m,count=count,hard=hard):
    data=bytes(i%256 for i in range(count));m.uc.mem_write(m.data_base+0xb000,data);m.put('uart_hardware_flow',hard)
    m.invoke('uart_transmit_buffer',[count,0xb000]);assert bytes(m.tx)==data
    return bytes(m.tx).hex()
   compare(f'raw-bulk-{count}-{hard}',bulk)
 def flush(m):
  m.ring(b'\0\xffABC');m.rx.extend(b'Q');m.invoke('uart_clear_receive_buffer')
  assert m.get('uart_rx_count')==0 and m.get('uart_rx_read')==m.get('uart_rx_write')==m.symbols['uart_rx_buffer']-m.data_base
  assert bytes(m.rx)==b'Q' and not m.polls[0x3f8]
  return m.invoke('uart_receive_byte')
 compare('flush-software-ring-not-hardware-RBR',flush)
 def header(m):
  assert m.invoke('transfer_uart_header_byte')==65535 and m.clock_calls==0
  return m.tick
 compare('36-change-BIOS-header-timeout',header)
 # Exact clock clobbers BX/CX/DX; no false SI/DI preservation claim needed.
 for second in [0,23,59]:
  def clock(m,second=second):
   m.seconds=itertools.repeat(second);answer=m.invoke('pcplus_seconds');assert answer==second
   sample=0x8f02 if m.native else m.symbols['transfer_dos_clock_sample']-m.data_base
   raw=bytes(m.uc.mem_read(m.data_base+sample,8));assert struct.unpack('<4H',raw)==(56,12,34,second)
   return raw.hex()
  compare(f'exact-DOS-clock-{second}',clock)
 # Maintained guard separately distinguishes validation from blocking original.
 extra=0
 for count,pointer in [(0,0xb000),(1025,0xb000),(1,0),(4,0xfffe),(0xffff,0x100)]:
  m=Machine();assert m.invoke('transfer_uart_send_bounded',[count,pointer])==1 and not m.tx;extra+=1
 for count,pointer in [(1,0xffff),(2,0xfffe),(1024,0xb000)]:
  m=Machine();data=bytes(i%256 for i in range(count));m.uc.mem_write(m.data_base+pointer,data)
  assert m.invoke('transfer_uart_send_bounded',[count,pointer])==0 and bytes(m.tx)==data;extra+=1
 # Prove why the maintained guard is necessary; raw zero count wraps DI.
 m=Machine();m.invoke('uart_transmit_buffer',[0,0x100],limit=3000000);assert len(m.tx)==65536;extra+=1
 # Source-linked flow branches execute the declared UI/cancel fixture bodies;
 # no callback is skipped. These tests do not claim full original vendor UI.
 m=Machine();m.put('uart_hardware_flow',1);m.cts_after=100000;m.put('transfer_fixture_escape',1)
 assert m.invoke('uart_transmit_byte',[0x55])==0x55 and m.tx==[0x55];extra+=1
 for busy in ['CTS','THRE']:
  m=Machine();m.put('uart_hardware_flow',1 if busy=='CTS' else 0)
  if busy=='CTS':m.cts_after=100000
  else:m.registers[0x3fd]=0;m.put('transfer_fixture_escape',1)
  try:m.invoke('uart_transmit_byte',[0x55],limit=1000)
  except AssertionError as e:assert 'did not return within' in str(e),e
  else:raise AssertionError((busy,'legacy blocking path unexpectedly returned'))
  assert not m.tx;extra+=1
 for escape,want_calls in [(0,21),(1,1)]:
  m=Machine();m.put('uart_tx_paused',1);m.put('transfer_fixture_escape',escape)
  m.invoke('uart_transmit_byte',[0x55]);assert m.tx==[0x55] and m.get('uart_tx_paused')==0
  assert m.clock_calls==want_calls and m.get('transfer_fixture_flow_calls')==1;extra+=1
 m=Machine();m.put('transfer_fixture_escape',1);m.invoke('uart_available',[3])
 assert m.clock_calls==4;extra+=1
 proof={'passed':True,'binary_sha256':hashlib.sha256((OUT/'TUART.EXE').read_bytes()).hexdigest(),'compared_inputs':len(rows),'original_comparisons':len(rows) if image else 0,'maintained_inputs':extra,'cases':rows,'scope':'Existing real UART core + exact DOS clock/header; modeled DOS2c/UART/PIC/BIOS tick memory. Original comparisons use unchanged resident instructions; maintained bounds remain separate. No skipped product callbacks.'};(OUT/'checks.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
