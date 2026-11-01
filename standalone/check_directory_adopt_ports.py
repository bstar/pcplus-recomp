#!/usr/bin/env python3
"""Run the linked adoption handoff on independent UART/PIC/vector fixtures.

Actual snapshot, handoff, restoration, IRQ and byte IO instructions execute.
Only hardware and DOS/BIOS boundaries are modeled; no product function is
patched, skipped or completed by this checker. Full C/UI adoption is separate.
"""
import argparse,collections,hashlib,json,struct
from pathlib import Path
import check_transport
from check_port_handoff import Ports,BASES,REGS
ROOT=Path(__file__).resolve().parents[1]
IRQS=(3,4,5,7)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class AdoptionPorts(Ports):
 def __init__(self,pic=0x47):
  super().__init__()
  self.vectors.update({13:(0x1122,0x3344),15:(0x5566,0x7788)})
  for vector in (13,15):self.uc.mem_write(vector*4,struct.pack('<HH',*self.vectors[vector]))
  # Establish this fixture's original PIC through the real native save path.
  self.shutdown();self.pic=pic;self.original_pic=pic
  self.call('uart_save_hardware_state');self.call('uart_set_baud_divisor',[38400,0]);self.call('uart_set_line_control',[0,8,1])
  self.mcr=11;self.ier=1;self.call('uart_install_interrupt',[self.get('terminal_irq_vector')])
  self.reads.clear();self.writes.clear();self.wire.clear();self.data_reads=0
 def quiet(self):
  super().quiet();self.put('terminal_program_kind',8);self.put('terminal_program_status',2);self.put('_terminal_directory_adopt_requested',1)
 def candidate(self,port,irq=None):
  pointer=super().candidate(port)
  if irq is not None:self.uc.mem_write(self.data_base+pointer+34,struct.pack('<H',irq))
  return pointer
 def move(self,port,irq):return self.call('terminal_port_handoff',ax=self.candidate(port,irq))
 def snapshot(self):
  return self.hardware(),self.saved(),self.pic,tuple(self.vector_at(i) for i in IRQS),self.get('terminal_port_number'),self.get('uart_irq_indices')
 def resumed(self,port,irq):
  self.call('terminal_program_restore_uart');self.put('terminal_program_active',0)
  assert self.get('terminal_port_number')==port and self.get('uart_irq_indices')==irq
  assert self.vector_at(irq)==self.parent_vector
  d=self.devices[BASES[port-1]];assert (d['dll'],d['dlm'],d['lcr'],d['ier'],d['mcr'])==(3,0,3,1,11)
  assert not self.pic&(1<<irq)
 def ready(self,port,irq):
  if (port,irq)!=(1,4):self.quiet();assert self.move(port,irq)==0;self.resumed(port,irq)
  return self
 def transition(self,port,irq):
  old_irq=self.get('uart_irq_indices');old_base=self.get('uart_port_rbr');self.quiet()
  before=self.snapshot();writes=len(self.writes);reads=self.data_reads;original_dtr=self.mcr&1
  assert self.call('terminal_port_check',ax=self.candidate(port,irq))==0
  assert self.snapshot()==before and len(self.writes)==writes
  assert self.move(port,irq)==0
  if old_irq!=irq:
   assert self.vector_at(old_irq)==self.vectors[old_irq+8]
   assert self.pic&(1<<old_irq)==self.original_pic&(1<<old_irq),('old IRQ mask not restored',old_irq,irq,self.pic,self.original_pic)
  if old_base!=BASES[port-1]:assert self.hardware()[old_base]==self.originals[old_base]
  else:
   assert all(value&1==original_dtr for p,value in self.writes[writes:] if p==old_base+4),'IRQ-only move pulsed DTR'
   for name in ('uart_saved_pic','uart_saved_lcr','uart_saved_mcr','uart_saved_ier','uart_saved_dll','uart_saved_dlm'):assert self.saved()[name]==before[1][name]
  assert self.data_reads==reads
  assert self.vector_at(irq)==self.vectors[irq+8] and self.devices[BASES[port-1]]['ier']==0 and self.pic&(1<<irq)
  self.resumed(port,irq)
  self.rx.append(0xa5);self.call('uart_receive_interrupt',irq=True);assert self.call('uart_receive_byte')==0xa5
  assert self.call('uart_try_write',ax=0x5a)==0x5a
  assert self.wire[-1:]==[(BASES[port-1],0x5a)]
  self.shutdown()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--smoke',action='store_true');a=p.parse_args();binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text());assert m['experimental_directory_adopt'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 check_transport.BINARY=binary;check_transport.MAP=binary.parent/'terminal.map'
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);cases=[]
 choices=[(port,irq) for port in range(1,5) for irq in IRQS]
 pairs=[((1,4),(1,5))] if a.smoke else [(s,t) for s in choices for t in choices if s!=t]
 for pic in ([0x47] if a.smoke else [0x47,0xff]):
  for source,target in pairs:
   x=AdoptionPorts(pic).ready(*source);x.transition(*target)
   cases.append(dict(case='handoff',source=source,target=target,initial_PIC=pic,passed=True))
 if not a.smoke:
  for problem in ['source-byte','target-byte','source-carrier','target-carrier','target-overrun','missing-BIOS','parser','pending-TX','ring-byte','wrong-owner','unrequested','already-published']:
   x=AdoptionPorts();x.quiet();pointer=x.candidate(2,5)
   assert x.call('terminal_port_check',ax=pointer)==0
   if problem=='source-byte':x.rx.append(0x52)
   elif problem=='target-byte':x.devices[BASES[1]]['rx'].append(0x54)
   elif problem=='source-carrier':x.carrier=True
   elif problem=='target-carrier':x.devices[BASES[1]]['carrier']=True
   elif problem=='target-overrun':x.devices[BASES[1]]['overrun']=True
   elif problem=='missing-BIOS':x.uc.mem_write(0x402,bytes(2))
   elif problem=='parser':x.put('terminal_parser_active',1)
   elif problem=='pending-TX':x.put('terminal_tx_count',1)
   elif problem=='ring-byte':x.put('uart_rx_count',1)
   elif problem=='wrong-owner':x.put('terminal_program_kind',6)
   elif problem=='unrequested':x.put('_terminal_directory_adopt_requested',0)
   else:x.put('_terminal_directory_adopt_requested',2)
   before=x.snapshot();writes=len(x.writes);reads=x.data_reads
   assert x.call('terminal_port_handoff',ax=pointer)!=0 and x.snapshot()==before and len(x.writes)==writes and x.data_reads==reads,problem
   cases.append(dict(case='late-refusal-'+problem,passed=True))
 result=dict(passed=True,binary_sha256=sha(binary),inputs=len(cases),cases=cases,original_inputs=[],sources={n:sha(ROOT/n) for n in ['standalone/check_directory_adopt_ports.py','standalone/check_port_handoff.py','standalone/live_setup_kernel.py','standalone/check_program_actions_live.py','standalone/check_meta_actions_live.py','standalone/check_transport.py','standalone/dos_image.py']},scope=__doc__+' This executes the acquisition/resumption portion under PROGRAM kind8/status2/requested1; it does not simulate successful full C/resource adoption or physical serial hardware.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'adoption port/IRQ inputs')
if __name__=='__main__':main()
