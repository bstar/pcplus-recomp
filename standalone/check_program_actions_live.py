#!/usr/bin/env python3
"""Actual linked live PROGRAM, C policy, process, video, keyboard and UART code.

Only DOSkernel/BIOS/UART hardware boundaries are modeled. Product callbacks
execute normally; none is substituted, patched, skipped or manually completed.
"""
import hashlib,json,struct
from unicorn.x86_const import *
from check_meta_actions_live import Meta,DAY,ROOT,BINARY
from check_process import Kernel
class LiveProgram(Meta):
 def __init__(self,keys=(),*,exec_error=0,resize_error=0,child_status=37,mutate_child=True):
  super().__init__(keys)
  self.calls=[];self.children=[];self.resize_error=resize_error;self.exec_error=exec_error;self.child_status=child_status;self.clobber=True
  self.mode=3;self.columns=80;self.page=0;self.cursor=0x0611;self.shape=0x060f;self.video_calls=[]
  self.lcr=3;self.mcr=1;self.ier=0;self.dll=0x44;self.dlm=0x22;self.pic=0xef;self.temt=True;self.overrun=False
  self.port_writes=[];self.data_reads=0;self.at_exec=[];self.mutate_child=mutate_child;self.prompt_key_sent=False
  self.vector=self.get('terminal_irq_vector');self.old_vector=(0x5678,0x1234)
  self.uc.mem_write(4*self.vector,struct.pack('<HH',*self.old_vector))
  assert self.call('terminal_program_initialize',ax=0xff0)==0xff0
  self.environment(b'COMSPEC=Z:\\COMMAND.COM\0PATH=Z:\\\0\0')
  # Actual recovered startup snapshot, divisor/format setup and ISR installer.
  self.call('uart_save_hardware_state');self.call('uart_set_baud_divisor',[38400,0]);self.call('uart_set_line_control',[0,8,1])
  self.mcr=0xb;self.ier=1
  self.call('uart_install_interrupt',[self.vector])
  self.parent_vector=struct.unpack('<HH',self.uc.mem_read(4*self.vector,4))
  self.baseline={name:self.get(name,1 if name.startswith('uart_saved_') else 2) for name in ['uart_saved_pic','uart_saved_lcr','uart_saved_mcr','uart_saved_ier','uart_saved_dll','uart_saved_dlm','uart_previous_irq_offset','uart_previous_irq_segment']}
  self.uc.reg_write(UC_X86_REG_DX,17);self.call('screen_set_cursor',ax=6)
  self.logical_names=['screen_cursor_row','screen_cursor_column','screen_video_offset','screen_attribute_offset','csi_wrap_pending','attributes_current','cursor_state_value_1d20']
  self.logical_before={name:self.get(name) for name in self.logical_names}
  self.original_screen=bytes((33+i%90 if i%2==0 else 1+(i//160)%7) for i in range(4000));self.uc.mem_write(0xb8000,self.original_screen)
  self.data_reads=0;self.calls.clear();self.port_writes.clear()
 def environment(self,data,segment=0x7000):
  self.uc.mem_write(self.get('process_psp')*16+0x2c,struct.pack('<H',segment))
  if segment:
   self.uc.mem_write((segment-1)*16,b'M\0\0'+struct.pack('<H',(len(data)+15)//16));self.uc.mem_write(segment*16,data)
 def vector_value(self):return struct.unpack('<HH',self.uc.mem_read(self.vector*4,4))
 def input_port(self,u,port,size,data):
  if port==0x21:return self.pic
  if port==self.get('uart_port_lcr'):return self.lcr
  if port==self.get('uart_port_mcr'):return self.mcr
  if port==self.get('uart_port_lsr'):return (0x20 if self.thre else 0)|(0x40 if self.temt else 0)|(1 if self.rx else 0)|(2 if self.overrun else 0)
  if port==self.get('uart_port_ier'):return self.dlm if self.lcr&0x80 else self.ier
  if port==self.get('uart_port_rbr'):
   if self.lcr&0x80:return self.dll
   self.data_reads+=1
   return self.rx.popleft() if self.rx else 0
  return super().input_port(u,port,size,data)
 def output_port(self,u,port,size,value,data):
  value&=255;self.port_writes.append((port,value))
  if port==0x21:self.pic=value;return
  if port==self.get('uart_port_lcr'):self.lcr=value;return
  if port==self.get('uart_port_mcr'):self.mcr=value;return
  if port==self.get('uart_port_ier'):
   if self.lcr&0x80:self.dlm=value
   else:self.ier=value
   return
  if port==self.get('uart_port_thr') and self.lcr&0x80:self.dll=value;return
  super().output_port(u,port,size,value,data)
 def set_carry(self,value):Kernel.set_carry(self,value)
 def interrupt(self,u,number,data):
  if number==0x16:
   if self.get('terminal_program_active'):
    assert self.pic&0x10 or self.ier==0 or not self.mcr&8,'Child UART interrupts remain live during returnprompt'
   return super().interrupt(u,number,data)
  if number==0x10:
   ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;self.video_calls.append(ah)
   if ah==15:
    u.reg_write(UC_X86_REG_AX,self.columns*256+self.mode);u.reg_write(UC_X86_REG_BX,(u.reg_read(UC_X86_REG_BX)&255)|(self.page<<8));return
   if ah==3:u.reg_write(UC_X86_REG_DX,self.cursor);u.reg_write(UC_X86_REG_CX,self.shape);return
   if ah==0:
    self.mode=ax&255;self.columns=80;self.page=0;self.cursor=0;self.shape=0x0607;u.mem_write(0xb8000,b' \x07'*2000);return
   if ah==1:self.shape=u.reg_read(UC_X86_REG_CX);return
   if ah==2:self.cursor=u.reg_read(UC_X86_REG_DX);return
   if ah==14:
    if self.get('terminal_program_active'):
     assert self.pic&0x10 and self.ier==0 and not self.lcr&0x80 and not self.mcr&2,'Child UART interrupts remain live before returnprompt'
     assert self.vector_value()==self.old_vector,'Child vector remains installed during returnprompt'
     if not self.prompt_key_sent:self.keys.append(0x1c0d);self.prompt_key_sent=True
    row,col=self.cursor>>8,self.cursor&255
    if ax&255==13:col=0
    elif ax&255==10:row+=1
    else:
     if row<25 and col<80:u.mem_write(0xb8000+(row*80+col)*2,bytes([ax&255,7]))
     col+=1
    if col>=80:col=0;row+=1
    self.cursor=(min(row,24)<<8)|col;return
   raise AssertionError(('Unexpected BIOSvideo',hex(ax)))
  assert number==0x21,number
  ax=u.reg_read(UC_X86_REG_AX)
  if ax>>8==0x35:
   off,seg=struct.unpack('<HH',u.mem_read((ax&255)*4,4));u.reg_write(UC_X86_REG_BX,off);u.reg_write(UC_X86_REG_ES,seg);self.calls.append(0x35);return
  if ax>>8==0x25:
   u.mem_write((ax&255)*4,struct.pack('<HH',u.reg_read(UC_X86_REG_DX),u.reg_read(UC_X86_REG_DS)));self.calls.append(0x25);return
  if ax==0x4b00:
   assert self.vector_value()==self.old_vector,'Parent UART ISR was not released beforeEXEC'
   assert self.ier==0 and self.mcr&1 and not self.mcr&2 and self.pic&0x10
   assert self.get('terminal_program_active')==1 and not self.get('terminal_program_pending')
   self.at_exec.append({'irq_released':True,'DTR_preserved':True,'RTS_lowered':True})
   Kernel.interrupt(self,u,number,data)
   if self.mutate_child and not self.exec_error:
    self.lcr=0x9b;self.mcr=0xb;self.ier=0xff;self.dll=0x77;self.dlm=0x88;self.pic&=~0x10
    u.mem_write(self.vector*4,struct.pack('<HH',0xabcd,0x4567))
    self.mode=0x13;self.page=2;self.cursor=0x1401;self.shape=0x2020;u.mem_write(0xb8000,b'\xff'*4000)
    self.rx.append(ord('R')) # hardware RBR pending across restore; no ISR active.
   return
  return Kernel.interrupt(self,u,number,data)
 def queue(self,command=b'ECHO ^M~^@ LITERAL',index=0):
  self.record(index,command,1);return self.start(index)
 def safe(self,tick=None):
  if tick is not None:self.tick=tick%DAY
  answer=self.call('terminal_program_poll',limit=3000000)
  for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert self.uc.reg_read(reg)==want
  return answer
 def restored(self):
  assert bytes(self.uc.mem_read(0xb8000,4000))==self.original_screen
  assert (self.mode,self.columns,self.page,self.cursor,self.shape)==(3,80,0,0x0611,0x060f)
  assert {name:self.get(name) for name in self.logical_names}==self.logical_before
  assert self.vector_value()==self.parent_vector
  assert (self.lcr,self.mcr,self.ier,self.dll,self.dlm)==(3,0xb,1,3,0)
  assert not self.pic&0x10
  assert {name:self.get(name,1 if name.startswith('uart_saved_') else 2) for name in self.baseline}==self.baseline

def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();cases=[]
 def check(name,fn):n=fn();cases.append({'case':name,'inputs':n,'passed':True});print(name,'passed',n,flush=True)
 def safepoint():
  for index in range(10):
   m=LiveProgram();m.record(index,b'ECHO ^M~^@ LITERAL',1);m.keys.append((0x78+index)<<8);m.poll()
   for _ in range(4):m.poll()
   assert not m.children and 0x4a not in m.calls and m.get('terminal_program_pending')
   assert m.call('ansi_next_byte')==0xffff and not m.children
   m.safe();assert m.children==[{'path':b'Z:\\COMMAND.COM','tail':b' /c ECHO ^M~^@ LITERAL'}]
   assert struct.unpack('<4H',m.uc.mem_read(m.symbols['terminal_program_result'],8))[:3]==(0,0,37)
   assert not m.get('terminal_program_pending') and not m.get('terminal_program_active')
   assert m.get('terminal_program_status')==4
   m.restored();assert m.data_reads==0 and bytes(m.rx)==b'R'
   # The real recovered IRQ consumes the pending hardwarebyte only afterward.
   m.call('uart_receive_interrupt',irq=True);assert m.call('uart_receive_byte')==ord('R')
  return 10
 check('allten-PROGRAM-indices-defer-DOS-to-safe-poll-literal-tail-realrestore-noRBRdiscard',safepoint)
 def flow():
  for initial in (0,0xfffb,DAY-5):
   m=LiveProgram([0x1c0d]);m.tick=initial;m.put('uart_software_flow',1);m.enqueue(b'REPLY');assert m.queue(b'OWNED.COM')==0
   m.safe();assert not m.children and not m.tx
   for _ in range(5):m.poll()
   assert bytes(m.tx)==b'REPLY';m.safe();assert bytes(m.tx)==b'REPLY\x13' and not m.children
   m.temt=False;m.safe(initial+9);assert not m.children
   m.temt=True;m.safe(initial+10);assert len(m.children)==1 and m.get('uart_flow_pending',1)==0x11
   m.poll();assert bytes(m.tx)==b'REPLY\x13\x11';m.restored()
  return 3
 check('SOFT-XOFF-physical-TEMT-drain-fulltick-wrap-and-owned-XON-resume',flow)
 def timeouts():
  for initial in (0,0xfff0,DAY-20):
   m=LiveProgram();m.tick=initial;m.temt=False;assert m.queue()==0
   m.safe(initial+35);assert m.get('terminal_program_pending') and not m.children
   m.safe(initial+36);assert not m.get('terminal_program_pending') and m.get('terminal_program_status')==8 and not m.children
   assert not m.get('terminal_quit')
  m=LiveProgram();m.enqueue(b'R'*80);assert m.queue()==0
  for tick in range(80):m.poll(tick);m.safe(tick)
  # No complete ring may false-timeout merely because cumulativedrain exceeds36.
  assert len(m.children)==1 and not m.get('terminal_program_pending') and not m.get('terminal_quit')
  return 4
 check('36tick-blocked-TEMT-deadline-midnight-and-long-reply-progress',timeouts)
 def cancel():
  for key in (0x011b,0x2d00,0x2300,0x2000):
   m=LiveProgram();m.put('uart_software_flow',1);assert m.queue()==0;m.safe();assert m.tx==[0x13]
   m.call('terminal_defer_key',ax=ord('q'));m.keys.append(key);m.poll()
   assert not m.get('terminal_program_pending') and not m.children
   m.call('terminal_take_deferred_key');assert m.uc.reg_read(UC_X86_REG_EFLAGS)&1
   m.safe();assert not m.children
  # Carrier loss uses the actual connectionpoll/DCD transition, notprivateflags.
  m=LiveProgram();m.put('connection_enabled',1,1);m.put('connection_state',6);m.call('terminal_connection_poll')
  assert m.queue()==0;m.carrier=False;m.poll();assert not m.get('terminal_program_pending') and m.get('connection_status')==6 and not m.children
  return 5
 check('pending-Escape-AltX-AltH-AltD-FIFO-cancel-and-real-carrierloss',cancel)
 def failures():
  for error in (2,8):
   m=LiveProgram([0x1c0d],exec_error=error,mutate_child=False);assert m.queue()==0;m.safe()
   assert m.get('terminal_program_status')==5 and struct.unpack('<4H',m.uc.mem_read(m.symbols['terminal_program_result'],8))[1]==error
   m.restored();assert not m.get('terminal_quit')
  for mode,cols,page in [(7,80,0),(3,40,0),(3,80,1)]:
   m=LiveProgram();m.mode=mode;m.columns=cols;m.page=page;assert m.queue()==0;m.safe()
   assert m.get('terminal_program_status')==9 and not m.children and not m.get('terminal_program_pending')
  m=LiveProgram();assert m.queue()==0;m.put('uart_rx_dropped',1);m.safe();assert not m.children and m.get('terminal_quit') and m.get('terminal_exit_code')==6
  return 6
 check('EXEC-error-recovery-unsupported-view-before-child-and-recordedRXoverflow',failures)
 def prechild_failures():
  for error in (7,8,9):
   m=LiveProgram(resize_error=error);assert m.queue()==0;m.safe()
   assert m.get('terminal_program_status')==5 and not m.children
   assert struct.unpack('<4H',m.uc.mem_read(m.symbols['terminal_program_result'],8))[:2]==(2,error)
   m.restored();assert m.data_reads==0 and not m.get('terminal_quit')
  m=LiveProgram();m.environment(b'BAD ENV WITHOUT TERMINATOR')
  # Make every byte of the owned span nonzero to prove bounded rejection.
  m.uc.mem_write(0x70000,b'X'*32);assert m.queue()==0;m.safe()
  assert m.get('terminal_program_status')==5 and not m.children and 0x4a not in m.calls
  assert m.get('terminal_program_result')==5;m.restored()
  m=LiveProgram();m.environment(b'',segment=0);assert m.queue()==0;m.safe()
  assert m.children==[{'path':b'COMMAND.COM','tail':b' /c ECHO ^M~^@ LITERAL'}]
  m.restored();return 5
 check('resize-environment-rejection-no-child-and-empty-environment-command-fallback',prechild_failures)

 def ownership_edges():
  # Driver-owned watermark XOFF must not be released by a PROGRAM which did
  # not create it. Establish the watermark through actual received IRQ bytes.
  m=LiveProgram(mutate_child=False);m.put('uart_software_flow',1)
  m.receive_irq(b'R'*3073);m.poll()
  assert m.get('uart_xoff_sent',1)==1 and bytes(m.tx)==b'\x13'
  assert m.queue()==0;m.safe();assert len(m.children)==1
  assert m.get('uart_xoff_sent',1)==1 and m.get('uart_flow_pending',1)==0
  # This launch owns XOFF, but cannot send XON while buffered input >128.
  m=LiveProgram(mutate_child=False);m.put('uart_software_flow',1);assert m.queue()==0;m.safe()
  m.receive_irq(b'R'*129);m.safe();assert len(m.children)==1
  assert m.get('uart_xoff_sent',1)==1 and m.get('uart_flow_pending',1)==0
  # A real postchild LSR overrun increments loss evidence without RBR reads.
  m=LiveProgram();m.overrun=True;assert m.queue()==0;m.safe()
  assert m.get('uart_rx_dropped')==1 and m.data_reads==0 and bytes(m.rx)==b'R'
  m=LiveProgram();assert m.queue()==0
  # Startup baseline is restored by the actual normal shutdown routines too.
  m.safe();m.call('uart_restore_interrupt',[m.vector]);m.call('uart_restore_hardware_state')
  assert m.vector_value()==m.old_vector
  assert (m.pic,m.lcr,m.mcr,m.ier,m.dll,m.dlm)==tuple(m.baseline[n] for n in ('uart_saved_pic','uart_saved_lcr','uart_saved_mcr','uart_saved_ier','uart_saved_dll','uart_saved_dlm'))
  # Queued normal keys survive successful child handoff, then drain in order.
  m=LiveProgram([0x1e61,0x3062]);assert m.queue()==0;m.poll();m.poll();m.safe()
  for _ in range(5):m.poll()
  assert bytes(m.tx)==b'ab' and not m.keys and len(m.children)==1
  for command in (b'',b'A\rB',b'A\nB',b'X'*52):
   m=LiveProgram();m.record(0,command,1,terminated=len(command)<52);assert m.start()==3
   assert not m.get('terminal_program_pending') and not m.children and not m.tx
  return 9
 check('driver-vs-program-flowownership-postchild-overrun-startupbaseline-FIFO-and-invalidcommands',ownership_edges)
 def shutdown_flow():
  total=0
  # Real AltX cancels the pending launch after its physical XOFF. Shutdown
  # then has to release the peer despite quit, CTS-low and peer-XOFF flags.
  for initial in (0,0xfff0,DAY-20):
   m=LiveProgram();m.tick=initial;m.put('uart_software_flow',1);assert m.queue()==0;m.safe()
   assert bytes(m.tx)==b'\x13'
   m.keys.append(0x2d00);m.poll();assert m.get('terminal_quit') and not m.get('terminal_program_pending')
   m.cts=False;m.put('uart_hardware_flow',1);m.put('uart_tx_paused',1)
   m.advance_ticks=True;m.call('terminal_release_flow')
   assert bytes(m.tx)==b'\x13\x11' and not m.get('uart_flow_pending',1) and not m.get('uart_xoff_sent',1)
   assert not m.get('terminal_cleanup_flow_failed') and not m.get('terminal_exit_code')
   assert not m.children and m.data_reads==0;total+=1
  # Owned pause and already-queued XON each release once, including when
  # pending input remains above the ordinary flow watermark.
  for xoff,pending in ((1,0),(0,0x11),(1,0x13)):
   m=LiveProgram();m.put('uart_software_flow',1);m.put('uart_xoff_sent',xoff,1);m.put('uart_flow_pending',pending,1)
   m.put('uart_rx_count',500);m.advance_ticks=True;m.call('terminal_release_flow')
   assert bytes(m.tx)==b'\x11' and not m.get('terminal_cleanup_flow_failed');total+=1
  for initial in (0,0xfff0,DAY-20):
   for prior in (0,6):
    m=LiveProgram();m.tick=initial;m.put('uart_software_flow',1);m.put('uart_xoff_sent',1,1)
    m.put('terminal_exit_code',prior);m.thre=False;m.advance_ticks=True
    m.call('terminal_release_flow',limit=300000)
    assert m.get('terminal_cleanup_flow_failed')==1 and m.get('terminal_exit_code')==(prior or 11)
    assert bytes(m.tx)==b'' and m.get('uart_flow_pending',1)==0x11
    assert 36<=(m.tick-initial)%DAY<=38 and m.data_reads==0;total+=1
  for soft,xoff,pending in ((0,1,0),(1,0,0)):
   m=LiveProgram();m.put('uart_software_flow',soft);m.put('uart_xoff_sent',xoff,1);m.put('uart_flow_pending',pending,1)
   m.call('terminal_release_flow');assert not m.tx and not m.tick_reads;total+=1
  return total
 check('actual-AltX-shutdown-XON-independent-CTS-peerpause-and-bounded-fulltick-timeout',shutdown_flow)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest,'Binary changed duringlivePROGRAM tests'
 proof={'passed':True,'binary_sha256':digest,'inputs':sum(c['inputs'] for c in cases),'cases':cases,'scope':'Actual linked maintained PROGRAMscheduler, C COMSPEC policy, processbackend, snapshots, keyboard/UART/IRQ/format/vector restoration. OnlyDOSkernel/BIOS/hardware boundaries modeled; no productcallbacks skipped.','limitations':['Kernel/BIOS/UART model, not physicaladapter or realDOSchild proof; rootseparate actualDOSdiagnostics coverkernel/child behavior.','NONEflow cannot guarantee remotepause; modeledLSR overrun boundary is explicit.']}
 (ROOT/'build/terminal/program-actions-live-checks.json').write_text(json.dumps(proof,indent=2)+'\n');print('Live PROGRAM:',len(cases),'groups,',proof['inputs'],'inputs passed')
if __name__=='__main__':main()
