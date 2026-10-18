#!/usr/bin/env python3
"""Actual linked live receive owner, native engine, UART/IRQ, UI and storage.

Only UART/BIOS/tick hardware and DOS filesystem syscalls are modeled. No product
callback is replaced, patched, skipped or manually returned from. Synthetic
peer bytes enter the hardware FIFO and execute the real recovered UART ISR.
"""
import binascii,hashlib,json,struct
from unicorn.x86_const import *
from check_program_actions_live import LiveProgram
from check_meta_actions_live import DAY,ROOT,BINARY

class LiveTransfer(LiveProgram):
 def __init__(self,*,data=bytes(range(128)),peer=True,fault=None,after_create=None):
  self.files={};self.handles={};self.fs_calls=[];self.events=[];self.fault=fault;self.irq_in_service=False
  self.after_create=after_create;self.peer_enabled=peer;self.peer_state=0
  self.blocks=tuple(data) if isinstance(data,(tuple,list)) else ((data,) if data else ());self.payload=b''.join(self.blocks);self.block_index=0;self.filename=b'OWNED.BIN';self.filename_sent=False;self.waiting_ui=False
  super().__init__()
  self.advance_ticks=True;self.tick=0;self.tick_reads=0;self.tx.clear()
  self.calls.clear();self.port_writes.clear();self.fs_calls.clear();self.events.clear()
 def tick_hook(self,u,address,size,_):
  if address in (self.symbols.get('terminal_tick_low'),self.symbols.get('terminal_clock_ticks')):
   self.tick_reads+=1
   if self.advance_ticks and self.tick_reads%8==0:
    self.tick=(self.tick+1)%DAY
   u.mem_write(0x46c,struct.pack('<I',self.tick))
  # Model real maskable hardware IRQ delivery, executing the actual ISR/IRET.
  if self.rx and not self.irq_in_service and not self.pic&(1<<(self.get('terminal_irq_vector')-8)) and address!=self.base+self.return_offset and u.reg_read(UC_X86_REG_EFLAGS)&0x200:
   self.irq_in_service=True
   sp=u.reg_read(UC_X86_REG_SP);ss=u.reg_read(UC_X86_REG_SS)
   frame=struct.pack('<3H',u.reg_read(UC_X86_REG_IP),u.reg_read(UC_X86_REG_CS),u.reg_read(UC_X86_REG_EFLAGS)&65535)
   u.mem_write(ss*16+((sp-6)&65535),frame)
   u.reg_write(UC_X86_REG_SP,(sp-6)&65535)
   u.reg_write(UC_X86_REG_EFLAGS,u.reg_read(UC_X86_REG_EFLAGS)&~0x300)
   u.reg_write(UC_X86_REG_CS,self.base_segment)
   u.reg_write(UC_X86_REG_IP,self.symbols['uart_receive_interrupt']-self.base)
 def path(self,segment,offset):
  raw=bytes(self.uc.mem_read(segment*16+offset,64));return raw.split(b'\0',1)[0].decode('ascii').upper().replace('/','\\')
 def interrupt(self,u,number,data):
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8
  if number==0x10 and ah==2 and self.waiting_ui and not self.filename_sent and u.reg_read(UC_X86_REG_DX)>>8==24:
   self.keys.extend(list(self.filename)+[0x1c0d]);self.filename_sent=True
  if number!=0x21 or ah not in (0x43,0x5b,0x40,0x3e,0x56,0x41):
   return super().interrupt(u,number,data)
  ds=u.reg_read(UC_X86_REG_DS);dx=u.reg_read(UC_X86_REG_DX);bx=u.reg_read(UC_X86_REG_BX);cx=u.reg_read(UC_X86_REG_CX)
  error=0;result=0;name=None
  if ah==0x43:
   name=self.path(ds,dx)
   if name not in self.files:error=2
   else:u.reg_write(UC_X86_REG_CX,0)
  elif ah==0x5b:
   name=self.path(ds,dx)
   if self.fault=='create':error=5
   elif name in self.files:error=80
   else:
    self.files[name]=bytearray();self.handles[5]=name;result=5
    if self.after_create=='escape':self.keys.append(0x011b)
    elif self.after_create=='altx':self.keys.append(0x2d00)
    elif self.after_create=='cts':self.cts=False;self.put('uart_hardware_flow',1)
    elif self.after_create=='thre':self.thre=False
    elif self.after_create=='carrier':self.carrier=False
  elif ah==0x40:
   name=self.handles.get(bx)
   if name is None:error=6
   elif self.fault=='write':error=5
   else:
    result=min(cx,1) if self.fault=='short' else cx
    self.files[name].extend(u.mem_read(ds*16+dx,result))
  elif ah==0x3e:
   name=self.handles.get(bx)
   if name is None:error=6
   elif self.fault=='close':error=6
   else:del self.handles[bx]
  elif ah==0x56:
   name=self.path(ds,dx);target=self.path(u.reg_read(UC_X86_REG_ES),u.reg_read(UC_X86_REG_DI))
   if self.fault=='install':error=5
   elif target in self.files:error=80
   elif name not in self.files:error=2
   else:self.files[target]=self.files.pop(name)
  elif ah==0x41:
   name=self.path(ds,dx)
   if name not in self.files:error=2
   else:del self.files[name]
  self.fs_calls.append({'ah':ah,'path':name,'error':error,'tx':bytes(self.tx).hex()})
  self.events.append(('DOS',ah,error,'OWNED.BIN' in self.files))
  u.reg_write(UC_X86_REG_AX,error or result)
  flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,(flags|1) if error else flags&~1)
 def output_port(self,u,port,size,value,data):
  is_data=port==self.get('uart_port_thr') and not self.lcr&0x80
  super().output_port(u,port,size,value,data)
  if port==0x20 and value&0x20:self.irq_in_service=False
  if not is_data:return
  value&=255;self.events.append(('TX',value,'OWNED.BIN' in self.files))
  if not self.peer_enabled:return
  if self.peer_state==0 and value==0x43:
   if self.blocks:
    self.offer_block();self.peer_state=1
   else:self.rx.append(4);self.peer_state=2
  elif self.peer_state==1 and value==6:
   self.block_index+=1
   if self.block_index<len(self.blocks):self.offer_block()
   else:self.rx.append(4);self.peer_state=2
  elif self.peer_state==2 and value==0x15:self.rx.append(4);self.peer_state=3
  elif self.peer_state==3 and value==6:self.peer_state=4
 def offer_block(self):
  data=self.blocks[self.block_index];assert len(data) in (128,1024);number=(self.block_index+1)&255
  self.rx.extend(bytes([1 if len(data)==128 else 2,number,255-number])+data+binascii.crc_hqx(data,0).to_bytes(2,'big'))
 def receive(self):
  self.waiting_ui=True;self.call('terminal_transfer_start');self.call('terminal_transfer_poll',limit=6000000)
  assert not self.get('terminal_transfer_active') and not self.get('terminal_transfer_pending')
  for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert self.uc.reg_read(reg)==want,('Transfer owner ABI',reg)
 def storage(self):return struct.unpack('<8H',self.uc.mem_read(self.symbols['_transfer_download_result'],16))

class SlowDrain(LiveTransfer):
 """300-baud-scale hardware pacing; prompt Escape proves drain completed."""
 def __init__(self):
  self.ready_after_reads=0
  super().__init__(peer=False)
 def input_port(self,u,port,size,data):
  if port==self.get('uart_port_lsr'):
   ready=self.tick_reads>=self.ready_after_reads
   return (0x60 if ready else 0)|(1 if self.rx else 0)
  return super().input_port(u,port,size,data)
 def output_port(self,u,port,size,value,data):
  wire=port==self.get('uart_port_thr') and not self.lcr&0x80
  super().output_port(u,port,size,value,data)
  if wire:self.ready_after_reads=self.tick_reads+5
 def interrupt(self,u,number,data):
  if number==0x10 and u.reg_read(UC_X86_REG_AX)>>8==2 and self.waiting_ui and not self.filename_sent and u.reg_read(UC_X86_REG_DX)>>8==24:
   self.filename_sent=True
   self.keys.append(0x011b)
  return super().interrupt(u,number,data)

def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();groups=[]
 def check(name,fn):
  try:n=fn()
  except AssertionError as error:
   groups.append({'case':name,'passed':False,'error':str(error)})
   (ROOT/'build/terminal/terminal-transfer-live-checks.json').write_text(json.dumps({'passed':False,'binary_sha256':digest,'cases':groups,'scope':'Actual linked transfer instructions; hardware/DOSkernel only modeled.'},indent=2)+'\n')
   raise
  groups.append({'case':name,'inputs':n,'passed':True});print(name,'PASS',n,flush=True)
 def rejects():
  for state in (1,2,3,4,5,7,8,9):
   m=LiveTransfer();m.put('connection_state',state);m.receive();assert not m.fs_calls and not m.tx
  m=LiveTransfer();m.put('uart_software_flow',1);m.receive();assert not m.fs_calls and not m.tx
  return 9
 check('SOFT-and-modem-owned-connections-reject-before-stage',rejects)
 def success():
  for data in (bytes(range(128)),bytes(range(256))*4,(bytes(range(128)),bytes(range(256))*4,bytes(range(128))),b''):
   m=LiveTransfer(data=data);m.receive()
   assert m.get('terminal_transfer_fault')==0 and m.storage()[0]==3,(m.storage(),m.get('terminal_transfer_fault'),m.events)
   assert bytes(m.files['OWNED.BIN'])==m.payload and 'PCRX.$$$' not in m.files and not m.handles
   ack=[e for e in m.events if e[:2]==('TX',6)]
   assert len(ack)==len(m.blocks)+1 and ack[-1][2]
   rename=next(i for i,e in enumerate(m.events) if e[:2]==('DOS',0x56));final=next(i for i,e in enumerate(m.events) if e[:2]==('TX',6) and e[2]);assert final>rename
   assert all(bytes.fromhex(c['tx']).count(b'\x06')<=len(m.blocks) for c in m.fs_calls),'FinalACK precedes a file syscall'
   closed=next(i for i,e in enumerate(m.events) if e[:2]==('DOS',0x3e));assert closed<rename<final
   assert m.get('terminal_transfer_eot_deferred')==1
  return 4
 check('actual-native-CRC128-1024-mixed-and-empty-EOT-ACK-after-checked-install',success)
 def stalls():
  n=0
  for initial in (0,0xfff0,DAY-20):
   for reason in ('cts','thre'):
    m=LiveTransfer();m.tick=initial
    if reason=='cts':m.put('uart_hardware_flow',1);m.cts=False;m.enqueue(b'R')
    else:m.thre=False
    m.receive();assert m.get('terminal_transfer_fault')==6 and not m.tx and not m.fs_calls
    assert 36<=(m.tick-initial)%DAY<45,(reason,m.tick,initial);n+=1
  return n
 check('physical-CTS-THRE-drain-bound-lowword-wrap-and-midnight',stalls)
 def slow_progress():
  # Five reads/byte and eight reads/tick =0.625ticks/byte, ~29.1bytes/s.
  # This is a legitimate300baud stream plus foreground-polling delay. The
  # entire128byte drain takes80ticks; every physical acceptance must refresh
  # the no-progress deadline. CTS stays ready. No protocol/file stage starts.
  observations=[]
  for initial in (0,0xfff0,DAY-20):
   m=SlowDrain();m.tick=initial;m.put('terminal_baud_low',300);m.put('terminal_baud_high',0)
   queued=bytes(range(1,129));m.enqueue(queued);m.receive()
   elapsed=(m.tick-initial)%DAY
   passed=(bytes(m.tx)==queued and m.get('terminal_tx_count')==0 and
    m.get('terminal_macro_tx_epoch')==128 and 75<=elapsed<100 and
    m.filename_sent and m.get('terminal_transfer_fault')==2 and
    not m.fs_calls and not m.files and not m.handles)
   observations.append({'initial_tick':initial,'sent':len(m.tx),
    'remaining':m.get('terminal_tx_count'),'elapsed_ticks':elapsed,
    'fault':m.get('terminal_transfer_fault'),'prompt_reached':m.filename_sent,
    'passed':bool(passed)})
  assert all(o['passed'] for o in observations),observations
  return 3
 check('progressing300baud128byte-drain-exceeds36ticks-with-wrap-midnight',slow_progress)
 def outer():
  n=0
  for initial in (0,0xfff0,DAY-20):
   for reason,want in [('cts',6),('thre',6),('escape',2),('altx',2),('carrier',4)]:
    m=LiveTransfer(after_create=reason);m.tick=initial;m.receive()
    assert m.get('terminal_transfer_fault')==want,(reason,m.get('terminal_transfer_fault'),m.events)
    assert not m.tx and not m.files and not m.handles and m.storage()[0]==4,(reason,m.storage(),m.files)
    assert bytes(m.uc.mem_read(m.symbols['session_context'],10))==bytes(10),'Native setjmp was reached; outer-unwind test invalid'
    assert bool(m.get('terminal_quit'))==(reason=='altx');n+=1
  return n
 check('outer-context-cancel-carrier-and-native-TX-stall-before-native-setjmp',outer)
 def deadlines():
  for initial in (0,0xfff0,DAY-20):
   m=LiveTransfer(peer=False);m.tick=initial;m.receive()
   assert m.get('terminal_transfer_fault')==3 and not m.files and not m.handles
   assert 540<=(m.tick-initial)%DAY<650,((m.tick-initial)%DAY,m.get('terminal_transfer_fault'))
  return 3
 check('whole-owner-progress-timeout-full-BIOS-ticks-wrap-midnight',deadlines)
 def faults():
  for fault,first in [('short',7),('write',7),('close',8),('install',9)]:
   m=LiveTransfer(fault=fault);m.receive();state=m.storage()
   assert m.get('terminal_transfer_fault')==7 and state[1]==first,(fault,state,m.events)
   assert 'OWNED.BIN' not in m.files
   assert bytes(m.tx).count(b'\x06')==1 and not any(e[:2]==('TX',6) and e[2] for e in m.events),(fault,m.events)
   if fault=='close':assert state[7] and 'PCRX.$$$' in m.files and sum(c['ah']==0x3e for c in m.fs_calls)==1
   if fault=='install':assert 'PCRX.$$$' in m.files and not m.handles
  return 4
 check('DOS-shortwrite-write-close-install-faults-never-publish-final-ACK',faults)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest,'Frozen binary changed during tests'
 proof={'passed':True,'binary_sha256':digest,'inputs':sum(g['inputs'] for g in groups),'cases':groups,'scope':'Actual linked transfer owner/native receiver/UI/storage/UARTISR; hardware FIFO/ports/BIOS ticks+keys/video and DOS filesystem kernel only modeled. No product callback patched, skipped or substituted.','limitations':['Synthetic CRC128/1024/mixed/empty peers; not full protocol or actual DOS/physical modem proof.','Synthetic clock advances one BIOSdaytick per eight clock reads; IRQ and busy-loop timing is modeled, and deadlines are checked using actual full daytick arithmetic.']}
 (ROOT/'build/terminal/terminal-transfer-live-checks.json').write_text(json.dumps(proof,indent=2)+'\n');print('Live transfer:',len(groups),'groups,',proof['inputs'],'inputs PASS')
if __name__=='__main__':main()
