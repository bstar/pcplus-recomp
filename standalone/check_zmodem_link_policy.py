#!/usr/bin/env python3
"""Explicit carrier-floor API and reply policy with an independent wire peer."""
import ctypes as C
import hashlib,json,subprocess
from pathlib import Path
from check_zmodem import Session,P,U
from check_zmodem_window import WindowPeer

ROOT=Path(__file__).resolve().parents[1]


class Observed(WindowPeer):
 def __init__(self,*args,**kw):
  self.response_reads=[]
  super().__init__(*args,**kw)
 def read(self,ctx,seconds):
  if self.session.phase==3 and self.session.owned==1:
   self.response_reads.append({'seconds':seconds,'confirmed':self.session.position,
    'wire_payload':self.cursor,'window':self.session.window,'block':self.session.block})
  return super().read(ctx,seconds)


def main():
 out=ROOT/'build/zmodem-link-policy';out.mkdir(exist_ok=True)
 sources=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c')]
 libpath=out/'session.so'
 subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',
  '-shared','-fPIC',*[str(p) for p in sources],'-o',str(libpath)],check=True)
 lib=C.CDLL(str(libpath));lib.zm_run_link.argtypes=[P,P,P,U,U]
 rows=[]
 for flags in (2,3):
  for floor in (0,300,1200,65535):
   f=Observed(lib,bytes(range(256))*73,flags=flags)
   f.session=Session();status=lib.zm_run_link(C.byref(f.session),C.byref(f.ops),None,1,floor)
   assert status==0 and not f.errors and bytes(f.file)==f.body and not f.buffer and not f.rx
   assert f.session.response_bps==floor and f.session.files==1 and f.source is None
   blocking=[r for r in f.response_reads if r['seconds']]
   assert blocking and (all(r['seconds']==3 for r in blocking) if not floor else all(3<r['seconds']<=560 for r in blocking))
   if floor==300:
    assert blocking[0]['seconds']==75
    if flags==3:assert max(r['seconds'] for r in blocking)==560
   rows.append(dict(flags=flags,carrier_floor=floor,passed=True,
    packets=len(f.packets),max_outstanding=f.max_outstanding,
    requested_blocking_seconds=sorted({r['seconds'] for r in blocking}),
    genuine_zero_wait_polls=sum(r['seconds']==0 for r in f.response_reads)))
 for floor,sending in ((1,1),(299,1),(300,2)):
  f=Observed(lib,b'ABC');f.session=Session();C.memset(C.byref(f.session),0xa5,C.sizeof(f.session))
  before=bytes(f.session)
  assert lib.zm_run_link(C.byref(f.session),C.byref(f.ops),None,sending,floor)==2
  assert bytes(f.session)==before and not f.events and not f.tx
  rows.append(dict(case='invalid-policy-before-side-effects',floor=floor,sending=sending,passed=True))
 result=dict(passed=True,cases=rows,checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
  scope='Strict C89 host engine, typed carrier-floor ABI and independent reactive Python wire/CRC peer. Exact file, bounded overlap, genuine polls, reply requests at zero/300/1200/65535bps policies, invalid policy rejects before side effects. Not DOS, audio or physical evidence.')
 (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',len(rows),'carrier reply policy cases')


if __name__=='__main__':main()
