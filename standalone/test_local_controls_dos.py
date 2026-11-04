#!/usr/bin/env python3
"""Actual DOS original local keys/menu actions while a serial peer queries state."""
import argparse,hashlib,json,re,struct
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True);a=p.parse_args()
assert re.fullmatch('[a-z0-9-]+',a.label);binary=a.terminal.resolve();assert binary.is_relative_to(ROOT/'build');harness.BINARY=binary
out=ROOT/'build/local-controls-dos'/a.label;assert not out.exists();out.mkdir(parents=True)
raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5);struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,0,0);struct.pack_into('<H',raw,0x1e6,0)
banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c';cases=[]
for mode in ('direct','reference','partial-parser'):
 def key(k):return ('a-z p150 ' if mode=='reference' else '')+k
 prefix='p900 enter p5000 '
 if mode=='partial-parser':prefix+='d i r t y p300 '
 keys=prefix+key('a-c')+' p1500 c l r p1000 '+key('a-u')+' p200 r s t p1000 '+key('a-e')+' p200 e c h o p1000 '+key('a-e')+' p200 q u i e t p1000 f i n i s h p1300 a-x'
 triggers=[]
 if mode=='partial-parser':triggers.append((b'dirty',((0,b'\x1b['),(1,b'5;8H'))))
 triggers += [(b'clr',b'\x1b[6n\x1b[8;19HRESETME\x1b[31;1m\x1b[?7l'),(b'rst',b'\x1b[6n'),(b'echo',b'\x1b[6n'),(b'quiet',b'\x1b[6n'),(b'finish',banner)]
 name=a.label+'-'+mode;assert not (ROOT/'build/connection-dos'/name).exists()
 native=harness.run(name,'success',keys,prm=bytes(raw),com=3,irq=5,cpu='8086',working_drive='d',arguments='@D:\\TEST.PRM /D:CaseTest:23 /I:3',online_triggers=tuple(triggers),timeout=35)
 assert native['passed'],native
 folder=ROOT/'build/connection-dos'/name;wire=(folder/'serial.bin').read_bytes();replies=re.findall(rb'\x1b\[\d+;\d+R',wire)
 assert replies==[b'\x1b[1;16R',b'\x1b[1;1R',b'\x1b[1;1R',b'\x1b[1;5R',b'\x1b[1;5R',b'\x1b[1;16R'],replies
 assert b'clr' in wire and b'rst' in wire and wire.count(b'echo')==1 and wire.count(b'quiet')==1
 screen=(folder/'SCREEN.BIN').read_bytes();assert screen[1:31:2]==bytes([7])*15,'Reset did not restore the captured normal color'
 cases.append(dict(case=mode,passed=True,result=str((folder/'result.json').relative_to(ROOT))))
r=dict(passed=True,terminal_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),cases=cases,scope='Actual DOS8086 COM3/IRQ5 direct/Alt-Z local controls, partial-CSI deferral, real keyboard/serial CPR and reset color, full/half echo, PRM and hardware restoration. Synthetic peer; not physical or full emulation parity.')
(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS actual DOS local controls:',len(cases),'workflows')
