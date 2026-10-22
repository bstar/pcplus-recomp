#!/usr/bin/env python3
"""Linked active-file recovery: real product code/UART ISR, modeled DOS kernel.

The peer waits for exact protocol responses. No product callback or instruction is
replaced; file read/seek/write and hardware/BIOS are declared external models.
"""
import argparse,hashlib,json
from collections import deque
from pathlib import Path
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE
from check_terminal_zmodem_live import LiveZmodem,ROOT,BINARY,h,offer,payload

class Active(LiveZmodem):
 def __init__(self,body,fmt,fault=None):
  self.positions={};self.readback_fault=fault;self.readback_calls=[];self.readback_seeks=0
  super().__init__(source=body,fmt=fmt);self.strict=fault is None
 def interrupt(self,u,n,data):
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8;bx=u.reg_read(UC_X86_REG_BX)
  if n!=0x21:return super().interrupt(u,n,data)
  if ah in (0x5b,0x3e):
   result=super().interrupt(u,n,data)
   if not u.reg_read(UC_X86_REG_EFLAGS)&1:
    if ah==0x5b:self.positions[u.reg_read(UC_X86_REG_AX)]=0
    else:self.positions.pop(bx,None)
   return result
  if ah not in (0x3f,0x40,0x42):return super().interrupt(u,n,data)
  name=self.handles.get(bx);error=0;result=0;before_cursor=self.positions.get(bx)
  if name is None:error=6
  elif ah==0x42:
   assert ax==0x4200
   at=(u.reg_read(UC_X86_REG_CX)<<16)|u.reg_read(UC_X86_REG_DX)
   self.readback_seeks+=1
   if self.readback_fault=='seek' and self.readback_seeks==1:error=5
   elif self.readback_fault=='restore' and self.readback_seeks==2:error=5
   else:self.positions[bx]=at;result=at
  else:
   count=u.reg_read(UC_X86_REG_CX);address=u.reg_read(UC_X86_REG_DS)*16+u.reg_read(UC_X86_REG_DX);at=self.positions[bx]
   if ah==0x3f:
    if self.readback_fault=='read':error=5
    else:
     value=bytes(self.files[name][at:at+count])
     if self.readback_fault=='short':value=value[:-1]
     if value:u.mem_write(address,value)
     result=len(value);self.positions[bx]+=result
   else:
    value=bytes(u.mem_read(address,count));body=self.files[name]
    if at>len(body):body.extend(bytes(at-len(body)))
    body[at:at+count]=value;result=count;self.positions[bx]+=count
  self.readback_calls.append(dict(ah=ah,path=name,error=error,result=result,before_cursor=before_cursor,cursor=self.positions.get(bx),tx_bytes=len(self.tx)))
  self.fs_calls.append(dict(ah=ah,path=name,error=error,tx=bytes(self.tx).hex()))
  u.reg_write(UC_X86_REG_AX,error or result&65535)
  if ah==0x42 and not error:u.reg_write(UC_X86_REG_DX,result>>16)
  self.set_carry(bool(error))

def run_case(fmt,overlap,fault=None,large=False):
 body=bytes((i*73+(i>>8)*19+37)&255 for i in range(65549)) if large else b'ABCDEFGHIJKL'
 m=Active(body,fmt,fault);ready=h(1,0x23002000);cancel=b'\x18'*8+b'\x08'*10
 if large:
  # Isolate32-bit memory/cursor arithmetic with the existing bounded HARD-flow
  # peer. Real DOS session cases separately retain the actual BIOS clock.
  m.advance_ticks=False;m.respect_rts=True;m.put('uart_hardware_flow',1)
 initial=65536 if large else 8
 packets=[payload(body[i:min(i+8192,initial)],i,fmt) for i in range(0,initial,8192)]
 script=[(ready,offer('ONE.BIN',len(body),fmt)),(h(9),packets[0])]
 for i,p in enumerate(packets[:-1]):script.append((h(3,(i+1)*8192),packets[i+1]))
 at=65530 if large else 4 if overlap else 2
 old=body[at:] if overlap or large else body[2:6]
 if fault=='mismatch':old=bytes([old[0]^1])+old[1:]
 script.append((h(3,initial),payload(old,at,fmt)))
 if fault:
  # The engine and foreground failure owner each emit their bounded cancel.
  script.append((cancel+cancel,b''))
 else:
  if not overlap and not large:script.append((h(9,8),payload(body[8:],8,fmt)))
  script += [(h(3,len(body)),h(11,len(body),fmt)),(ready,h(8)),(h(8),b'OOAPP')]
 expected=b''.join(w for w,_ in script);m.script=deque(script)
 result=m.run(owner=True)
 checks=dict(owner_result=result==(7 if fault else 0),peer_script_exhausted=not m.script and not m.pending,
  exact_wire=bytes(m.tx)==expected,no_owned_handles=not m.handles and not m.positions,
  readback_seek_observed=any(c['ah']==0x42 for c in m.readback_calls),
  only_unique_payload_written=sum(c['result'] for c in m.readback_calls if c['ah']==0x40)==(initial if fault else len(body)))
 if fault:
  checks.update(no_installed_or_owned_stage=not m.files,
   no_ACK_for_unverified_replay=h(3,6) not in m.tx and h(3,len(body)) not in m.tx,
   sticky_storage_failure=int.from_bytes(m.uc.mem_read(m.symbols['_transfer_download_result']+2,2),'little')!=0)
 else:
  checks.update(exact_single_file=bytes(m.files['D:\\RECV\\ONE.BIN'])==body,
   raw_application_tail=bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP',
   file_accounting=m.get('_terminal_zmodem_files',4)==1,
   append_cursor_restored=all(c['before_cursor']==sum(v['result'] for v in m.readback_calls[:i] if v['ah']==0x40) for i,c in enumerate(m.readback_calls) if c['ah']==0x40))
 assert all(checks.values()),(fmt,overlap,fault,large,checks,m.readback_calls,bytes(m.tx).hex(),expected.hex(),bytes(m.pending).hex())
 return dict(case=f'fmt{fmt}-overlap{overlap}-fault{fault}-large{large}',passed=True,checks=checks,kernel_calls=m.readback_calls,body_bytes=len(body),clock='Frozen BIOS ticks for large memory/HARD-flow case' if large else 'Modeled BIOS ticks')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 rows=[run_case(fmt,overlap) for fmt in (65,67) for overlap in (False,True)]
 rows += [run_case(67,False,fault) for fault in ('mismatch','read','short','seek','restore')]
 rows.append(run_case(67,True,large=True))
 rows.extend(run_frontier(fmt) for fmt in (65,67))
 rows.extend(run_frontier(fmt,expired=True) for fmt in (65,67))
 sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
 report=dict(passed=True,cases=rows,case_count=len(rows),binary_sha256=sha(BINARY),test_sha256=sha(Path(__file__)),scope=__doc__,
  limitations=['Kernel models are external; actual DOS read/seek is tested separately.','No sender timeout model, audio/BBS or physical compatibility acceptance.'])
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(passed=True,case_count=len(rows))))
def run_frontier(fmt,expired=False):
 class Frontier(Active):
  def __init__(self,body):
   self.ack_ticks={};self.old_controls=0;self.control_cursor=0;super().__init__(body,fmt)
   self.advance_ticks=False;self.strict=not expired
  def output_port(self,u,port,size,value,data):
   super().output_port(u,port,size,value,data)
   if port==self.get('uart_port_thr') and not self.lcr&0x80:
    if len(self.tx)>self.control_cursor and bytes(self.tx).endswith(h(9,512)):
      # Each fully consumed old packet requests the already verified position.
      self.control_cursor=len(self.tx);self.old_controls+=1;self.tick+=1
      if expired and self.old_controls==16:
       self.tick+=65536;self.advance_ticks=True
      if self.old_controls==16:self.ack_ticks[256]=self.tick
    if bytes(self.tx).endswith(h(3,512)):self.ack_ticks[512]=self.tick
 body=bytes(range(256))*4;m=Frontier(body);ready=h(1,0x23002000)
 script=[(ready,offer('ONE.BIN',1024,fmt)),(h(9),payload(body[:512],0,fmt)),(h(3,512),payload(body[:16],0,fmt))]
 script.extend((h(9,512),payload(body[i:i+16],i,fmt)) for i in range(16,256,16))
 script.extend([(h(9,512),payload(body[512:],512,fmt)),(h(3,1024),h(11,1024,fmt)),(ready,h(8)),(h(8),b'OOAPP')])
 expected=b''.join(w for w,_ in script);m.script=deque(script);progress=[]
 def observe(u,address,size,ignored):
  if address==m.symbols['terminal_transfer_accepted_progress']:progress.append(dict(tx_bytes=len(m.tx),tick=m.tick))
 m.uc.hook_add(UC_HOOK_CODE,observe)
 result=m.run(owner=True);begin=len(ready+h(9)+h(3,512));end=begin+16*len(h(9,512))
 checks=dict(no_handles=not m.handles and not m.positions,
  sixteen_stored_prefix_reads=sum(c['ah']==0x3f for c in m.readback_calls)==16,
  no_accepted_progress_calls_during_old_packets=not any(begin<=p['tx_bytes']<end for p in progress),
  modeled_clock_advances_during_old_packets=m.ack_ticks[256]>m.ack_ticks[512])
 if expired:
  prefix=expected[:end];remaining=bytes(m.tx)[end:]
  checks.update(watchdog_timeout=result==3,no_installed_or_owned_stage=not m.files,
   correct_controls_before_timeout=bytes(m.tx).startswith(prefix),
   bounded_cancel_after_timeout=5<=remaining.count(24)<=16 and len(remaining)<=36 and all(v in (8,24) for v in remaining),
   no_ACK_for_unaccepted_new_data=h(3,1024) not in m.tx)
 else:
  checks.update(owner_success=result==0,exact_wire=bytes(m.tx)==expected,peer_exhausted=not m.script and not m.pending,
   exact_file=bytes(m.files['D:\\RECV\\ONE.BIN'])==body,
   intact_application_tail=bytes(m.call('uart_receive_byte') for _ in range(3))==b'APP')
 assert all(checks.values()),(fmt,checks,progress,m.ack_ticks)
 return dict(case=f'sixteen-advancing-old-packets-CRC{fmt}-expired{expired}',passed=True,checks=checks,observed_accepted_progress=progress,old_packet_TX_range=[begin,end],ACK_ticks=m.ack_ticks,
  clock='Explicit65536-tick idle jump after last old packet; polling clock resumes for cleanup' if expired else 'One modeled BIOS tick per old packet; no wall-time throughput claim')

if __name__=='__main__':main()
