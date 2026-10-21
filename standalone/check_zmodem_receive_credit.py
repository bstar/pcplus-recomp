#!/usr/bin/env python3
"""Source-only receive-credit API, exact wire and pre-side-effect admission."""
import argparse,ctypes as C,hashlib,json,subprocess
from pathlib import Path
from check_zmodem import ROOT,Fixture,Session,P,U,h,offer,payload
from check_zmodem_window import WindowPeer


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline-library',type=Path);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 sources=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c')]
 library=out/'session.so';subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',*[str(p) for p in sources],'-o',str(library)],check=True)
 lib=C.CDLL(str(library));lib.zm_run_profile.argtypes=[P,P,P,U,U,U];lib.zm_run.argtypes=[P,P,P,U];lib.zm_run_link.argtypes=[P,P,P,U,U]
 rows=[]
 def receive(credit,body,fmt=67,api='profile',owned_lib=lib):
  wire=offer('TEST.BIN',len(body),fmt)+(payload(body,0,fmt) if body else b'')+h(11,len(body),fmt)+h(8)+b'OO'
  f=Fixture(owned_lib,wire);f.session=Session()
  args=[C.byref(f.session),C.byref(f.ops),None,0]
  r=owned_lib.zm_run(*args) if api=='plain' else owned_lib.zm_run_link(*args,300) if api=='link' else owned_lib.zm_run_profile(*args,300,credit)
  expected=h(1,0x23000000|(credit or 8192))+h(9)+(h(3,len(body)) if body else b'')+h(1,0x23000000|(credit or 8192))+h(8)
  assert r==0 and not f.errors and f.received=={'TEST.BIN':body} and f.tx==expected
  assert f.session.files==1 and f.session.bytes==len(body) and f.session.capacity==credit
  return f
 for credit in (0,1,7,127,128,255,256,511,512,1023,1024,1025,4096,8191,8192):
  for fmt in (65,67):
   for body in (b'',b'A\0\x18^"\r\xff'):
    receive(credit,body,fmt);rows.append(dict(case='exact_receive_credit',credit=credit,format=fmt,bytes=len(body),passed=True))
 body=bytes(range(256))*32
 f=receive(1,body);rows.append(dict(case='peer_ignoring_credit_still_bounded8KiB_packet',credit=1,bytes=len(body),passed=True))
 for credit,sending,floor in [(8193,0,300),(65535,0,300),(65536,0,300),(1,1,300),(8192,1,300),(0,2,300),(256,0,299)]:
  f=Fixture(lib);f.session=Session();C.memset(C.byref(f.session),0xa5,C.sizeof(f.session));before=bytes(f.session)
  assert lib.zm_run_profile(C.byref(f.session),C.byref(f.ops),None,sending,floor,credit)==2
  assert bytes(f.session)==before and not f.events and not f.tx and not f.errors
  rows.append(dict(case='invalid_before_mutation_or_callbacks',credit=credit,sending=sending,floor=floor,passed=True))
 for args in [(None,None,None,0,300,256),(None,None,None,1,300,256)]:assert lib.zm_run_profile(*args)==2
 rows.append(dict(case='null_arguments_rejected',passed=True))
 for api in ('plain','link','profile'):
  receive(0,b'UNCHANGED',api=api);rows.append(dict(case='default8192_wire_'+api,passed=True))
 for floor in (0,300,1200):
  f=WindowPeer(lib,bytes(range(256))*9);f.session=Session()
  assert lib.zm_run_profile(C.byref(f.session),C.byref(f.ops),None,1,floor,0)==0
  assert bytes(f.file)==f.body and not f.errors and not f.buffer and not f.rx
  rows.append(dict(case='sending_peer_negotiation_unchanged',floor=floor,passed=True))
 if a.baseline_library:
  baseline=a.baseline_library.resolve();assert baseline.is_relative_to(ROOT/'build')
  old=C.CDLL(str(baseline));old.zm_run.argtypes=[P,P,P,U];old.zm_run_link.argtypes=[P,P,P,U,U]
  for api in ('plain','link'):
   before=receive(0,b'BASELINE\0\xff',api=api,owned_lib=old);after=receive(0,b'BASELINE\0\xff',api=api)
   assert before.tx==after.tx and before.received==after.received and before.events==after.events
   rows.append(dict(case='source_built_predecessor_default_'+api,passed=True))
 result=dict(passed=True,cases=rows,case_count=len(rows),library_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
  baseline_library_sha256=hashlib.sha256(a.baseline_library.read_bytes()).hexdigest() if a.baseline_library else None,
  inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),*sources,*[ROOT/'src/transfer'/n for n in ('zmodem.h','zmodem_wire.h','zmodem_name.h','batch_header.h')],ROOT/'standalone/check_zmodem.py',ROOT/'standalone/check_zmodem_window.py']},
  scope='Strict C89 source-built host API with typed fixture callbacks and independent exact wire. Credits/default wrappers, empty/binary bodies, full8KiB peer packet despite smaller offer, invalid admission before effects, unchanged sender negotiation and optional source-built predecessor comparison. No actual DOS/16-bit callback/UI/UART/BBS/audio/hardware acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'case_count':len(rows)}))


if __name__=='__main__':main()
