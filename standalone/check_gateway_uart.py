#!/usr/bin/env python3
"""Run linked live Gateway IRQ/return code; UART/PIC/IVT endpoints modeled."""
import argparse,collections,hashlib,itertools,json,struct
from pathlib import Path
from unicorn import UC_HOOK_INSN
from unicorn.x86_const import *
from check_directory_identity import Identity
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class UART(Identity):
 def __init__(self,binary,port=1,irq=None,flow='N'):
  super().__init__(binary);self.port=[0x3f8,0x2f8,0x3e8,0x2e8][port-1];self.irq=irq or (4 if port in (1,3) else 3);self.vector=self.irq+8
  self.rx=collections.deque();self.tx=[];self.reads=[];self.writes=[];self.fifo=False
  self.reg={0x21:0xff^(1<<self.irq),1:1,3:3,4:0xb,5:0x60,6:0x90};self.divisor=[12,0]
  for name,off in [('uart_port_rbr',0),('uart_port_thr',0),('uart_port_ier',1),('uart_port_lcr',3),('uart_port_mcr',4),('uart_port_lsr',5)]:self.put(name,self.port+off)
  self.put('uart_port_index',port-1);self.uc.mem_write(self.symbols['uart_irq_indices']+2*(port-1),struct.pack('<H',self.irq));self.put('terminal_irq_vector',self.vector)
  self.put('terminal_program_active',1);self.put('terminal_program_kind',9);self.put('terminal_program_pending',0);self.put('hardware_active',1,1);self.put('vector_active',1,1)
  self.put('uart_software_flow',int(flow in 'SB'));self.put('uart_hardware_flow',int(flow in 'HB'))
  self.put('uart_rx_count',0);self.put('uart_rx_read',self.offset('uart_rx_buffer'));self.put('uart_rx_write',self.offset('uart_rx_buffer'));self.put('uart_rx_last',self.offset('uart_rx_buffer')+4095)
  self.parent=self.entries['uart_receive_interrupt'];self.set_vector(self.parent)
  self.put('uart_previous_irq_offset',0x1234);self.put('uart_previous_irq_segment',0xf000)
  self.uc.hook_add(UC_HOOK_INSN,self.input,None,1,0,UC_X86_INS_IN);self.uc.hook_add(UC_HOOK_INSN,self.output,None,1,0,UC_X86_INS_OUT)
 def set_vector(self,pair):self.uc.mem_write(self.vector*4,struct.pack('<HH',pair[1],pair[0]))
 def get_vector(self):off,seg=struct.unpack('<HH',self.uc.mem_read(self.vector*4,4));return seg,off
 def input(self,u,p,s,data):
  self.reads.append(p)
  if p==0x21:return self.reg[p]
  off=p-self.port
  if off in (0,1) and self.reg[3]&0x80:return self.divisor[off]
  if off==0:return self.rx.popleft() if self.rx else 0
  if off==2:
   value=4 if self.rx and self.reg[1]&1 else 2 if self.reg[1]&2 and self.reg[5]&0x20 else 0 if self.reg[1]&8 and self.reg[6]&15 else 1
   return value|(0xc0 if self.fifo else 0)
  value=self.reg.get(off,0)
  if off==5:self.reg[5]&=~0x1e
  if off==6:self.reg[6]&=0xf0
  return value
 def output(self,u,p,s,v,data):
  self.writes.append((p,v))
  if p==0x21:self.reg[p]=v;return
  if p==0x20:return
  off=p-self.port
  if off in (0,1) and self.reg[3]&0x80:self.divisor[off]=v
  elif off==0:self.tx.append(v)
  elif off==2:self.fifo=bool(v&1)
  else:self.reg[off]=v
 def far(self,name,flags=0x202,foreign=False):
  u=self.uc;seg,off=self.entries[name];sp=self.offset('terminal_stack_top')-4
  u.mem_write(self.data_base+sp,struct.pack('<HH',self.return_offset,self.code_segment))
  regs={UC_X86_REG_CS:seg,UC_X86_REG_DS:self.ds+int(foreign),UC_X86_REG_SS:self.ds,UC_X86_REG_ES:0xb800,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:flags,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678}
  for r,v in regs.items():u.reg_write(r,v)
  self.waiting=(self.code_segment,self.code_base+self.return_offset);u.emu_start(self.symbols[name],0,count=500000)
  assert u.reg_read(UC_X86_REG_CS)==self.code_segment and u.reg_read(UC_X86_REG_IP)==self.return_offset and u.reg_read(UC_X86_REG_SP)==sp+4,name
  for r in (UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI):assert u.reg_read(r)==regs[r],(name,r)
  assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==flags&0x600
  self.waiting=None;return u.reg_read(UC_X86_REG_AX)
 def interrupt(self,u,n,data):
  assert n==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x25,'Only fallback vector restoration may use DOS'
  self.uc.mem_write((u.reg_read(UC_X86_REG_AX)&255)*4,struct.pack('<HH',u.reg_read(UC_X86_REG_DX),u.reg_read(UC_X86_REG_DS)))
 def irq_run(self,payload=b''):
  self.rx.extend(payload);u=self.uc;seg,off=self.get_vector();child_ss=0x8800;sp=0xe000
  regs={UC_X86_REG_CS:seg,UC_X86_REG_DS:0x8700,UC_X86_REG_SS:child_ss,UC_X86_REG_ES:0x8600,UC_X86_REG_SP:sp,UC_X86_REG_EFLAGS:0x402,UC_X86_REG_AX:0x9876,UC_X86_REG_BX:0x1234,UC_X86_REG_CX:0x5678,UC_X86_REG_DX:0x4321,UC_X86_REG_BP:0xbabe,UC_X86_REG_SI:0x1234,UC_X86_REG_DI:0x5678}
  u.mem_write(child_ss*16+sp,struct.pack('<HHH',0x1234,0x7000,0x602))
  for r,v in regs.items():u.reg_write(r,v)
  self.waiting=(0x7000,0x71234);u.emu_start(seg*16+off,0,count=600000)
  assert u.reg_read(UC_X86_REG_CS)==0x7000 and u.reg_read(UC_X86_REG_IP)==0x1234 and u.reg_read(UC_X86_REG_SP)==sp+6
  for r in (UC_X86_REG_DS,UC_X86_REG_SS,UC_X86_REG_ES,UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI):assert u.reg_read(r)==regs[r],('IRQ register',r)
  assert u.reg_read(UC_X86_REG_EFLAGS)&0x600==0x600;self.waiting=None
 def ring(self):return bytes(self.uc.mem_read(self.symbols['uart_rx_buffer'],4096)),self.get('uart_rx_read'),self.get('uart_rx_write'),self.get('uart_rx_count')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_gateway_uart'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir(parents=True);cases=[]
 def record(name,**info):cases.append(dict(case=name,passed=True,**info))
 for port,flow in itertools.product(range(1,5),'NSHB'):
  m=UART(binary,port=port,flow=flow);initial=m.ring();assert m.far('gateway_uart_begin')==0 and m.reg[1]==9 and m.get_vector()==m.entries['gateway_uart_interrupt'] and m.ring()==initial
  assert m.far('gateway_uart_begin')==4
  payload=b'A'*3200;m.irq_run(payload);assert m.get('uart_rx_count')==3200 and m.ring()[0][:3200]==payload
  assert m.tx==([19] if flow in 'SB' else []) and not m.get('uart_rx_dropped')
  assert bool(m.get('uart_rts_lowered',1))==(flow in 'HB') and m.reg[4]==(9 if flow in 'HB' else 11)
  before=m.ring();baseline=(m.get('uart_previous_irq_offset'),m.get('uart_previous_irq_segment'));m.reg[0x21]^=1;assert m.far('terminal_process_quiet_uart',flags=2)==0 and m.ring()==before
  assert m.far('gateway_uart_end')==0 and m.get_vector()==m.parent and m.reg[1]==1 and not m.reg[0x21]&1
  assert m.ring()==before and m.get('gateway_uart_active')==0
  assert baseline==(m.get('uart_previous_irq_offset'),m.get('uart_previous_irq_segment'))
  record('COM'+str(port)+'-'+flow,retained_bytes=3200)
 for port,irq in [(3,5),(4,7)]:
  m=UART(binary,port=port,irq=irq,flow='B');assert m.far('gateway_uart_begin')==0;m.irq_run(b'A'*3200)
  assert m.tx==[19] and m.get('uart_rx_count')==3200 and m.reg[4]==9 and m.far('gateway_uart_end')==0 and m.get_vector()==m.parent
  record('custom-COM'+str(port)+'-IRQ'+str(irq))
 m=UART(binary,flow='S');assert m.far('gateway_uart_begin')==0;m.reg[5]=0x40;m.irq_run(b'A'*3073)
 assert not m.tx and m.get('uart_flow_pending',1)==19 and m.reg[1]==11
 reads=m.reads.count(m.port);m.reg[5]=0x60;m.irq_run();assert m.tx==[19] and m.reads.count(m.port)==reads and m.reg[1]==9
 assert m.far('gateway_uart_end')==0;record('deferred-THRE-XOFF-no-RBR-read')
 m=UART(binary,flow='B');assert m.far('gateway_uart_begin')==0;m.irq_run(b'A'*3200);assert m.far('gateway_uart_end')==0
 m.put('uart_rx_count',129);m.put('uart_rx_read',m.offset('uart_rx_buffer')+3071)
 assert m.call('uart_receive_byte')==65 and m.get('uart_rx_count')==128 and m.get('uart_rts_lowered',1)==1
 m.call('uart_poll_flow');assert m.reg[4]==11 and not m.get('uart_rts_lowered',1) and not m.get('uart_xoff_sent',1) and not m.get('uart_flow_pending',1) and m.tx==[19,17]
 record('combined-SH-low-water-resumes-RTS-and-XON')
 for fault,status in [('DTR',8),('framing',8),('divisor',8),('vector',8),('FIFO',8),('IER',8),('overrun',5),('TEMT',7),('ring-overflow',5)]:
  m=UART(binary);assert m.far('gateway_uart_begin')==0
  if fault=='DTR':m.reg[4]&=~1
  elif fault=='framing':m.reg[3]=0x9e
  elif fault=='divisor':m.divisor=[0x34,0x12]
  elif fault=='vector':m.set_vector((0x7777,0x5555))
  elif fault=='FIFO':m.fifo=True
  elif fault=='IER':m.reg[1]=0
  elif fault=='overrun':m.reg[5]|=2
  elif fault=='TEMT':m.reg[5]=0x20
  elif fault=='ring-overflow':m.irq_run(b'A'*4097)
  ring=m.ring();assert m.far('terminal_process_quiet_uart',flags=2)==0
  assert m.get('gateway_uart_fault')==status,(fault,m.get('gateway_uart_fault'))
  assert m.far('gateway_uart_end')==status and m.get_vector()==m.parent and m.reg[1]==1 and m.reg[3]==3 and m.reg[4]==11 and m.divisor==[12,0] and not m.fifo and m.ring()==ring
  record('child-'+fault,status=status)
 m=UART(binary);assert m.far('gateway_uart_begin')==0;m.reg[6]=0x18;m.irq_run();assert m.get('gateway_uart_carrier_falls',1)==1 and m.get('gateway_uart_dcd_delta',1)==1 and not m.get('gateway_uart_fault')
 assert m.far('gateway_uart_end')==0;record('DCD-fall-observed-without-false-line-fault')
 for fault,status in [('wrong-kind',4),('pending',4),('inactive',4),('no-hardware',4),('no-vector',4),('TX-queued',7),('BREAK',7),('flow-queued',7),('existing-drop',5),('bad-base',4),('wrong-vector',4),('masked-IRQ',4),('BREAK-line',8),('FIFO',8),('IER',8),('loopback',8),('no-OUT2',8),('TX-busy',7)]:
  m=UART(binary)
  if fault=='wrong-kind':m.put('terminal_program_kind',0)
  elif fault=='pending':m.put('terminal_program_pending',1)
  elif fault=='inactive':m.put('terminal_program_active',0)
  elif fault=='no-hardware':m.put('hardware_active',0,1)
  elif fault=='no-vector':m.put('vector_active',0,1)
  elif fault=='TX-queued':m.put('terminal_tx_count',1)
  elif fault=='BREAK':m.put('uart_break_hold',1)
  elif fault=='flow-queued':m.put('uart_flow_pending',19,1)
  elif fault=='existing-drop':m.put('uart_rx_dropped',1)
  elif fault=='bad-base':m.put('uart_port_rbr',0x1234)
  elif fault=='wrong-vector':m.set_vector((0x7777,0x1234))
  elif fault=='masked-IRQ':m.reg[0x21]|=1<<m.irq
  elif fault=='BREAK-line':m.reg[3]|=0x40
  elif fault=='FIFO':m.fifo=True
  elif fault=='IER':m.reg[1]=0
  elif fault=='loopback':m.reg[4]|=0x10
  elif fault=='no-OUT2':m.reg[4]&=~8
  elif fault=='TX-busy':m.reg[5]=0x20
  vector=m.get_vector();assert m.far('gateway_uart_begin')==status and not m.writes and m.get_vector()==vector and m.get('gateway_uart_active')==0,fault
  record('admission-'+fault,status=status)
 m=UART(binary);assert m.far('gateway_uart_begin')==0;m.put('gateway_uart_storage',0)
 before=m.ring();m.far('terminal_process_quiet_uart',flags=2)
 assert m.reg[1]==0 and m.reg[0x21]&(1<<m.irq) and m.get_vector()==(0xf000,0x1234) and m.ring()==before
 assert m.far('gateway_uart_end')==4 and m.get('gateway_uart_active')==1
 record('corrupt-lease-masks-child-before-IF1')
 for name,flags,foreign in [('begin',2,False),('begin',0x602,False),('begin',0x202,True),('return',0x202,False),('end',2,False)]:
  m=UART(binary);writes=len(m.writes);assert m.far('gateway_uart_'+name,flags,foreign)==(1 if name=='return' else 4) and len(m.writes)==writes
  record('context-'+name+'-'+str(flags)+'-'+str(foreign))
 result=dict(passed=True,binary_sha256=sha(binary),inputs=len(cases),cases=cases,original_inputs=[],scope=__doc__+' Actual wrapper/native RX and far ABI execute with foreign child DS/SS/DF. No real DOS child, physical UART or BBS acceptance.',sources={n:sha(ROOT/n) for n in ['standalone/check_gateway_uart.py','standalone/check_directory_identity.py','standalone/dos_image.py','src/terminal/gateway_uart.asm','src/terminal/program_actions.asm']},memory=inspect_terminal_memory(binary,binary.with_name('terminal.map')))
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'Gateway UART cases')
if __name__=='__main__':main()
