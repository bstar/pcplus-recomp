#!/usr/bin/env python3
"""Linked YMODEM owner, real UART ISR/CRC/metadata/storage; only kernel/hardware modeled."""
import argparse,binascii,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import *
from check_terminal_upload_live import LiveUpload
from check_terminal_transfer_live import LiveTransfer,ROOT,BINARY

def packet(data,seq=0):
 assert len(data) in (128,1024)
 return bytes([1 if len(data)==128 else 2,seq&255,255-(seq&255)])+data+binascii.crc_hqx(data,0).to_bytes(2,'big')
def metadata(name,size):return (name.encode()+b'\0'+str(size).encode()+b'\0').ljust(128,b'\0')
class LiveYmodem(LiveUpload):
 def __init__(self,*,sending=False,source=b'ABC\0\x1a\xff\x11\x13',fault=None,peer=False):
  self.direction=sending;self.enable_peer=False;self.phase='header';self.frame_packet=bytearray();self.frame_length=0
  self.next_bad_header=False;self.rx_control_octets=[]
  self.end_mode='ack';self.end_frames=0;self.control_octets=[];self.eot_acked=0
  self.eot_count=0;self.acks=0;self.ack_phases=[];self.accepted_payload=0;self.sequence=1;self.frames_seen=[];self.peer_rx_phase='initial'
  self.kernel_calls=[];self.dta=None;self.enumeration=['SEND.BIN'];self.find_calls=[];self.directory_calls=[];self.rx_fault=None
  super().__init__(source)
  self.dta=(self.ds,0x80);self.upload_fault=fault if sending else None;self.fault=fault if not sending else None
  self.files={'SEND.BIN':bytearray(source)} if sending else {};self.source=bytes(source);self.initial_offered=True
  self.call('_terminal_batch_initialize');self.fs_calls.clear();self.events.clear();self.tx.clear();self.kernel_calls.clear()
  self.enable_peer=peer
  # Direct engine entry retains actual serviced ISR/clock behavior without UI.
  self.put('terminal_transfer_fault',0)
  self.call('terminal_transfer_accepted_progress')
 def interrupt(self,u,n,data):
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8
  if n==0x21:self.kernel_calls.append(ah)
  if n==0x21 and ah in (0x2f,0x1a,0x4e,0x4f):
   ds=u.reg_read(UC_X86_REG_DS);dx=u.reg_read(UC_X86_REG_DX)
   if ah==0x2f:u.reg_write(UC_X86_REG_ES,self.dta[0]);u.reg_write(UC_X86_REG_BX,self.dta[1]);return
   if ah==0x1a:self.dta=(ds,dx);return
   address=self.dta[0]*16+self.dta[1]
   index=0 if ah==0x4e else struct.unpack('<I',u.mem_read(address,4))[0]
   self.find_calls.append({'ah':ah,'index':index,'dta':list(self.dta)})
   if index>=len(self.enumeration):error=18
   else:
    name=self.enumeration[index];body=bytearray(43);struct.pack_into('<I',body,0,index+1)
    struct.pack_into('<BHHI',body,21,0,0,0,len(self.files[name]));body[30:30+len(name)+1]=name.encode()+b'\0'
    u.mem_write(address,bytes(body));error=0
   u.reg_write(UC_X86_REG_AX,error);self.set_carry(error!=0);return
  if n==0x21 and ah==0x43:
   path=self.path(u.reg_read(UC_X86_REG_DS),u.reg_read(UC_X86_REG_DX))
   if path in ('D:\\RECV','.'):
    self.directory_calls.append(path);u.reg_write(UC_X86_REG_CX,0x10);u.reg_write(UC_X86_REG_AX,0);self.set_carry(False);return
  if n==0x21 and ah==0x3e and not self.direction:return LiveTransfer.interrupt(self,u,n,data)
  return super().interrupt(u,n,data)
 def output_port(self,u,port,size,value,data):
  wire=port==self.get('uart_port_thr') and not self.lcr&0x80
  # Bypass only the other test's peer decoder, never any product instructions.
  LiveTransfer.output_port(self,u,port,size,value,data)
  if not wire or not self.enable_peer:return
  value&=255
  if self.direction:self.peer_upload(value)
  else:self.peer_download(value)
 def peer_upload(self,value):
  if self.frame_packet:
   self.frame_packet.append(value)
   if len(self.frame_packet)!=self.frame_length:return
   frame=bytes(self.frame_packet);self.frame_packet.clear();n=128 if frame[0]==1 else 1024
   seq=frame[1];body=frame[3:3+n];assert frame[2]==255-seq
   assert binascii.crc_hqx(body,0)==int.from_bytes(frame[-2:],'big')
   self.frames_seen.append((seq,n))
   if self.phase=='header':
    assert seq==0 and body==metadata('SEND.BIN',len(self.source));self.phase='data';self.rx.extend(b'\x06C')
   elif self.phase=='data':
    assert seq==self.sequence&255;self.sequence+=1
    want=self.source[self.accepted_payload:self.accepted_payload+n];assert body==want.ljust(n,b'\x1a');self.accepted_payload+=len(want);self.rx.append(6)
   else:
    assert self.phase=='end' and seq==0 and not any(body);self.end_frames+=1
    if self.end_mode=='app':self.phase='done';self.rx.extend(b'\x1bAPP')
    elif self.end_mode=='nak':self.rx.append(21)
    elif self.end_mode=='wait':pass
    else:self.phase='done';self.rx.append(6)
  elif value in (1,2):self.frame_packet.append(value);self.frame_length=(128 if value==1 else 1024)+5
  elif value==4:
   self.control_octets.append(value);self.eot_count+=1;assert not self.handles,'EOT before checked physical source close'
   if self.eot_count%2:self.rx.append(21)
   else:self.eot_acked+=1;self.phase='end';self.rx.extend(b'\x06C')
  else:self.control_octets.append(value);assert value==24,('Unexpected TX control',value)
 def peer_download(self,value):
  self.rx_control_octets.append(value)
  if value==6:self.acks+=1;self.ack_phases.append(self.peer_rx_phase)
  if self.peer_rx_phase=='initial' and value==67:
   self.rx.extend(packet(metadata('ONE.BIN',len(self.source))));self.peer_rx_phase='header'
  elif self.peer_rx_phase=='header' and value==67:
   self.rx.extend(packet(self.source.ljust(128,b'\x1a'),1));self.peer_rx_phase='data'
  elif self.peer_rx_phase=='data' and value==6:self.rx.append(4);self.peer_rx_phase='eot-first'
  elif self.peer_rx_phase=='eot-first' and value==21:self.rx.append(4);self.peer_rx_phase='eot-second'
  elif self.peer_rx_phase=='eot-second' and value==6:
   assert bytes(self.files['D:\\RECV\\ONE.BIN'])==self.source,'EOT ACK before exact install'
   self.peer_rx_phase='committed'
  elif self.peer_rx_phase=='committed' and value==67:
   if self.next_bad_header:self.rx.extend(packet(metadata('../BAD.BIN',0)));self.peer_rx_phase='bad-header'
   else:self.rx.extend(packet(bytes(128)));self.peer_rx_phase='end'
  elif self.peer_rx_phase=='end' and value==6:self.peer_rx_phase='done';self.rx.extend(b'APP')
 def scratch(self,data,delta=4096):
  pointer=self.offset('_terminal_batch_buffer')+delta;self.uc.mem_write(self.data_base+pointer,data);return pointer
 def run_engine(self,path=None):
  path=path or (b'SEND.BIN' if self.direction else b'D:\\RECV\\')
  pointer=self.scratch(path+b'\0',6000)
  if self.enable_peer and self.direction:self.rx.append(67)
  return self.call('_ymodem_run',[pointer,int(self.direction)],limit=40000000)
 def snapshot(self,name,count):return bytes(self.uc.mem_read(self.symbols[name],count))
 def header(self):
  source=self.scratch(metadata('HELD.BIN',128));out=self.scratch(b'\0'*36,4300)
  assert self.call('_batch_header_decode',[source,128,out])==0
  return out
 def counts(self):return {a:sum(c['ah']==a for c in self.fs_calls) for a in (0x3e,0x40,0x41,0x56)}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--sha256',help='Optional required immutable runtime SHA256');args=parser.parse_args()
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert not args.sha256 or digest==args.sha256,'Frozen binary differs'
 groups=[]
 def save(passed):
  (ROOT/'build/terminal/terminal-ymodem-live-checks.json').write_text(json.dumps({'passed':passed,'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'binary_sha256':digest,'inputs':sum(g.get('inputs',0) for g in groups),'cases':groups,'scope':'Actual linked maintained YMODEM/codec/per-file owners/CRC and UART ISR; only BIOS/UART/ticks and DOS kernel filesystem/DTA/enumeration boundaries modeled. No product callback patched, skipped or manually returned.','limitations':['Focused synthetic kernel/peer CPU tests, separate from actual DOS/BBS evidence.','No physical serial timing, power-loss atomicity, streaming YMODEM-G or native batch equivalence claim.','Most cases use direct C engine entry; final-ACK uncertainty and partial/cancel notices additionally exercise foreground UI/ASM notice. No complete accepted-progress watchdog matrix is asserted here.']},indent=2)+'\n')
 def check(name,fn):
  try:count=fn()
  except Exception as error:groups.append({'case':name,'passed':False,'error':str(error)});save(False);raise
  groups.append({'case':name,'passed':True,'inputs':count});print(name,'PASS',count,flush=True)
 def rx_busy():
  for retained in ('open','closed'):
   m=LiveYmodem();directory=m.scratch(b'D:\\RECV\\\0',6000)
   assert m.call('_batch_download_begin',[directory])==0
   assert m.call('_batch_download_open',[m.header()])==0
   if retained=='closed':assert m.call('_transfer_download_seal')==0
   prior={n:m.snapshot(n,c) for n,c in [('_batch_download_result',240),('_transfer_download_result',148)]}
   files={k:bytes(v) for k,v in m.files.items()};handles=dict(m.handles);fs=len(m.fs_calls);dirs=len(m.directory_calls);kernel=len(m.kernel_calls)
   assert m.run_engine()==7
   assert all(m.snapshot(n,len(b))==b for n,b in prior.items()) and handles==m.handles and files=={k:bytes(v) for k,v in m.files.items()}
   assert len(m.fs_calls)==fs and len(m.directory_calls)==dirs and len(m.kernel_calls)==kernel and not m.tx
  return 2
 check('RX-busy-prior-open-or-sealed-owned-stage-unchanged-no-DOS',rx_busy)
 def tx_busy():
  for active in (False,True):
   m=LiveYmodem(sending=True);path=m.scratch(b'SEND.BIN\0',6000)
   assert m.call('_batch_upload_begin',[path])==0
   if active:assert m.call('_batch_upload_next')==1
   prior={n:m.snapshot(n,c) for n,c in [('_batch_upload_current',90),('_upload_source_result',92),('_batch_upload_find',43)]};handles=dict(m.handles);dta=m.dta
   calls=len(m.fs_calls);finds=len(m.find_calls);kernel=len(m.kernel_calls);assert dta==(m.ds,0x80)
   assert m.run_engine()==7
   assert all(m.snapshot(n,len(b))==b for n,b in prior.items()) and handles==m.handles and dta==m.dta
   assert len(m.fs_calls)==calls and len(m.find_calls)==finds and len(m.kernel_calls)==kernel and not m.tx
  return 2
 check('TX-busy-prior-enumeration-or-open-source-preserved-no-DOS',tx_busy)
 def tx_fault():
  for fault in ('read','close'):
   m=LiveYmodem(sending=True,fault=fault,peer=True);assert m.run_engine()==7
   assert m.eot_count==0 and m.counts()[0x3e]==1 and bytes(m.files['SEND.BIN'])==m.source
   state=m.upload_state();assert state['close_calls']==1
   assert state['uncertain']==int(fault=='close')
   if fault=='read':assert not m.handles
   else:
    before=m.snapshot('_upload_source_result',92);calls=len(m.fs_calls);handles=dict(m.handles);m.enable_peer=False
    assert m.run_engine()==7 and len(m.fs_calls)==calls and m.handles==handles and m.snapshot('_upload_source_result',92)==before
  return 3
 check('TX-read-close-fault-no-EOT-close-once-and-uncertain-retry',tx_fault)
 def rx_fault():
  for fault in ('write','short','close','install'):
   m=LiveYmodem(fault=fault,peer=True);assert m.run_engine()==7
   assert 'eot-second' not in m.ack_phases and 'D:\\RECV\\ONE.BIN' not in m.files
   assert m.counts()[0x3e]==1
   if fault=='close':
    assert m.handles and m.get('_batch_download_result',2)==6 and m.get('_transfer_download_result',2)==6
    prior={n:m.snapshot(n,c) for n,c in [('_batch_download_result',240),('_transfer_download_result',148)]};kernel=len(m.kernel_calls);handles=dict(m.handles);m.enable_peer=False
    assert m.run_engine()==7 and len(m.kernel_calls)==kernel and handles==m.handles
    assert all(m.snapshot(n,len(b))==b for n,b in prior.items())
   else:assert not m.handles and 'D:\\RECV\\PCRX.$$$' not in m.files
  return 5
 check('RX-write-short-close-install-faults-withhold-final-EOT-ACK',rx_fault)
 def success():
  for sending in (False,True):
   m=LiveYmodem(sending=sending,peer=True);assert m.run_engine()==0
   assert m.counts()[0x3e]==1 and not m.handles
   if sending:assert m.phase=='done' and m.eot_count==2 and m.accepted_payload==len(m.source)
   else:
    assert m.peer_rx_phase=='done' and bytes(m.files['D:\\RECV\\ONE.BIN'])==m.source
    assert bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP'
    assert m.call('uart_receive_byte')==0xffff
  return 2
 check('TX-RX-normal-controls-and-storage-before-peer-commit',success)
 def rewind_bounds():
  for full in (False,True):
   m=LiveYmodem()
   if full:m.receive_irq(b'X'*4096)
   before=(m.get('uart_rx_read'),m.get('uart_rx_count'));count=1 if full else 1030
   assert m.call('_ymodem_io_unread',[count])==1
   assert (m.get('uart_rx_read'),m.get('uart_rx_count'))==before and m.get('terminal_transfer_fault')==5
   assert m.uc.reg_read(UC_X86_REG_EFLAGS)&0x200,'Unread changed entry IF'
  return 2
 check('actual-UART-ring-rewind-capacity-and-count-guards-fail-closed',rewind_bounds)
 def final_ack_policy():
  for bridge in ('engine','C-bridge','ASM-owner'):
   m=LiveYmodem(sending=True,peer=True);m.end_mode='app'
   if bridge=='ASM-owner':
    m.put('terminal_transfer_protocol',1);m.waiting_ui=True;m.rx.append(67)
    m.call('terminal_upload_start');m.call('terminal_transfer_poll',limit=40000000)
    assert not m.get('terminal_transfer_active') and not m.get('terminal_transfer_pending')
    assert b'TX batch sent; ACK?' in bytes(m.uc.mem_read(0xb8000,4000))[::2]
   elif bridge=='C-bridge':
    m.uc.mem_write(m.symbols['terminal_transfer_filename'],b'SEND.BIN\0');m.put('_terminal_transfer_direction',1);m.rx.append(67)
    assert m.call('_terminal_batch_store',limit=40000000)==2
   else:assert m.run_engine()==10
   assert m.get('_ymodem_current')==10 and m.get('terminal_transfer_fault')==0 and m.get('terminal_transfer_cleanup_status')==0
   assert m.eot_acked==1 and m.eot_count==2 and m.accepted_payload==len(m.source)
   assert struct.unpack_from('<I',m.snapshot('_ymodem_current',32),10)[0]==1
   assert m.end_frames==1 and len(m.frames_seen)==3 and m.control_octets==[4,4],'Binary header or CAN injected after application resume'
   assert m.get('_batch_upload_current')==3 and not m.handles and m.counts()[0x3e]==1,'Unconfirmed end aborted resolved source'
   assert bytes(m.call('uart_receive_byte') for _ in range(4))==b'\x1bAPP'
   assert m.call('uart_receive_byte')==0xffff,'Application prefix duplicated'
  for mode in ('nak','wait'):
   m=LiveYmodem(sending=True,peer=True);m.end_mode=mode
   assert m.run_engine()==3 and m.get('_ymodem_current')==3,'Pure retry/timeout incorrectly treated as application return'
   assert m.end_frames==10 and m.eot_acked==1 and m.eot_count==2 and m.accepted_payload==len(m.source)
   assert m.control_octets==[4,4] and m.counts()[0x3e]==1 and not m.handles
  return 5
 check('final-header-unconfirmed-application-preserved-and-NAK-WAIT-remain-strict',final_ack_policy)
 def partial_notice():
  m=LiveYmodem(peer=True);m.next_bad_header=True;m.filename=b'D:\\RECV\\';m.waiting_ui=True;m.put('terminal_transfer_protocol',1)
  m.call('terminal_transfer_start');m.call('terminal_transfer_poll',limit=40000000)
  video=bytes(m.uc.mem_read(0xb8000,4000))[::2]
  assert b'RX batch partial' in video and b'RX saved; ACK?' not in video
  assert m.get('_ymodem_current')==6 and m.get('terminal_transfer_fault')==7 and not m.get('terminal_transfer_cleanup_status')
  assert struct.unpack_from('<I',m.snapshot('_ymodem_current',32),10)[0]==1
  assert m.peer_rx_phase=='bad-header' and m.ack_phases==['header','data','eot-second'],'Invalid next metadata got a fake ACK'
  assert m.rx_control_octets[-2:]==[24,24] and m.rx_control_octets.count(24)==2
  assert m.files=={'D:\\RECV\\ONE.BIN':bytearray(m.source)} and not m.handles and m.counts()[0x3e]==1
  assert not m.get('terminal_transfer_active') and not m.get('terminal_transfer_pending')
  # The previous batch's real completed-file DWORD remains nonzero when the
  # next filename prompt is cancelled before a new C engine entry.
  kernel=len(m.kernel_calls);wire=len(m.tx);files={p:bytes(data) for p,data in m.files.items()};m.enable_peer=False;m.keys.append(0x011b)
  m.call('terminal_transfer_start');m.call('terminal_transfer_poll',limit=40000000)
  video=bytes(m.uc.mem_read(0xb8000,4000))[::2]
  assert b'RX canceled' in video and b'RX batch partial' not in video and b'RX saved; ACK?' not in video
  assert struct.unpack_from('<I',m.snapshot('_ymodem_current',32),10)[0]==1
  assert m.get('terminal_transfer_fault')==2 and not m.get('terminal_transfer_cleanup_status')
  assert len(m.kernel_calls)==kernel and len(m.tx)==wire and files=={p:bytes(data) for p,data in m.files.items()}
  return 2
 check('ASM-partial-batch-notice-preserves-earlier-file-and-cancel-ignores-stale-count',partial_notice)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==digest,'Frozen binary changed';save(True)
if __name__=='__main__':main()
