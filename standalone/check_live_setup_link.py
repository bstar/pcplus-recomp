#!/usr/bin/env python3
"""Real foreground serial choice, old-format XON/TEMT gate and same-port commit."""
import hashlib,json,struct
from live_setup_kernel import LiveSettings
from check_directory_live import word
from check_program_actions_live import ROOT,BINARY
class Link(LiveSettings):
 def __init__(self,**kw):
  self.serial_events=[];self.child_busy=False;self.busy_after_xon=False
  super().__init__(**kw);self.prompt_key_sent=True
 def interrupt(self,u,number,data):
  from unicorn.x86_const import UC_X86_REG_AX
  ax=u.reg_read(UC_X86_REG_AX);result=super().interrupt(u,number,data)
  if number==0x21 and ax==0x4b00 and self.child_busy:self.temt=False;self.advance_ticks=True
  return result
 def output_port(self,u,port,size,value,data):
  if hasattr(self,'lcr') and port==self.get('uart_port_thr') and not self.lcr&0x80:
   self.serial_events.append((value&255,self.dll|(self.dlm<<8),self.lcr))
   if value==17 and self.busy_after_xon:self.temt=False;self.advance_ticks=True
  return super().output_port(u,port,size,value,data)
 def launch(self,raw,choice=ord('Y'),extra_ack=False):
  self.after_raw=raw;self.keys.append(0x7100);self.keys.append(choice)
  if extra_ack:self.keys.append(0x1c0d)
  self.poll();assert self.get('terminal_program_pending')
  for _ in range(6):
   self.safe()
   if not self.get('terminal_program_pending'):break
  assert not self.get('terminal_program_active') and not self.keys
 def preserved(self):
  assert self.vector_value()==self.parent_vector and not self.pic&0x10 and self.ier==1
  assert {n:self.get(n,1 if n.startswith('uart_saved_') else 2) for n in self.baseline}==self.baseline
  assert self.data_reads==0 and bytes(self.rx)==b'R'
  assert bytes(self.uc.mem_read(0xb8000,4000))==self.original_screen
def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 for rate,index in [(300,0),(2400,2),(4800,3),(9600,4),(19200,5),(57600,7),(115200,8)]:
  m=Link();m.launch(word(m.raw,2,index));assert m.get('terminal_setup_link_status')==1
  assert (m.dll,m.dlm)==((115200//rate)&255,(115200//rate)>>8) and m.get('terminal_baud_low')==rate&65535 and m.get('terminal_baud_high')==rate>>16
  assert struct.unpack('<4H',m.uc.mem_read(m.symbols['terminal_setup_outcome'],8))==(0,0,2,0)
  m.preserved()
 done('accepted-all-changed-supported-rates-program-real-divisor-without-baseline-recapture',7)
 count=0
 for parity in range(5):
  for bits in [7,8]:
   for stop in [1,2]:
    if (parity,bits,stop)==(0,8,1):continue
    m=Link();raw=m.raw
    for at,value in [(4,parity),(6,stop),(8,bits)]:raw=word(raw,at,value)
    m.launch(raw);assert m.lcr==(bits-5)|(4 if stop==2 else 0)|([0,8,24,40,56][parity])
    assert (m.get('terminal_parity'),m.get('terminal_data_bits'),m.get('terminal_stop_bits'))==(parity,bits,stop)
    m.preserved();count+=1
 done('every-changed-supported-line-format-programs-native-LCR',count)
 for choice in [ord('N'),27,32,13]:
  m=Link();m.launch(word(m.raw,2,8),choice)
  assert m.get('terminal_setup_link_status')==2 and (m.dll,m.dlm,m.lcr)==(3,0,3) and m.get('terminal_baud_low')==38400
  assert struct.unpack('<4H',m.uc.mem_read(m.symbols['terminal_setup_outcome'],8))==(0,0,0,2);m.preserved()
 done('No-Escape-space-and-Enter-decline-without-consuming-following-input',4)
 count=0
 for oldsoft,oldhard in [(0,0),(0,1),(1,0),(1,1)]:
  for soft,hard in [(0,0),(0,1),(1,0),(1,1)]:
   if (soft,hard)==(oldsoft,oldhard):continue
   m=Link();m.put('uart_software_flow',oldsoft);m.put('uart_hardware_flow',oldhard)
   raw=word(word(m.raw,0x198,soft),0x19a,hard);m.launch(raw)
   assert (m.get('uart_software_flow'),m.get('uart_hardware_flow'))==(soft,hard)
   assert m.mcr&3==3 and m.get('uart_tx_paused')==0
   if oldsoft:assert [e for e in m.serial_events if e[0]==17]==[(17,3,3)]
   if soft and not oldsoft:assert m.get('uart_flow_pending',1)==17
   if not soft:assert m.get('uart_flow_pending',1)==m.get('uart_xoff_sent',1)==0
   m.preserved();count+=1
 done('all-changed-software-hardware-flow-combinations-and-old-format-XON',count)
 for oldsoft,oldhard,soft,hard in [(1,0,1,1),(1,0,0,1),(1,0,0,0),(0,1,1,1),(1,1,1,0)]:
  m=Link();m.put('uart_software_flow',oldsoft);m.put('uart_hardware_flow',oldhard)
  m.receive_irq(b'R'*129);m.data_reads=0
  m.launch(word(word(m.raw,0x198,soft),0x19a,hard));m.preserved()
  assert m.get('uart_rx_count')==129
  assert m.get('uart_rts_lowered',1)==int(hard and not soft)
  if soft:assert m.get('uart_flow_pending',1)==19 and m.mcr&2
  elif hard:assert not m.mcr&2
  else:assert m.mcr&2
  assert m.call('uart_receive_byte')==ord('R') and m.get('uart_rx_count')==128
  assert m.get('uart_rts_lowered',1)==0 and m.mcr&2
  if soft:assert m.get('uart_flow_pending',1)==17
 done('buffered-RX-keeps-conservative-pause-and-dual-flow-selects-releasable-SOFT-owner',5)
 m=Link();m.put('uart_software_flow',1)
 m.put('terminal_parity',2);m.put('terminal_data_bits',7);m.put('terminal_stop_bits',2);m.lcr=0x1e
 m.launch(word(m.raw,2,8))
 assert m.serial_events==[(19,3,0x1e),(17,3,0x1e)] and (m.dll,m.dlm,m.lcr)==(1,0,3)
 # File still requests SOFT0, so the accepted proposal changes both baud/flow.
 assert m.get('uart_software_flow')==0
 m.enqueue(b'q');m.poll();assert m.serial_events[-1]==(ord('q'),1,3)
 done('old-pause-is-physically-released-before-new-rate-carries-ordinary-data',1)
 for after_xon in [False,True]:
  m=Link();m.put('uart_software_flow',1);m.child_busy=not after_xon;m.busy_after_xon=after_xon
  raw=word(word(m.raw,2,8),0x1a4,65535);m.launch(raw,extra_ack=True)
  assert m.get('terminal_setup_link_status')==3 and m.get('terminal_baud_low')==38400 and (m.dll,m.dlm)==(3,0)
  assert m.get('terminal_break_delay_units')==65535 and b'Line busy' in m.local_text
  assert 36<=m.tick<=40;m.preserved()
 done('blocked-TEMT-before-and-after-XON-defers-serial-with-bounded-wait',2)
 m=Link();m.launch(word(m.raw,2,8));m.prompt_key_sent=True;m.rx.clear();m.data_reads=0
 m.launch(word(m.raw,2,1));assert m.get('terminal_baud_low')==1200 and (m.dll,m.dlm)==(96,0)
 m.preserved();done('successfully-applied-rate-can-be-reverted-in-the-next-editor-session',1)
 m=Link();m.put('connection_state',6);m.launch(word(m.raw,2,8));m.preserved()
 assert m.get('connection_state')==6 and not m.tx and (m.dll,m.dlm)==(1,0)
 m.call('uart_receive_interrupt',irq=True);byte=m.call('uart_receive_byte');assert byte==ord('R')
 m.call('terminal_connection_receive',ax=byte)
 from unicorn.x86_const import UC_X86_REG_EFLAGS
 assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&1 and m.get('connection_state')==6
 done('established-session-retains-controller-state-and-pending-RX-after-accepted-baud',1)
 m=Link();raw=word(word(word(m.raw,0,1),2,8),4,2);m.launch(raw,extra_ack=True)
 assert m.get('terminal_setup_link_status')==3 and (m.dll,m.dlm,m.lcr)==(3,0,3)
 assert m.get('terminal_port_number')==1 and m.get('terminal_setup_outcome',8)>>48==7
 m.preserved();done('different-port-request-never-partially-applies-its-baud-or-line-to-old-port',1)
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),inputs=sum(c['inputs'] for c in cases),cases=cases,scope='Actual linked DOS foreground choice, C policy/acknowledgment, native UART setters, old-format XON/TEMT gate, ISR/video restoration and original baseline retention. Kernel/BIOS/UART are modeled. Same port only; port/profile remain deferred. Physical peer must independently match the chosen format; real DOS timer/serial tests are separate.')
 (ROOT/'build/terminal/live-setup-link-checks.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
