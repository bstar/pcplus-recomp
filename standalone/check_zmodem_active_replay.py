#!/usr/bin/env python3
"""Checked active-stage replay through source-built C; storage/transport fixtures.

Packet bytes come from the independent Python codec. No DOS/audio/BBS or physical
acceptance. Fixed-input cases assert exact ACK/resume positions and callback ordering.
"""
import argparse,ctypes as C,hashlib,json,subprocess
from pathlib import Path
from check_zmodem import ROOT,Fixture,Session,P,U,D,h,offer,payload

VERIFY=C.CFUNCTYPE(U,P,D,P,U)

class Checked(Fixture):
 def __init__(self,lib,wire,fault=None):
  super().__init__(lib,wire);self.verify_fault=fault;self.order=[];self.verify_errors=[];self.verification_states=[]
  def compare(context,at,data,n):
   try:
    content=C.string_at(data,n);self.order.append(['verify',at,n,content.hex()])
    self.verification_states.append(dict(position=self.session.position,retries=self.session.retries,frontier=self.session.replay_verified))
    assert self.stage is not None and at<=len(self.stage) and n<=len(self.stage)-at
    if self.verify_fault:return self.verify_fault
    return 0 if self.stage[at:at+n]==content else 6
   except BaseException as e:self.verify_errors.append(repr(e));return 7
  self.verify=VERIFY(compare)
 def append(self,context,data,n):
  self.order.append(['append',n]);return super().append(context,data,n)
 def write(self,context,data,n):
  self.order.append(['wire',C.string_at(data,n).hex()]);return super().write(context,data,n)
 def abort(self,context):
  self.aborted=bytes(self.stage or b'');return super().abort(context)
 def run_checked(self,credit=0):
  self.session=Session()
  r=self.lib.zm_run_checked_profile(C.byref(self.session),C.byref(self.ops),None,0,0,credit,self.verify)
  assert not self.errors and not self.verify_errors,(self.errors,self.verify_errors)
  return r

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--baseline-proof',type=Path);p.add_argument('--baseline-sources',type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 sources=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c')]
 library=out/'session.so'
 subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',*[str(s) for s in sources],'-o',str(library)],check=True)
 lib=C.CDLL(str(library));lib.zm_run.argtypes=[P,P,P,U];lib.zm_run_checked_profile.argtypes=[P,P,P,U,U,U,VERIFY]
 rows=[];body=b'ABCDEFGHIJKL'
 def run(label,wire,wanted,status=0,old=None,fault=None,appends=None):
  f=Checked(lib,wire,fault);got=f.run_checked();assert got==status,(label,got,status,f.order)
  assert f.tx==wanted,(label,f.tx.hex(),wanted.hex())
  if not status:
   assert f.received=={'TEST.BIN':body} and f.session.position==len(body)
   assert sum(e[0]=='commit' for e in f.events)==1 and not any(e[0]=='abort' for e in f.events)
  else:
   assert not f.received and f.aborted==old and sum(e[0]=='abort' for e in f.events)==1
  if appends is not None:assert [e[1] for e in f.events if e[0]=='append']==appends,(label,f.events)
  rows.append(dict(case=label,passed=True,status=got,position=f.session.position,events=f.events,order=f.order))
  return f
 ready=h(1,0x23002000);cancel=b'\x18'*8+b'\x08'*10
 for credit in (0,1,128,256,1024,8191,8192):
  for fmt in (65,67):
   f=Checked(lib,offer('CREDIT.BIN',12,fmt)+payload(body,0,fmt)+h(11,12,fmt)+h(8)+b'OO')
   assert f.run_checked(credit)==0 and f.received=={'CREDIT.BIN':body}
   flags=0x21000000 if 0<credit<8192 else 0x23000000
   init=h(1,flags|(credit or 8192))
   assert f.tx==init+h(9)+h(3,12)+init+h(8) and f.session.capacity==credit
   rows.append(dict(case='checked-receive-offer',credit=credit,format=fmt,flags=flags>>24,passed=True))
 start=ready+h(9)+h(3,8);finish=h(1,0x23002000)+h(8)
 for fmt in (65,67):
  prefix=offer('TEST.BIN',len(body),fmt)+payload(body[:8],0,fmt)
  tail=h(11,len(body),fmt)+h(8)+b'OO'
  for ending in (104,105,106,107):
   # G/Q require a continuation packet within the same frame.
   extra=b'' if ending in (104,107) else __import__('check_zmodem_wire').packet(b'GH',fmt,107,0)
   ack=(h(9,8) if ending in (104,106,107) else b'')+(h(3,8) if extra else b'')
   f=run(f'old-prefix-{fmt}-{ending}',prefix+payload(b'CDEF',2,fmt,ending)+extra+payload(body[8:],8,fmt)+tail,
    start+ack+h(3,12)+finish,appends=[8,4])
   assert f.order.index(['verify',2,4,b'CDEF'.hex()])>f.order.index(['append',8])
  for ending in (104,107):
   run(f'overlap-appends-suffix-{fmt}-{ending}',prefix+payload(body[4:],4,fmt,ending)+tail,
    start+(h(3,12) if ending==107 else b'')+finish,appends=[8,4])
  from check_zmodem_wire import packet
  run(f'continued-overlap-{fmt}',prefix+payload(b'CD',2,fmt,106)+packet(b'EF',fmt,106,0)+packet(body[6:],fmt,107,0)+tail,
   start+h(9,8)*2+h(3,12)+finish,appends=[8,4])
  for failure,code in [(6,6),(7,7),(65533,5),(65534,3)]:
   run(f'verifier-failure-{fmt}-{failure}',prefix+payload(b'CDEF',2,fmt)+tail,start+cancel,status=code,old=body[:8],fault=failure,appends=[8])
  run(f'CRC-valid-prefix-mismatch-{fmt}',prefix+payload(b'C!EF',2,fmt)+tail,start+cancel,status=6,old=body[:8],appends=[8])
  damaged=bytearray(payload(b'CDEF',2,fmt));at=len(h(10,2,fmt));damaged[at+1]^=1
  f=run(f'bad-CRC-before-readback-{fmt}',prefix+bytes(damaged)+payload(body[8:],8,fmt)+tail,
   start+h(9,8)+h(3,12)+finish,appends=[8,4])
  assert not any(e[0]=='verify' for e in f.order)
  f=run(f'future-position-not-readback-{fmt}',prefix+payload(b'ZZ',20,fmt)+payload(body[8:],8,fmt)+tail,
   start+h(9,8)+h(3,12)+finish,appends=[8,4])
  assert not any(e[0]=='verify' for e in f.order)
  run(f'bounded-nine-old-packets-{fmt}',prefix+payload(b'CD',2,fmt)*9+payload(body[8:],8,fmt)+tail,
   start+h(9,8)*9+h(3,12)+finish,appends=[8,4])
  run(f'tenth-old-packet-exhausts-budget-{fmt}',prefix+payload(b'CD',2,fmt)*10+tail,
   start+h(9,8)*9+cancel,status=4,old=body[:8],appends=[8])
  run(f'empty-continuation-rejects-{fmt}',prefix+payload(b'',2,fmt,106)+tail,
   start+cancel,status=6,old=body[:8],appends=[8])
 # Verified recovery endpoints may progress without changing accepted position.
 body=bytes(range(256))*4
 prefix=offer('TEST.BIN',len(body))+payload(body[:512])
 oldframes=b''.join(payload(body[i:i+16],i) for i in range(0,256,16))
 tail=payload(body[512:],512)+h(11,len(body))+h(8)+b'OO'
 frontier_wire=prefix+oldframes+tail
 f=run('sixteen-advancing-old-packets',frontier_wire,
  ready+h(9)+h(3,512)+h(9,512)*16+h(3,1024)+finish,appends=[512,512])
 assert len(f.verification_states)==16 and all(s['position']==512 for s in f.verification_states)
 run('advancing-frontier-does-not-waive-repeated-endpoint-budget',prefix+oldframes[:len(payload(body[:16]))]+payload(body[16:32],16)*11,
  ready+h(9)+h(3,512)+h(9,512)*11+cancel,status=4,old=body[:512],appends=[512])
 baseline=None
 if a.baseline_proof:
  assert a.baseline_sources
  proof=a.baseline_proof.resolve();folder=a.baseline_sources.resolve()
  assert proof.is_relative_to(ROOT/'build') and folder.is_relative_to(ROOT/'build')
  receipt=json.loads(proof.read_text());old_library=proof.parent/'session.so'
  assert receipt['passed'] and hashlib.sha256(old_library.read_bytes()).hexdigest()==receipt['library_sha256']
  for name,digest in receipt['inputs'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest,name
  previous_lib=C.CDLL(str(old_library));previous_lib.zm_run_checked_profile.argtypes=[P,P,P,U,U,U,VERIFY]
  previous=Checked(previous_lib,frontier_wire);old_status=previous.run_checked()
  assert old_status==4 and not previous.received and previous.aborted==body[:512] and previous.session.position==512
  assert previous.tx==ready+h(9)+h(3,512)+b''.join(h(3,i) for i in range(16,145,16))+cancel
  baseline=dict(proof=str(proof.relative_to(ROOT)),proof_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),
   library_sha256=receipt['library_sha256'],frozen_source_root=str(folder.relative_to(ROOT)),
   reproduced_status=old_status,verified_position=previous.session.position,all_baseline_source_hashes_verified=True)
  rows.append(dict(case='verified-predecessor-fails-advancing-recovery',passed=True,status=old_status))
 # Offset and suffix arithmetic must remain32-bit across the64KiB boundary.
 body=bytes((i*73+(i>>8)*19+37)&255 for i in range(65549))
 wire=offer('TEST.BIN',len(body))+b''.join(payload(body[i:i+8192],i) for i in range(0,65536,8192))
 run('overlap-across64KiB',wire+payload(body[65530:],65530)+h(11,len(body))+h(8)+b'OO',
  ready+h(9)+b''.join(h(3,i) for i in range(8192,65537,8192))+h(3,len(body))+finish,appends=[8192]*8+[13])
 # Invalid send/verifier policy must reject before session mutation or IO.
 f=Checked(lib,b'');f.session=Session();C.memset(C.byref(f.session),0xa5,C.sizeof(f.session));before=bytes(f.session)
 assert lib.zm_run_checked_profile(C.byref(f.session),C.byref(f.ops),None,1,0,0,f.verify)==2
 assert bytes(f.session)==before and not f.order and not f.events
 rows.append(dict(case='send-verifier-rejected-before-effects',passed=True))
 dependencies=[*sources,*[ROOT/'src/transfer'/n for n in ('zmodem.h','zmodem_wire.h','zmodem_name.h','batch_header.h')],Path(__file__).resolve(),ROOT/'standalone/check_zmodem.py',ROOT/'standalone/check_zmodem_wire.py']
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 result=dict(passed=True,cases=rows,case_count=len(rows),baseline=baseline,library_sha256=sha(library),inputs={str(q.relative_to(ROOT)):sha(q) for q in dependencies},original_inputs=[],scope=__doc__,
  limitations=['Readback is a byte-array fixture, not the DOS file owner.','The normal terminal still uses the legacy API pending checked storage integration.','No unmodified sender scheduling, actual DOS/BBS/audio or physical acceptance.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,case_count=len(rows))))
if __name__=='__main__':main()
