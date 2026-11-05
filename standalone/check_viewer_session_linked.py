#!/usr/bin/env python3
"""Execute actual paging controller; assert bounded DOS steps and cleanup under faults."""
import argparse,json,re,struct
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import *
from check_viewer_file_linked import Owner
from dos_image import DosImage
from build_path_session import ROOT,sha

class Session(Owner):
 def __init__(self,binary,fault=''):
  DosImage.__init__(self,binary,binary.with_name('VIEWPAGE.map'))
  self.entries={n:(self.base_segment+int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',binary.with_name('VIEWPAGE.map').read_text(),re.M|re.I)}
  self.fault=fault;self.calls=[];self.position=0;self.opened=False;self.step_calls=[]
  self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
  self.uc.mem_write(self.data_base+0xb000,b'data.bin\0'+bytes(55))
  self.uc.mem_write(0x90ff0,b'\xa5'*1952)
 def bank(self,name,args=()):
  # Reuse the same proved far cdecl entry harness with a session symbol alias.
  key='_viewer_file_'+name;value=self.entries.get(key)
  self.entries[key]=self.entries['_viewer_session_'+name]
  try:return Owner.bank(self,name,args)
  finally:
   if value is None:del self.entries[key]
   else:self.entries[key]=value
 def begin(self):return self.bank('begin',[0xb000,0xb300,0x1000,0x9000,1920,80,24])
 def snapshot(self):
  assert self.bank('inspect',[0xb100])==0
  fields=['phase','error','file_status','decode_status','owned','pending','count','at','eof','width','rows','page','target','start','next','read_position','first','last']
  return dict(zip(fields,struct.unpack('<11H7L',self.uc.mem_read(self.data_base+0xb100,50))))
 def file_snapshot(self):
  assert Owner.bank(self,'inspect',[0xb400])==0
  return struct.unpack_from('<8HL',self.uc.mem_read(self.data_base+0xb400,84))
 def step(self):
  before=len(self.calls);result=self.bank('step');calls=self.calls[before:]
  assert len(calls)<=1 and all(c in ['read','seek'] for c in calls),calls
  self.step_calls.append(calls);return result
 def pump(self):
  for _ in range(10000):
   s=self.snapshot()
   if s['phase']!=1:return s
   assert s['first']<=s['last'] and s['last']-s['first']<64
   if not s['pending']:assert s['read_position']>=s['next'] and s['read_position']-s['next']==s['count']-s['at']
   self.step()
  raise AssertionError('unbounded controller progress')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['program','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.program.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 rows=[];step_count=0
 for fault,want,file_status,closes in [('canonical-error',6,4,0),('canonical-device',6,4,0),('attributes-error',6,6,0),
  ('directory',6,6,0),('open-error',6,7,0),('device-error',6,8,1),('character-device',6,8,1),('invalid-handle',8,14,0)]:
  m=Session(binary,fault);assert m.begin()==want
  s=m.snapshot();assert s['file_status']==file_status and s['phase']==(4 if want==8 else 3) and s['owned']==(1 if want==8 else 0)
  assert m.calls.count('close')==closes
  calls=m.calls[:];assert m.bank('stop')==want and m.calls==calls
  rows.append(dict(case=fault,status=want,file_status=file_status,DOS_calls=m.calls,passed=True))
 for fault,file_status in [('read-error',9),('read-too-many',14)]:
  m=Session(binary,fault);assert m.begin()==0 and m.step()==6
  s=m.snapshot();assert s['phase']==3 and s['owned']==1 and s['file_status']==file_status and s['next']==0
  calls=m.calls[:];assert m.step()==3 and m.bank('move',[2])==3 and m.calls==calls
  assert m.bank('stop')==6 and m.calls.count('close')==1 and m.snapshot()['owned']==0
  rows.append(dict(case=fault,status=6,DOS_calls=m.calls,passed=True));step_count+=len(m.step_calls)
 for fault,file_status in [('seek-error',10),('seek-wrong',14)]:
  m=Session(binary,fault);assert m.begin()==0 and m.pump()['phase']==2
  assert m.bank('move',[0])==0 and m.snapshot()['pending']==1
  assert m.step()==6 and m.snapshot()['file_status']==file_status
  assert m.bank('stop')==6 and m.calls.count('close')==1
  rows.append(dict(case=fault,status=6,DOS_calls=m.calls,passed=True));step_count+=len(m.step_calls)
 for fault in ['close-error','read-close-error','release-error']:
  m=Session(binary,fault);assert m.begin()==0
  if fault=='read-close-error':assert m.step()==6
  if fault=='release-error':m.uc.mem_write(m.symbols['_capture_reservation']+6,b'\1\0')
  assert m.bank('stop')==8
  s=m.snapshot();f=m.file_snapshot();assert s['phase']==4 and s['owned']==1 and f[0]==4 and f[7]==1
  if fault=='read-close-error':assert f[1:4]==(9,5,6)
  calls=m.calls[:];state=bytes(m.uc.mem_read(m.symbols['_viewer_session_storage'],596))
  assert m.begin()==8 and m.bank('move',[0])==8 and m.step()==8 and m.bank('stop')==8
  assert m.calls==calls and bytes(m.uc.mem_read(m.symbols['_viewer_session_storage'],596))==state
  rows.append(dict(case=fault,quarantined=True,file_first_status=f[1],file_close_error=f[3],file_release_error=f[5],DOS_calls=m.calls,passed=True));step_count+=len(m.step_calls)
 for advance in [0,1]:
  m=Session(binary);assert m.begin()==0
  if advance:assert m.step()==0
  assert m.bank('stop')==0 and m.calls.count('read')==advance and m.calls.count('close')==1
  calls=m.calls[:];assert m.bank('stop')==0 and m.calls==calls and m.snapshot()['phase']==5
  rows.append(dict(case='cancel-'+str(advance)+'-reads',DOS_calls=m.calls,passed=True));step_count+=len(m.step_calls)
 m=Session(binary);assert Owner.bank(m,'open',[0xb000,0xb300])==0
 calls=m.calls[:];assert m.begin()==2 and m.bank('stop')==0 and m.calls==calls
 assert m.file_snapshot()[6:8]==(7,1) and Owner.bank(m,'close')==0
 rows.append(dict(case='never-close-another-owner',passed=True))
 m=Session(binary);m.uc.mem_write(m.symbols['_capture_reservation']+6,b'\1\0');assert m.begin()==6
 assert m.calls==['canonical'] and m.snapshot()['owned']==0 and m.bank('stop')==6
 rows.append(dict(case='claim-busy-without-handle',passed=True))
 m=Session(binary);before=bytes(m.uc.mem_read(m.symbols['_viewer_session_storage'],596));sg,off=m.entries['_viewer_session_storage']
 for name,page,capacity,width,rows0 in [('state-alias',[off+16,sg-1],1920,80,24),('segment-wrap',[0xffff,0x9000],1920,80,24),
  ('over-1MB',[0x10,0xffff],1920,80,24),('capacity',[0x1000,0x9000],1919,80,24),('width0',[0x1000,0x9000],1920,0,24)]:
  assert m.bank('begin',[0xb000,0xb300]+page+[capacity,width,rows0])==1 and not m.calls
  assert bytes(m.uc.mem_read(m.symbols['_viewer_session_storage'],596))==before and bytes(m.uc.mem_read(0x90ff0,1952))==b'\xa5'*1952
  rows.append(dict(case='argument-'+name,preserved=True,passed=True))
 m=Session(binary);assert m.begin()==0
 first=m.pump();assert first['phase']==2 and first['page']==first['target']==0
 assert m.bank('move',[2])==0 and m.snapshot()['page']==m.snapshot()['target']==1
 s=m.pump();assert s['phase']==2 and s['page']==1
 assert m.bank('move',[1])==0 and m.pump()['page']==0
 assert m.bank('move',[1])==4 and m.bank('move',[0])==0 and m.pump()['page']==0
 assert m.bank('stop')==0 and m.calls.count('close')==1
 assert bytes(m.uc.mem_read(0x90ff0,16))==b'\xa5'*16 and bytes(m.uc.mem_read(0x91780,16))==b'\xa5'*16
 rows.append(dict(case='paging-current-target-read-ahead-invariant',steps=len(m.step_calls),max_DOS_data_calls_per_step=max(map(len,m.step_calls)),passed=True));step_count+=len(m.step_calls)
 m=Session(binary);state=m.symbols['_viewer_session_storage'];m.uc.mem_write(state+4,b'\1\0')
 assert m.begin()==2 and m.step()==2 and m.bank('move',[0])==2 and m.bank('stop')==2 and not m.calls
 rows.append(dict(case='busy-guard',passed=True))
 names=['standalone/check_viewer_session_linked.py','standalone/check_viewer_file_linked.py','standalone/dos_image.py']
 r=dict(passed=True,binary_sha256=sha(binary),inputs=len(rows),cases=rows,bounded_steps=step_count,max_DOS_data_calls_per_step=1,
  sources={**manifest['sources'],**{n:sha(ROOT/n) for n in names}},original_inputs=[],
  scope=__doc__+' Actual controller/decoder/owner/admission/assembly execute; DOS responses are modeled. Every observed loading step permits at most one read or seek. Test open/read/seek/close/release faults, non-feeding failed read, retained quarantine/claim, no blind retries, cancellation, foreign-owner protection, far spans/aliases, busy guard, current/target/read-ahead invariants and ABI. No UI/UART/hardware acceptance.')
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS',len(rows),'controller cases,',step_count,'bounded steps')
if __name__=='__main__':main()
