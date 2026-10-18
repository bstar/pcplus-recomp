#!/usr/bin/env python3
"""Linked single-owner COM migration with four independent modeled UARTs.

No application function is replaced: native snapshot/vector code, maintained
handoff and PROGRAM restore execute against modeled DOS/BIOS/hardware boundaries.
"""
import collections,hashlib,json,struct
from unicorn.x86_const import UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES,UC_X86_REG_EFLAGS
from live_setup_kernel import LiveSettings
from check_program_actions_live import ROOT,BINARY

BASES=[0x3f8,0x2f8,0x3e8,0x2e8]
IRQS=[4,3,4,3]
REGS=['lcr','mcr','ier','dll','dlm']
SAVED=['uart_saved_pic','uart_saved_lcr','uart_saved_mcr','uart_saved_ier',
       'uart_saved_dll','uart_saved_dlm','uart_previous_irq_offset','uart_previous_irq_segment']

class Ports(LiveSettings):
 # Hardware fixtures remain tied to their physical base when product globals
 # change. Parent PROGRAM/BIOS checks observe whichever UART is now selected.
 def field(name):
  def get(self):
   return self.devices[self.get('uart_port_rbr')][name] if self.devices is not None else getattr(self,'_'+name)
  def put(self,value):
   if self.devices is None:setattr(self,'_'+name,value)
   else:self.devices[self.get('uart_port_rbr')][name]=value
  return property(get,put)
 lcr=field('lcr');mcr=field('mcr');ier=field('ier');dll=field('dll');dlm=field('dlm')
 temt=field('temt');thre=field('thre');overrun=field('overrun');carrier=field('carrier');rx=field('rx')
 @property
 def vector(self):return self.get('terminal_irq_vector')
 @vector.setter
 def vector(self,value):pass
 @property
 def old_vector(self):return self.vectors[self.vector] if self.vectors is not None else self._old_vector
 @old_vector.setter
 def old_vector(self,value):self._old_vector=value
 def __init__(self):
  self.devices=None;self.vectors=None
  super().__init__(mutate_child=False)
  self.devices={base:dict(lcr=[3,0x1e,0x9b,7][i],mcr=[11,1,2,0][i],
    ier=[1,2,3,0][i],dll=[3,0x32,0x76,0x54][i],dlm=[0,0x12,0x34,0x56][i],
    temt=True,thre=True,overrun=False,carrier=False,rx=collections.deque()) for i,base in enumerate(BASES)}
  self.reads=[];self.writes=[];self.wire=[]
  self.uc.mem_write(0x400,struct.pack('<4H',*BASES))
  self.vectors={12:self._old_vector,11:(0x2468,0x1357)}
  self.uc.mem_write(11*4,struct.pack('<HH',*self.vectors[11]))
  first=self.devices[BASES[0]].copy()
  for key in REGS:first[key]=self.baseline['uart_saved_'+key]
  self.originals={base:{key:dev[key] for key in REGS} for base,dev in self.devices.items()}
  self.originals[BASES[0]]={key:first[key] for key in REGS}
  self.original_pic=self.baseline['uart_saved_pic']
  self.put('connection_state',0)
 def input_port(self,u,port,size,data):
  if self.devices is None:return super().input_port(u,port,size,data)
  if port==0x21:return self.pic
  for base,dev in self.devices.items():
   if not base<=port<=base+7:continue
   self.reads.append(port);at=port-base
   if at==0:
    if dev['lcr']&128:return dev['dll']
    assert dev['rx'],'Unexpected RBR read'
    self.data_reads+=1;return dev['rx'].popleft()
   if at==1:return dev['dlm'] if dev['lcr']&128 else dev['ier']
   if at==2:return 4 if dev['rx'] else 1
   if at==3:return dev['lcr']
   if at==4:return dev['mcr']
   if at==5:
    result=(32 if dev['thre'] else 0)|(64 if dev['temt'] else 0)|int(bool(dev['rx']))|(2 if dev['overrun'] else 0)
    dev['overrun']=False;return result
   if at==6:return 0x10|(128 if dev['carrier'] else 0)
   return 0
  return super().input_port(u,port,size,data)
 def output_port(self,u,port,size,value,data):
  if self.devices is None:return super().output_port(u,port,size,value,data)
  value&=255;self.writes.append((port,value))
  if port==0x21:self.pic=value;return
  for base,dev in self.devices.items():
   if not base<=port<=base+7:continue
   at=port-base
   if at==0:
    if dev['lcr']&128:dev['dll']=value
    else:self.wire.append((base,value))
   elif at==1:dev['dlm' if dev['lcr']&128 else 'ier']=value
   elif at==3:dev['lcr']=value
   elif at==4:dev['mcr']=value
   return
  return super().output_port(u,port,size,value,data)
 def vector_at(self,irq):return struct.unpack('<HH',self.uc.mem_read((irq+8)*4,4))
 def hardware(self):return {base:{key:d[key] for key in REGS} for base,d in self.devices.items()}
 def saved(self):return {n:self.get(n,1 if n.startswith('uart_saved_') else 2) for n in SAVED}
 def quiet(self):
  self.put('terminal_program_kind',1);self.put('terminal_program_status',4);self.put('terminal_program_active',1)
  dev=self.devices[self.get('uart_port_rbr')]
  self.put('terminal_program_mcr',dev['mcr'],1)
  self.call('uart_mask_irq');dev['lcr']&=127;dev['ier']=0;dev['mcr']&=~2
  self.call('uart_restore_interrupt',[self.get('terminal_irq_vector')])
 def candidate(self,port):
  raw=bytearray(self.uc.mem_read(self.symbols['terminal_configuration_values'],42))
  struct.pack_into('<H',raw,0,port);struct.pack_into('<HH',raw,32,BASES[port-1],IRQS[port-1])
  self.pointer=self.offset('terminal_setup_plan');self.uc.mem_write(self.data_base+self.pointer,bytes(raw))
  return self.pointer
 def handoff(self,port):
  result=self.call('terminal_port_handoff',ax=self.candidate(port))
  for r,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert self.uc.reg_read(r)==want
  return result
 def resume(self):
  self.call('terminal_program_restore_uart');self.put('terminal_program_active',0)
  base=self.get('uart_port_rbr');dev=self.devices[base];irq=self.get('terminal_irq_vector')-8
  assert self.vector_at(irq)==self.parent_vector
  assert (dev['lcr'],dev['mcr'],dev['ier'],dev['dll'],dev['dlm'])==(3,11,1,3,0)
  assert not self.pic&(1<<irq)
 def shutdown(self):
  self.call('uart_disable');self.call('uart_restore_interrupt',[self.get('terminal_irq_vector')]);self.call('uart_restore_hardware_state')
  assert self.hardware()==self.originals and self.pic==self.original_pic
  for vector,want in self.vectors.items():assert self.vector_at(vector-8)==want

def main():
 cases=[]
 def done(name,n):cases.append(dict(case=name,inputs=n,passed=True));print(name,n,flush=True)
 count=0
 for source in range(1,5):
  for target in range(1,5):
   if source==target:continue
   m=Ports()
   if source!=1:m.quiet();assert m.handoff(source)==0;m.resume()
   m.quiet();old=m.get('uart_port_rbr');assert m.handoff(target)==0
   assert m.hardware()[old]==m.originals[old]
   assert m.get('terminal_port_number')==target and m.get('terminal_irq_vector')==IRQS[target-1]+8
   assert m.get('uart_port_rbr')==BASES[target-1] and m.vector_at(IRQS[target-1])==m.vectors[IRQS[target-1]+8]
   assert m.devices[BASES[target-1]]['ier']==0 and not m.devices[BASES[target-1]]['lcr']&128
   assert m.pic&(1<<IRQS[target-1]) and m.data_reads==0
   m.resume()
   # Deliver binary input through the real ISR, and output through the native
   # checked UART writer on the new port. No bytes reach any previous UART.
   m.devices[BASES[target-1]]['rx'].append(0xa5)
   m.call('uart_receive_interrupt',irq=True);assert m.call('uart_receive_byte')==0xa5
   assert m.call('uart_try_write',ax=0x5a)==0x5a and not m.uc.reg_read(UC_X86_REG_EFLAGS)&1
   assert m.wire==[(BASES[target-1],0x5a)]
   m.shutdown();count+=1
 done('all-directed-port-pairs-shared-and-different-IRQs-native-traffic-and-final-full-restoration',count)
 m=Ports()
 for port in [2,3,4,1,4,3,2,1]:
  m.quiet();assert m.handoff(port)==0;m.resume()
 m.shutdown();done('repeated-roundtrips-recapture-original-state-without-a-per-port-snapshot-table',8)
 failures=[('connection_state',6),('connection_state',1),('terminal_parser_active',1),('terminal_tx_count',1),('uart_rx_count',1),
  ('uart_xoff_sent',1),('uart_flow_pending',17)]
 for name,value in failures:
  m=Ports();m.quiet();m.put(name,value,1 if name in ('uart_xoff_sent','uart_flow_pending') else 2)
  before=(m.hardware(),m.saved(),m.pic,bytes(m.uc.mem_read(44,8)),len(m.writes))
  assert m.handoff(2)==2
  assert (m.hardware(),m.saved(),m.pic,bytes(m.uc.mem_read(44,8)),len(m.writes))==before
  m.resume();m.shutdown()
 done('occupied-controller-TX-RX-and-unreleased-software-pause-do-not-transfer-resources',len(failures))
 count=0
 for device,key,value in [(0,'rx',collections.deque(b'R')),(1,'rx',collections.deque(b'T')),
   (0,'temt',False),(1,'temt',False),(0,'thre',False),(1,'thre',False),
   (0,'carrier',True),(1,'carrier',True),(1,'overrun',True),
   (0,'lcr',0x83),(0,'ier',1),(0,'mcr',3)]:
  m=Ports();m.quiet();m.devices[BASES[device]][key]=value
  before=(m.hardware(),m.saved(),m.pic,len(m.writes))
  assert m.handoff(2)==2
  assert (m.hardware(),m.saved(),m.pic,len(m.writes))==before and m.data_reads==0
  if key=='rx':assert m.devices[BASES[device]][key]==value
  # A failed acquisition still permits ordinary return to the old terminal
  # and its eventual native shutdown. Neither UART's baseline was replaced.
  m.resume();m.shutdown()
  count+=1
 m=Ports();m.quiet();m.pic&=~16;assert m.handoff(2)==2;count+=1
 done('pending-hardware-data-carrier-TEMT-format-and-IRQ-ownership-gates-preserve-both-UARTs',count)
 for device in [0,1]:
  for previous in [0,65534,65535]:
   m=Ports();m.quiet();m.put('uart_rx_dropped',previous);m.devices[BASES[device]]['overrun']=True
   before=(m.hardware(),m.saved(),m.pic,len(m.writes));assert m.handoff(2)==2
   assert m.get('uart_rx_dropped')==min(previous+1,65535)
   assert (m.hardware(),m.saved(),m.pic,len(m.writes))==before
   m.resume();m.shutdown()
 done('acknowledged-old-or-target-LSR-overrun-counts-loss-with-saturation-and-rejects-switch',6)
 for at,value in [(0,0),(0,5),(32,0x3f8),(32,0x1234),(34,4),(34,7)]:
  m=Ports();m.quiet();ptr=m.candidate(2);m.uc.mem_write(m.data_base+ptr+at,struct.pack('<H',value))
  before=(m.hardware(),m.saved(),m.pic,len(m.writes),len(m.reads))
  assert m.call('terminal_port_handoff',ax=ptr)==1
  assert (m.hardware(),m.saved(),m.pic,len(m.writes),len(m.reads))==before
 for ptr in [0,65500,65535]:
  m=Ports();m.quiet();assert m.call('terminal_port_handoff',ax=ptr)==1
 m=Ports();m.quiet();assert m.handoff(1)==1
 for name,value in [('terminal_program_active',0),('terminal_program_kind',0),('terminal_program_status',5)]:
  m=Ports();m.quiet();m.put(name,value);assert m.handoff(2)==1
 done('invalid-bounds-layout-same-port-and-foreground-owner-are-rejected',13)
 for bios in [0,0x3f8,0x1234]:
  m=Ports();m.quiet();m.uc.mem_write(0x402,struct.pack('<H',bios));before=(len(m.reads),len(m.writes),m.saved())
  assert m.handoff(2)==1 and (len(m.reads),len(m.writes),m.saved())==before
 done('BIOS-absent-or-mismatched-target-is-never-probed',3)
 for mcr in [0,1,2,3]:
  m=Ports();m.quiet();base=BASES[1];m.devices[base]['mcr']=mcr;m.originals[base]['mcr']=mcr
  ptr=m.candidate(2);before=(m.hardware(),m.saved(),m.pic,len(m.writes))
  assert m.call('terminal_port_check',ax=ptr)==0
  assert (m.hardware(),m.saved(),m.pic,len(m.writes))==before
  assert m.call('terminal_port_handoff',ax=ptr)==0
  assert all(value&1==mcr&1 for port,value in m.writes[before[3]:] if port==base+4)
  assert not m.devices[base]['mcr']&2
  m.resume();m.shutdown()
 done('preflight-does-not-acquire-and-target-DTR-never-pulses-during-acquisition',4)
 for problem in ['owner','bios','rx']:
  m=Ports();m.quiet();ptr=m.candidate(2)
  if problem=='owner':m.put('terminal_program_active',0)
  elif problem=='bios':m.uc.mem_write(0x402,b'\0\0')
  else:m.devices[BASES[1]]['rx'].append(ord('R'))
  before=(m.hardware(),m.saved(),m.pic,len(m.writes))
  assert m.call('terminal_port_check',ax=ptr)==(2 if problem=='rx' else 1)
  assert (m.hardware(),m.saved(),m.pic,len(m.writes))==before and m.data_reads==0
 done('preflight-failure-leaves-owner-and-queued-input-intact',3)
 result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
  inputs=sum(c['inputs'] for c in cases),cases=cases,
  sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['standalone/check_port_handoff.py','src/terminal/port_handoff.asm','src/terminal/program_actions.asm']},
  scope='Actual linked preflight/ownership primitive, native vector/snapshot routines, PROGRAM restoration, UART traffic and final shutdown with four independent modeled UARTs. Target DTR is preserved during acquisition. Settings UI integration has separate checks. BIOS/DOS/hardware modeled; no actual DOS multiport or physical hardware claim here.')
 (ROOT/'build/terminal/port-handoff-checks.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
