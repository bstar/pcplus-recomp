#!/usr/bin/env python3
"""Actual DOS KEY import, BIOS Alt-digit invocation and UART TEXT output."""
import hashlib,json,struct
from test_connection_dos import run,ROOT,BINARY
from modem_fixtures import fixture

def main():
 cases=[]
 settings=bytearray(fixture(timeout=5));settings[0x1e2]=ord('~')
 def table(first=b'',last=b'',kind=3):
  image=bytearray(540)
  for index in range(10):struct.pack_into('<H',image,index*54,3)
  struct.pack_into('<H',image,0,kind);image[2:2+len(first)]=first
  image[488:488+len(last)]=last
  return bytes(image)
 def check(name,data,keys,wanted=None,expected=0,mode='success'):
  proof=run('meta-'+name,mode,keys,prm=bytes(settings),arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\TEST.KEY',expected=expected,files={'TEST.KEY':data})
  folder=ROOT/'build/connection-dos'/('meta-'+name);wire=(folder/'serial.bin').read_bytes()
  if wanted is not None:proof['checks']['TEXT_wire']=wanted in wire
  proof['passed']=all(proof['checks'].values());(folder/'result.json').write_text(json.dumps(proof,indent=2)+'\n');cases.append(proof)
  print(name,'PASS' if proof['passed'] else json.dumps(proof),flush=True)
 check('Alt1-Alt0-caret-binary',table(b'ONE^@^^^~END^M',b'ZERO^^^M'), 'p3000 a-1 p120 x p1500 a-0 p1500 a-x', b'ONE\0^END\rxZERO^M')
 check('embedded-decoded-NUL',table(b'A^`HIDDEN'), 'p3000 a-1 p600 z p500 a-x', b'Az')
 check('unsafe-dangling-caret',table(b'DONT-SEND^'), 'p3000 a-1', expected=4)
 check('unsupported-program',table(b'NOEXEC.EXE',kind=1), 'p3000 a-1',expected=4)
 for name,data in [('short',bytes(539)),('suffix',bytes(541)),('bad-kind',table(kind=4)),('unterminated',struct.pack('<H',3)+b'X'*52+table()[54:])]:
  check(name,data,'p500 a-x',expected=7,mode='reject')
 summary={'passed':all(c['passed'] for c in cases),'cases':cases,'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'scope':'Actual DOS startup KEY validation, BIOS Alt1/Alt0, bounded recovered caret expansion, pause and deferred ordinary key, wire NUL and UART/IRQ restoration. Synthetic records only; no physical modem or ASPECT/PROGRAM/HOOK executor.'}
 out=ROOT/'build/meta-actions-dos';out.mkdir(parents=True,exist_ok=True);(out/'checks.json').write_text(json.dumps(summary,indent=2)+'\n')
 return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
