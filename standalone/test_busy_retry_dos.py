#!/usr/bin/env python3
"""Prove BUSY releases the DOS terminal and allows a same-process redial.

Uses a synthetic Hayes peer; no live ATA, bridge, BBS or physical PC changes.
The old and current release can be selected explicitly for differential checks.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True)
 a=p.parse_args();assert re.fullmatch('[a-z0-9-]+',a.label)
 binary=a.terminal.resolve();assert binary.is_relative_to(ROOT/'build') and binary.name=='TERMINAL.EXE'
 out=ROOT/'build/busy-retry-dos'/a.label;assert not out.exists();out.mkdir(parents=True)
 harness.BINARY=binary
 raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5)
 struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
 struct.pack_into('<HH',raw,0x4e4,8,4)
 struct.pack_into('<HH',raw,0x1bc,0,0)
 struct.pack_into('<H',raw,0x1e6,0)
 m=json.loads((binary.parent/'manifest.json').read_text())
 assert m['binary_sha256']==hashlib.sha256(binary.read_bytes()).hexdigest()
 if m.get('experimental_display_startup'):
  for at,value in ((0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0)):struct.pack_into('<H',raw,at,value)
 redial='` p500 right p500 d' if m.get('experimental_original_reference') else 'a-d'
 cases=[]
 for kind,mode,keys in [
  ('busy-exit','busy','p900 enter p5000 a-x'),
  ('busy-redial','redial','p900 enter p6500 '+redial+' p9000 a-x'),
  ('three-calls','hangup','p900 enter p5000 o n e enter a-h p2500 '+redial+' p7000 t w o enter a-h p2500 '+redial+' p7000 t h r e e enter a-x')]:
  name=a.label+'-'+kind;assert not (ROOT/'build/connection-dos'/name).exists()
  result=harness.run(name,mode,keys,prm=bytes(raw),com=3,irq=5,cpu='8086',
    arguments='@D:\\TEST.PRM /D:CaseTest:23 /I:3',working_drive='d',timeout=30)
  assert result['passed'],result
  if kind=='three-calls':
   assert result['commands']==['ATZ','ATDCaseTest:23']*3,result['commands']
   wire=(ROOT/'build/connection-dos'/name/'serial.bin').read_bytes()
   assert wire.count(b'\x1b[1;16R')==3 and wire.count(b'\x1b[?1;2c')==3
   assert all(wire.count(value+b'\r')==1 for value in (b'one',b'two',b'three'))
  cases.append({'case':kind,'passed':True,'result':str((ROOT/'build/connection-dos'/name/'result.json').relative_to(ROOT))})
 report={'passed':True,'terminal_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'cases':cases,
  'sources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('standalone/test_busy_retry_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py')},
  'scope':'Actual8086 DOS COM3/IRQ5 current-keyboard/controller execution. BUSY followed by bounded exit, and BUSY then explicit same-process successful redial with real parser replies, screen, PRM and hardware restoration. Three successful calls with intervening local hangups also check repeated replies and distinct keyboard input. Synthetic serial modem; not physical lockup reproduction.'}
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS BUSY cleanup and same-process retry')
if __name__=='__main__':main()
