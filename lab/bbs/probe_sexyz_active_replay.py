#!/usr/bin/env python3
"""Unmodified stock helper versus checked host receiver with paced input.

Explicit experiment: wrapper replaces complete ZRINIT offers with selected
flags/credit. This is not native policy negotiation, DOS, DSP/audio or a BBS run.
"""
import argparse,ctypes as C,hashlib,json,select,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from check_zmodem import P,U,Session,h
from check_zmodem_active_replay import Checked,VERIFY
from audit_zmodem import scan,audit_batch,audit_controls
from prepare_audio_pressure_download import NAME,payload

STOCK_SHA='d1aeb1347fee332be75dd638dd4cb10a1bf7c418d96d0ebb79ca90470b0ed4bd'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class Paced(Checked):
 def __init__(self,lib,peer,bps,credit,flags,out):
  super().__init__(lib,b'');self.peer=peer;self.bps=bps;self.offer=(flags<<24)|credit
  self.next_byte=time.monotonic();self.deadline=self.next_byte+1800
  self.trace=[];self.offers=[];self.base=self.next_byte;self.log=(out/'trace.jsonl').open('w',buffering=1)
 def event(self,direction,offset,count):
  row=dict(direction=direction,offset=offset,size=count,seconds=time.monotonic()-self.base)
  self.trace.append(row);self.log.write(json.dumps(row)+'\n')
 def read(self,context,seconds):
  if time.monotonic()>self.deadline:return 65533
  if not select.select([self.peer.stdout],[],[],seconds)[0]:return 65535
  value=self.peer.stdout.read(1)
  if not value:return 65534
  self.next_byte=max(time.monotonic(),self.next_byte)+10/self.bps
  time.sleep(max(0,self.next_byte-time.monotonic()))
  at=len(self.peer_wire);self.peer_wire.extend(value);self.engine_wire.extend(value)
  self.event('bbs',at,1);return value[0]
 def write(self,context,pointer,count):
  data=C.string_at(pointer,count);headers=list(scan(data))
  if len(headers)==1 and headers[0]['type']==1 and headers[0]['offset']==0 and headers[0]['end']==len(data):
   updated=h(1,self.offer);self.offers.append(dict(original_hex=data.hex(),replacement_hex=updated.hex()))
   data=updated;pointer=C.create_string_buffer(data);count=len(data)
  self.event('dos',len(self.tx),count)
  return super().write(context,pointer,count)
 def append(self,context,pointer,count):
  result=super().append(context,pointer,count)
  size=len(self.stage or b'')
  if not result and (size//8192!=(size-count)//8192):print(json.dumps(dict(verified_bytes=size,seconds=time.monotonic()-self.base)),flush=True)
  return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--bps',type=int,default=1200);p.add_argument('--credit',type=int,default=256)
 p.add_argument('--flags',type=int,choices=(1,3,33,35),default=33);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists() and 300<=a.bps<=14400 and 1<=a.credit<=8192
 out.mkdir(parents=True);helper=ROOT/'build/bbs-lab/enigma/helpers/sexyz';assert sha(helper)==STOCK_SHA
 source=payload();(out/NAME).write_bytes(source)
 sources=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c')]
 inputs=[*sources,*[ROOT/'src/transfer'/n for n in ('zmodem.h','zmodem_wire.h','zmodem_name.h','batch_header.h')],
  ROOT/'standalone/check_zmodem.py',ROOT/'standalone/check_zmodem_active_replay.py',ROOT/'standalone/check_zmodem_wire.py',
  ROOT/'lab/bbs/audit_zmodem.py',ROOT/'lab/bbs/prepare_audio_pressure_download.py',Path(__file__).resolve()]
 frozen={str(q.relative_to(ROOT)):sha(q) for q in inputs}
 for q in inputs:
  copy=out/'frozen-source'/q.relative_to(ROOT);copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(q.read_bytes())
 (out/'start.json').write_text(json.dumps(dict(inputs=frozen,helper_sha256=sha(helper),bps=a.bps,credit=a.credit,flags=a.flags),indent=2)+'\n')
 library=out/'session.so';subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',*map(str,sources),'-o',str(library)],check=True)
 lib=C.CDLL(str(library));lib.zm_run_checked_profile.argtypes=[P,P,P,U,U,U,VERIFY]
 f=None;peer=None;status=None;error=None
 with (out/'helper.stderr').open('w') as log:
  try:
   peer=subprocess.Popen([str(helper),'-raw','-8','sz',NAME],cwd=out,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,bufsize=0)
   f=Paced(lib,peer,a.bps,a.credit,a.flags,out);f.session=Session()
   status=lib.zm_run_checked_profile(C.byref(f.session),C.byref(f.ops),None,0,0,a.credit,f.verify)
   peer.wait(timeout=20)
  except BaseException as exc:error=repr(exc)
  finally:
   if peer is not None and peer.poll() is None:peer.kill();peer.wait()
   if f is not None:f.log.close()
   if peer is not None:peer.stdin.close();peer.stdout.close()
 assert f is not None
 (out/'sender.bin').write_bytes(bytes(f.peer_wire));(out/'receiver.bin').write_bytes(bytes(f.tx))
 checks=dict(native_status_zero=status==0,stock_helper_exit_zero=peer.returncode==0,
  exact_received_file=f.received=={NAME:source},no_callback_errors=not f.errors and not f.verify_errors,
  declared_inputs_unchanged=all(sha(ROOT/n)==digest and sha(out/'frozen-source'/n)==digest for n,digest in frozen.items()),
  stock_helper_unchanged=sha(helper)==STOCK_SHA,source_unchanged=(out/NAME).read_bytes()==source,
  all_offers_explicit_and_exact=len(f.offers)>=2 and all(x['position']==f.offer for x in scan(bytes(f.tx)) if x['type']==1))
 protocol=None;protocol_error=None
 try:
  protocol=audit_batch(bytes(f.peer_wire),{NAME:source})
  for file in protocol['files']:assert file.pop('source')==source
  protocol['controls']=audit_controls(protocol,bytes(f.tx),f.trace,'bbs',time.monotonic()-f.base+1)
  checks['complete_independent_source_CRC_finish_opposite_controls']=True
 except BaseException as exc:protocol_error=repr(exc);checks['complete_independent_source_CRC_finish_opposite_controls']=False
 result=dict(passed=all(checks.values()) and error is None,checks=checks,status=status,helper_exit=peer.returncode,error=error,
  protocol_error=protocol_error,protocol=protocol,bps_ceiling=a.bps,credit=a.credit,flags=a.flags,
  callback_errors=f.errors,verify_errors=f.verify_errors,offers=f.offers,readback_operations=[x for x in f.order if x[0]=='verify'],
  session_position=f.session.position,session_bytes=f.session.bytes,session_files=f.session.files,
  source_bytes=len(source),source_sha256=hashlib.sha256(source).hexdigest(),library_sha256=sha(library),helper_sha256=sha(helper),
  inputs=frozen,captures_sha256={q.name:sha(q) for q in out.iterdir() if q.is_file() and q.name!='result.json'},
  original_inputs=[],scope=__doc__,
  limitations=['Paced bytes enter a host C receiver; no UART/FIFO, physical flow-control or DOS file readback.',
   'Stored-prefix comparison is a byte-array callback; native offer policy is explicitly overridden.',
   'Sender runs unchanged in real elapsed time; input delivery adds pacing and may be slower than its declared ceiling.',
   'No BBS menus/accounting, DSP/audio, physical modem or full application acceptance.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=result['passed'],status=status,helper_exit=peer.returncode,verified_position=f.session.position,protocol_error=protocol_error)),flush=True)
 assert result['passed'],result['checks']
if __name__=='__main__':main()
