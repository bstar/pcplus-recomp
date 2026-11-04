#!/usr/bin/env python3
"""Actual DOS8086 Alt-T, live parser/underlay, local dismissal and passive video."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True);a=p.parse_args()
assert re.fullmatch('[a-z0-9-]+',a.label)
binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_elapsed_view']
out=ROOT/'build/elapsed-view-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
watcher=out/'ELAPW.COM';subprocess.run(['nasm','-fbin',str(ROOT/'standalone/elapsed_watch.asm'),'-o',str(watcher)],check=True)
harness.BINARY=binary
raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5);struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5);struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,0,0);struct.pack_into('<H',raw,0x1e6,0)
cases=[]
for mode,resume in [('direct','x'),('reference','a-x'),('partial-parser','escape'),('sustained','x')]:
 name=a.label+'-'+mode;keys='p900 enter p5000 ';triggers=[]
 if mode=='partial-parser':keys+='d i r t y p200 ';triggers=[(b'dirty',((0,b'\x1b['),(.8,b'7;1H')))]
 keys+=('a-z p200 ' if mode=='reference' else '')+'a-t '+('p12000 ' if mode=='sustained' else 'p3500 ')+resume+' p500 r e a d y enter p1000 a-x'
 updates=[(6,b'\x1b[2;3HUNDERLAY\x1b[6n'),(6.8,b'\x1b[12;30HINNER\x1b[6n')]
 if mode=='sustained':
  updates += [(5.5+i*.125,b'\x1b[4;1HP%03d '%i+b'X'*55+b'\x1b[6n') for i in range(64)]
  updates.sort(key=lambda row:row[0])
 result=harness.run(name,'success',keys,prm=bytes(raw),com=3,irq=5,cpu='8086',working_drive='d',arguments='@D:\\TEST.PRM /D:CaseTest:23 /I:3',timeout=35,files={'ELAPW.COM':watcher.read_bytes()},observer='ELAPW',online_updates=tuple(updates),online_triggers=tuple(triggers))
 assert result['passed'],result
 folder=ROOT/'build/connection-dos'/name;frames=(folder/'ELAPSED.BIN').read_bytes();assert len(frames)==8000
 for frame in (frames[:4000],frames[4000:]):
  def text(row,col,count):return frame[row*160+col*2:row*160+(col+count)*2:2]
  assert text(12,27,23)==b'ELAPSED TIME THIS CALL:'
  assert re.fullmatch(rb'\d\d:\d\d:\d\d',text(10,30,8)) and re.fullmatch(rb'\d\d/\d\d/\d\d',text(10,47,8))
  assert re.fullmatch(rb'\d\d:\d\d:\d\d',text(12,51,8))
  assert frame[(14*80+25)*2:(14*80+25)*2+2]==b'\xc8\x1f'
 wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
 assert b'\x1b[2;11R' in wire and b'\x1b[12;35R' in wire and wire.count(b'ready\r')==1
 assert b'x' not in wire and b'\x13' not in wire and b'\x11' not in wire
 assert screen[(1*80+2)*2:(1*80+10)*2:2]==b'UNDERLAY'
 assert screen[(11*80+29)*2:(11*80+34)*2:2]==b'INNER'
 if mode=='sustained':
  assert wire.count(b'\x1b[4;61R')==64
  assert screen[(3*80)*2:(3*80+5)*2:2]==b'P063 '
 cases.append(dict(case=mode,passed=True,result=str((folder/'result.json').relative_to(ROOT)),video_sha256=hashlib.sha256(frames).hexdigest()))
report=dict(passed=True,terminal_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),cases=cases,scope=__doc__+' Independent timer ISR only observes cells; real COM3/IRQ5 UART and DOS time. Synthetic serial Hayes peer, no physical/SIP/DSP acceptance or exact original pixel equivalence.')
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS actual DOS elapsed view:',len(cases),'workflows')
