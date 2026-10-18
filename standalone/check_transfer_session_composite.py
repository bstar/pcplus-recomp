#!/usr/bin/env python3
"""Run a complete one-owner native ordinary receiver with replaceable fixture IO."""
import hashlib,json,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import UC_X86_REG_BX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_ES
from dos_image import DosImage
from check_transfer_blocks import expected
ROOT=Path(__file__).resolve().parents[1];BINARY=ROOT/'build/transfer-session-composite/TRANSFER.EXE'
class Unsupported(Exception):pass
class Composite(DosImage):
 def __init__(self):
  super().__init__(BINARY,BINARY.parent/'composite.map');self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
 def interrupt(self,u,n,unused):raise Unsupported(n)
 def run(self,schedule,settings=None):
  assert len(schedule)<=128
  raw=b''.join(payload for trigger,payload in schedule);assert len(raw)<=16000
  self.uc.mem_write(self.symbols['composite_input_data'],raw or b'\0');offset=0;descriptors=[]
  for trigger,payload in schedule:descriptors.extend((trigger,self.offset('composite_input_data')+offset,len(payload)));offset+=len(payload)
  if descriptors:self.uc.mem_write(self.symbols['composite_schedule'],struct.pack('<'+'H'*len(descriptors),*descriptors))
  self.put('composite_schedule_count',len(schedule))
  for name,value in (settings or {}).items():self.put(name,value)
  result=self.call('_transfer_composite_run',limit=20000000)
  got={'owner_result':result,'file':bytes(self.uc.mem_read(self.symbols['composite_file_data'],self.get('composite_file_used'))),'wire':bytes(self.uc.mem_read(self.symbols['composite_wire'],self.get('composite_wire_count'))),'writes':self.get('composite_file_write_calls'),'closes':self.get('composite_file_close_calls'),'first_error':self.get('composite_first_error'),'accepted':self.get('session_blocks_accepted'),'errors':self.get('session_error_count'),'status':self.get('composite_status_code'),'next_frame':self.get('composite_schedule_next')}
  # An installer must require both owner success and clean persistent storage.
  got['may_install']=got['owner_result']==1 and got['first_error']==0
  return got

def transfer(payloads,crc=1):
 schedule=[(ord('C') if crc else 0x15,expected(payloads[0],1,crc))]
 schedule += [(6,expected(data,(index+1)&255,crc)) for index,data in enumerate(payloads[1:],1)]
 return schedule+[(6,b'\x04'),(0x15,b'\x04')]
def main():
 cases=[]
 def record(name,got):cases.append({'case':name,'passed':True,**{k:(len(v) if k=='file' else v.hex()) if isinstance(v,bytes) else v for k,v in got.items()}});print(name,'passed',flush=True)
 for crc in (0,1):
  for sizes in ([128],[1024],[128,128,1024,128],[128]*96,[1024]*12,[128]*79+[1024]):
   payloads=[bytes((i*37+j*13)%256 for i in range(size)) for j,size in enumerate(sizes)];m=Composite();got=m.run(transfer(payloads,crc))
   assert got['owner_result']==1 and got['may_install'] and got['file']==b''.join(payloads) and got['accepted']==len(payloads) and got['closes']==1 and not got['errors'],(crc,sizes,got)
   assert got['writes']==1+int(sum(sizes)>=10240)
   record(f'one-native-owner-{crc}-sizes-{sizes[0]}-blocks-{len(sizes)}',got)
 # Duplicate/error retransmits keep the same native frame and running counters.
 data=bytes((i*17)%256 for i in range(128));good=expected(data,1,1);bad=bytearray(good);bad[-1]^=1
 for name,schedule,accepted,errors in [
  ('duplicate-ACK-no-double-append',[(67,good),(6,good),(6,expected(data,2,1)),(6,b'\x04'),(21,b'\x04')],2,0),
  ('CRC-reject-NAK-then-valid',[(67,bytes(bad)),(21,good),(6,b'\x04'),(21,b'\x04')],1,1),
  ('wrong-sequence-NAK-then-valid',[(67,expected(data,2,1)),(21,good),(6,b'\x04'),(21,b'\x04')],1,1)]:
  m=Composite();got=m.run(schedule);assert got['may_install'] and got['file']==data*accepted and got['accepted']==accepted and got['errors']==errors,(name,got);record(name,got)
 for name,schedule,settings,status in [
  ('double-CAN-real-longjmp-cleanup',[(67,b'\x18\x18')],{},11),
  ('local-cancel-after-first-block',transfer([data,data]),{'composite_cancel_after_reads':133},11),
  ('carrier-loss',[(67,good)],{'composite_carrier':0},15)]:
  m=Composite();got=m.run(schedule,settings);assert got['owner_result']==0 and not got['may_install'] and got['status']==status and got['closes']==1,(name,got);record(name,got)
 m=Composite();got=m.run([]);assert not got['may_install'] and got['owner_result']==0 and got['errors']==15 and got['closes']==0;record('native-timeout-limit-return-requires-outer-abort-close',got)
 for name,payloads,settings,result,error in [
  ('periodic-write-failure', [data]*81, {'composite_write_fail_call':1},0,1),
  ('native-final-write-ignored-requires-storage-first-error-gate',[data],{'composite_write_fail_call':1},1,1),
  ('native-final-close-ignored-requires-storage-first-error-gate',[data],{'composite_close_fail':1},1,2)]:
  m=Composite();got=m.run(transfer(payloads),settings);assert got['owner_result']==result and got['first_error']==error and not got['may_install'],(name,got);record(name,got)
 m=Composite();m.uc.reg_write(UC_X86_REG_ES,0x4321);got=m.run(transfer([data]));
 for reg,value in [(UC_X86_REG_ES,0x4321),(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)]:assert m.uc.reg_read(reg)==value,(reg,m.uc.reg_read(reg))
 record('composed-near-caller-stack-BP-SI-DI-preserved',got)
 m=Composite()
 try:m.run([(67,expected(bytes(128),0,1))],{'session_protocol':5})
 except Unsupported as e:assert e.args==(3,)
 else:raise AssertionError('Batch metadata unsupported path silently succeeded')
 cases.append({'case':'batch-metadata-explicit-trap','passed':True})
 result={'passed':True,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'One invocation of actual native receive owner persists its BP frame, CRC/sequence, counters and setjmp context across asynchronous scheduled128/1024-byte frames. Actual native CRC/validation/ACK/NAK/EOT and periodic/final FILE control execute; explicit replaceable UART/time/UI/path/memory-file boundaries only. Installer policy demonstrated but no live UART, real disk install or full protocol application claimed.'}
 (BINARY.parent/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',len(cases),'one-owner composite cases')
if __name__=='__main__':main()
