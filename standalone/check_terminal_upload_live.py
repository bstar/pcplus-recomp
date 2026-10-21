#!/usr/bin/env python3
"""Live upload: actual native sender/UARTISR/UI/read-only DOS ownership.

Only BIOS/UART/ticks and DOS filesystem syscalls are modeled. The independent
peer parses physical TX bytes; ACK/NAK arrives through the actual hardware ISR.
No product callback is patched, skipped, substituted or manually returned from.
"""
import binascii,hashlib,json,struct
from unicorn.x86_const import *
from check_terminal_transfer_live import LiveTransfer,DAY,ROOT,BINARY

class LiveUpload(LiveTransfer):
 def __init__(self,data=b'ABC',*,crc=True,reject=0,silent=False,fault=None,after_open=None):
  self.source=bytes(data);self.crc_mode=crc;self.reject=reject;self.silent=silent;self.upload_fault=fault;self.after_open=after_open
  self.packet=bytearray();self.packet_size=0;self.frames=[];self.accepted=0;self.peer_offset=0;self.eots=0;self.initial_offered=False
  self.position=0;self.rejected=0;self.readonly_calls=[]
  super().__init__(peer=False)
  self.filename=b'SEND.BIN';self.files={'SEND.BIN':bytearray(data)};self.handles={}
  self.fs_calls=[];self.events=[];self.tick=0;self.tick_reads=0
  assert self.call('_terminal_upload_initialize')==0
 def interrupt(self,u,number,data):
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8
  if number!=0x21 or ah not in (0x43,0x3d,0x42,0x3f,0x3e):return super().interrupt(u,number,data)
  ds=u.reg_read(UC_X86_REG_DS);dx=u.reg_read(UC_X86_REG_DX);bx=u.reg_read(UC_X86_REG_BX);cx=u.reg_read(UC_X86_REG_CX)
  error=0;result=0
  if ah==0x43:
   path=self.path(ds,dx)
   if path not in self.files:error=2
   else:u.reg_write(UC_X86_REG_CX,0)
  elif ah==0x3d:
   assert ax&3==0,'Source opened with write access'
   path=self.path(ds,dx)
   if self.upload_fault=='open':error=5
   elif path not in self.files:error=2
   else:
    result=5;self.handles[5]=path;self.position=0
    if self.after_open in ('escape','altx'):self.keys.append(0x011b if self.after_open=='escape' else 0x2d00)
    elif self.after_open=='cts':self.cts=False;self.put('uart_hardware_flow',1)
    elif self.after_open=='thre':self.thre=False
    elif self.after_open=='carrier':self.carrier=False
  elif ah==0x42:
   if self.upload_fault=='seek':error=5
   elif bx not in self.handles:error=6
   elif ax&255==2:
    self.position=len(self.source);result=self.position&65535;u.reg_write(UC_X86_REG_DX,self.position>>16)
   else:
    assert ax&255==0 and cx==dx==0
    self.position=0;result=0;u.reg_write(UC_X86_REG_DX,0)
    if not self.initial_offered and self.after_open not in ('escape','altx','carrier'):
     self.rx.append(0x43 if self.crc_mode else 0x15);self.initial_offered=True
  elif ah==0x3f:
   if bx not in self.handles:error=6
   elif self.upload_fault=='read':error=5
   else:
    result=min(cx,len(self.source)-self.position)
    if self.upload_fault=='short' and result>1:result=1
    elif self.upload_fault=='earlyEOF':result=0
    u.mem_write(ds*16+dx,self.source[self.position:self.position+result]);self.position+=result
  elif ah==0x3e:
   if bx not in self.handles:error=6
   elif self.upload_fault=='close':error=6
   else:del self.handles[bx]
  self.fs_calls.append({'ah':ah,'error':error,'count':result,'tx_bytes':len(self.tx)})
  self.events.append(('DOS',ah,error))
  u.reg_write(UC_X86_REG_AX,error or result);flags=u.reg_read(UC_X86_REG_EFLAGS);u.reg_write(UC_X86_REG_EFLAGS,flags|1 if error else flags&~1)
 def output_port(self,u,port,size,value,data):
  wire=port==self.get('uart_port_thr') and not self.lcr&0x80
  super().output_port(u,port,size,value,data)
  if not wire:return
  value&=255
  if self.packet:
   self.packet.append(value)
   if len(self.packet)==self.packet_size:self.finish_packet()
  elif value in (1,2):
   self.packet=bytearray([value]);self.packet_size=3+(128 if value==1 else 1024)+(2 if self.crc_mode else 1)
  elif value==4:
   self.eots+=1
   assert not self.handles,'EOT emitted before source close'
   state=self.upload_state();assert state['consumed']==len(self.source) and state['close_calls']==1,('Premature EOT',state)
   if not self.silent:self.rx.append(6)
  else:assert value==0x18,('Unexpected upload control',value)
 def finish_packet(self):
  frame=bytes(self.packet);self.packet=bytearray();size=128 if frame[0]==1 else 1024
  number=(self.accepted+1)&255
  assert frame[1]==number and frame[2]==255-number,('Sequence/complement',frame[:3],number)
  body=frame[3:3+size];want=self.source[self.peer_offset:self.peer_offset+size];want+=b'\x1a'*(size-len(want))
  assert body==want,('Binary/padding mismatch',self.peer_offset,size)
  trailer=binascii.crc_hqx(body,0).to_bytes(2,'big') if self.crc_mode else bytes([sum(body)&255])
  assert frame[3+size:]==trailer,'Checksum/CRC mismatch'
  self.frames.append({'size':size,'number':number,'sha256':hashlib.sha256(frame).hexdigest()})
  if self.silent:return
  if self.reject==-1 or self.rejected<self.reject:
   self.rejected+=1;self.rx.append(0x15)
  else:self.accepted+=1;self.peer_offset+=size;self.rx.append(6)
 def upload_state(self):
  raw=bytes(self.uc.mem_read(self.symbols['_upload_source_result'],92));words=struct.unpack_from('<10H',raw)
  return dict(zip(['state','first','dos','close_error','open','uncertain','discovery','binary','reads','close_calls'],words),size=struct.unpack_from('<I',raw,20)[0],consumed=struct.unpack_from('<I',raw,24)[0])
 def upload(self):
  self.waiting_ui=True;self.call('terminal_upload_start');self.call('terminal_transfer_poll',limit=60000000)
  assert not self.get('terminal_transfer_active') and not self.get('terminal_transfer_pending')
  assert bytes(self.files['SEND.BIN'])==self.source,'Read-only source changed'
  assert not any(c['ah'] in (0x40,0x41,0x56,0x5b) for c in self.fs_calls),'Source mutation syscall'
  for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_ES,0xb800)]:assert self.uc.reg_read(reg)==want,('Upload owner ABI',reg)

def main():
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();groups=[]
 def save(passed):
  (ROOT/'build/terminal/terminal-upload-live-checks.json').write_text(json.dumps({'passed':passed,'binary_sha256':digest,'inputs':sum(c.get('inputs',0) for c in groups),'cases':groups,'scope':'Actual linked upload owner/native sender/read-only storage/UI/UARTISR. Independent peer checks physical frame/padding/sequence/checksumCRC. Only hardware/BIOS and DOSkernel boundaries modeled.','limitations':['Synthetic peers and kernel, not physicalmodem or actualDOSproof; sourceguardchanges after frozenbinary are not implicitly tested.']},indent=2)+'\n')
 def check(name,fn):
  try:n=fn()
  except Exception as error:
   groups.append({'case':name,'passed':False,'error':str(error)});save(False);raise
  groups.append({'case':name,'inputs':n,'passed':True});print(name,'PASS',n,flush=True)
 def rejects():
  for state in (1,2,3,4,5,7,8,9):
   m=LiveUpload();m.put('connection_state',state);m.upload();assert not m.fs_calls and not m.tx
  m=LiveUpload();m.put('uart_software_flow',1);m.upload();assert not m.fs_calls and not m.tx
  return 9
 check('SOFT-and-modem-owned-state-reject-before-source-open',rejects)
 def binary():
  recipes=[(b'',True),(bytes(range(128)),True),(bytes(range(256))*4,True),(bytes(range(256))*4+b'\0\x1a\xff',True),(bytes(range(256))*44+b'LAST',True),(bytes(range(256))*257+b'LAST',True),(bytes(range(128)),False)]
  for data,crc in recipes:
   m=LiveUpload(data,crc=crc);m.upload();state=m.upload_state()
   assert m.get('terminal_transfer_fault')==0 and state['state']==5,(len(data),state,m.get('terminal_transfer_fault'))
   assert state['size']==state['consumed']==len(data) and not state['open'] and not m.handles
   assert m.get('terminal_upload_blocks_accepted')==m.accepted==len(m.frames) and m.eots==1
   assert m.get('terminal_upload_accepted_bytes',4)==m.peer_offset
   if len(data)>10240:assert state['reads']>=2
   if len(data)>65535:assert state['consumed']>65535
   if len(data)==1027:assert [f['size'] for f in m.frames]==[1024,128]
  return len(recipes)
 check('binary-empty-CRC-checksum-mixed-over10240-and-DWORD-over64K',binary)
 def retries():
  m=LiveUpload(bytes(range(128)),reject=1);m.upload()
  assert len(m.frames)==2 and m.frames[0]==m.frames[1] and m.accepted==1
  assert m.get('terminal_upload_blocks_accepted')==1 and not m.get('terminal_transfer_fault')
  class FrozenPacketClock(LiveUpload):
   def output_port(self,u,port,size,value,data):
    if port==self.get('uart_port_thr') and not self.lcr&0x80 and not self.tx and value&255 in (1,2):
     self.advance_ticks=False
    super().output_port(u,port,size,value,data)
  for data in (bytes(range(128)),bytes(range(256))*44):
   m=FrozenPacketClock(data,reject=-1)
   # Startup's quiet interval needs the BIOS clock. Freeze only after the
   # first physical packet begins to isolate the actual15-attempt native
   # boundary under immediate synthetic NAKs. Deadline tests advance time.
   m.upload()
   assert m.advance_ticks is False
   assert len(m.frames)==15 and not m.accepted and not m.get('terminal_upload_blocks_accepted')
   assert m.get('send_blocks_counted')==1 and m.get('terminal_transfer_fault')==3 and not m.eots
   assert m.get('terminal_upload_accepted_bytes',4)==0 and not m.handles
   assert m.upload_state()['close_calls']==1
  return 3
 check('NAK-retransmit-and15failed-native-count-not-maintained-accepted',retries)
 def faults():
  for fault,first in [('open',5),('seek',6),('read',7),('short',8),('earlyEOF',8),('close',9)]:
   m=LiveUpload(bytes(range(128)),fault=fault);m.upload();state=m.upload_state()
   assert m.get('terminal_transfer_fault')==7 and state['first']==first,(fault,state,m.get('terminal_transfer_fault'))
   assert not m.eots and state['close_calls']<2
   if fault=='close':assert state['uncertain'] and state['close_calls']==1
   else:assert not m.handles
  return 6
 check('read-only-open-seek-read-shrink-close-errors-no-EOT',faults)
 def outer():
  n=0
  for initial in (0,0xfff0,DAY-20):
   for why,want in [('escape',2),('altx',2),('carrier',4)]:
    m=LiveUpload(after_open=why);m.tick=initial;m.upload();state=m.upload_state()
    assert m.get('terminal_transfer_fault')==want and not m.tx and not m.handles,(why,state,m.events)
    assert bytes(m.uc.mem_read(m.symbols['send_checkpoint_buffer'],10))==bytes(10),'Cancellation occurred after native context'
    assert state['close_calls']==1 and not state['uncertain']
    n+=1
  return n
 check('outer-context-Escape-AltX-carrier-before-native-checkpoint',outer)
 def stalled():
  n=0
  for initial in (0,0xfff0,DAY-20):
   for why in ('cts','thre'):
    m=LiveUpload(after_open=why);m.tick=initial;m.upload()
    assert m.get('terminal_transfer_fault')==6 and not m.tx and not m.handles and not m.eots,(why,m.get('terminal_transfer_fault'))
    assert 36<=(m.tick-initial)%DAY<50,(why,initial,(m.tick-initial)%DAY)
    n+=1
  return n
 check('CTS-THRE-physical-TX-stall-midnight-bounded',stalled)
 def watchdog():
  for initial in (0,0xfff0,DAY-20):
   m=LiveUpload(bytes(range(128)),silent=True);m.tick=initial;m.upload()
   assert m.get('terminal_transfer_fault')==3 and not m.handles and not m.eots and not m.accepted
   assert 540<=(m.tick-initial)%DAY<650,((m.tick-initial)%DAY,m.upload_state())
  return 3
 check('no-ACK-whole-owner-watchdog-lowword-wrap-midnight',watchdog)
 def next_peer(m,data,*,fault=None,after_open=None):
  # Reset only the independent peer/file-fixture for a new quiescent session.
  # Never reinitialize application/backend state or discard pending UART bytes.
  assert not m.packet and not m.rx and not m.get('uart_rx_count')
  m.source=bytes(data);m.files['SEND.BIN']=bytearray(data)
  m.upload_fault=fault;m.after_open=after_open;m.filename_sent=False;m.initial_offered=False
  m.frames.clear();m.packet_size=0;m.accepted=0;m.peer_offset=0;m.eots=0;m.rejected=0
  m.tx.clear();m.fs_calls.clear();m.events.clear();m.keys.clear()
 def repeated():
  m=LiveUpload(b'FIRST')
  recipes=[(b'FIRST',None,None),(bytes(range(256))*5,None,None),
           (b'FAIL','read',None),(b'AFTER',None,None),
           (b'CANCEL',None,'escape'),(b'AGAIN',None,None)]
  for data,fault,why in recipes:
   next_peer(m,data,fault=fault,after_open=why);m.upload();state=m.upload_state()
   success=not fault and not why
   assert m.eots==int(success) and not m.handles,(fault,why,state,m.eots,m.handles)
   assert state['close_calls']==1 and sum(c['ah']==0x3e for c in m.fs_calls)==1
   if success:
    assert state['state']==5 and not state['first'] and state['consumed']==len(data)
    assert not m.get('terminal_transfer_fault') and m.get('terminal_upload_blocks_accepted')==m.accepted
    assert m.get('terminal_upload_accepted_bytes',4)==m.peer_offset
   else:
    assert state['state']==6 and m.get('terminal_transfer_fault')==(7 if fault else 2)
  return len(recipes)
 check('same-instance-success-size-change-read-failure-success-Escape-success-no-reinitialize',repeated)
 def unresolved():
  class SeekThenCloseFailure(LiveUpload):
   def interrupt(self,u,number,data):
    failed_seek=number==0x21 and u.reg_read(UC_X86_REG_AX)==0x4202 and self.upload_fault=='seek'
    super().interrupt(u,number,data)
    if failed_seek:self.upload_fault='close'
  class ReadThenCloseFailure(LiveUpload):
   def interrupt(self,u,number,data):
    failed_read=number==0x21 and u.reg_read(UC_X86_REG_AX)>>8==0x3f and self.upload_fault=='read'
    super().interrupt(u,number,data)
    if failed_read:self.upload_fault='close'
  for cls,fault,first in [(LiveUpload,'close',9),(SeekThenCloseFailure,'seek',6),(ReadThenCloseFailure,'read',7)]:
   m=cls(bytes(range(128)),fault=fault);m.upload();state=m.upload_state()
   assert state['state']==8 and state['first']==first and state['uncertain'] and not state['open']
   assert state['close_error']==6 and state['close_calls']==1 and not m.eots
   assert m.get('terminal_transfer_cleanup_status')==11
   assert sum(c['ah']==0x3e for c in m.fs_calls)==1
   before=bytes(m.uc.mem_read(m.symbols['_upload_source_result'],92));handles=dict(m.handles)
   # The generic kernel model retains a handle on failed close. Real DOS may
   # already have closed it: unresolved ownership MUST NOT probe/retry either.
   next_peer(m,m.source);m.upload()
   assert not m.fs_calls and not m.tx and not m.eots
   assert m.handles==handles and bytes(m.uc.mem_read(m.symbols['_upload_source_result'],92))==before
   assert m.get('terminal_transfer_fault')==7 and m.get('terminal_transfer_cleanup_status')==11
  return 3
 check('same-instance-ambiguous-close-seek-read-cleanup-close-retry-no-DOS-no-forgotten-error',unresolved)
 def peer_cancel():
  class CancelAfterFrame(LiveUpload):
   def finish_packet(self):
    # Validate the complete physical frame without acknowledging it. The peer
    # sends genuine CAN bytes through the FIFO/real ISR, not a product hook.
    self.silent=True
    super().finish_packet()
    self.rx.extend((0x18,0x18))
  for data in (bytes(range(128)),bytes(range(256))*44):
   m=CancelAfterFrame(data);m.upload();state=m.upload_state()
   assert m.get('terminal_transfer_fault')==2 and m.get('terminal_transfer_native_status')==11
   assert not m.eots and not m.accepted and not m.get('terminal_upload_blocks_accepted')
   assert m.get('terminal_upload_accepted_bytes',4)==0
   assert state['close_calls']==1 and not state['open'] and not state['uncertain'] and not m.handles
   assert not state['first'],'Intentional peer cancellation manufactured a source error'
   assert sum(c['ah']==0x3e for c in m.fs_calls)==1
  return 2
 check('peer-double-CAN-real-ISR-native11-is-cancel-not-timeout-no-EOT',peer_cancel)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest,'Frozen binary changed during upload tests'
 save(True);print('Live upload:',len(groups),'groups,',sum(c['inputs'] for c in groups),'inputs PASS')
if __name__=='__main__':main()
