#!/usr/bin/env python3
"""Five-minute actual DOS receive/render/reply and modal-input endurance check."""
import argparse,hashlib,json,re,struct
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True)
p.add_argument('--seconds',type=int,default=300,help='300 for the acceptance run; shorter values are diagnostics')
a=p.parse_args();assert re.fullmatch('[a-z0-9-]+',a.label) and 10<=a.seconds<=600
binary=a.terminal.resolve();assert binary.is_relative_to(ROOT/'build') and binary.name=='TERMINAL.EXE'
out=ROOT/'build/terminal-endurance'/a.label;assert not out.exists();out.mkdir(parents=True)
harness.BINARY=binary
raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5)
manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['binary_sha256']==hashlib.sha256(binary.read_bytes()).hexdigest()
if manifest.get('experimental_display_startup'):
 for at,value in ((0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0)):struct.pack_into('<H',raw,at,value)
struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
struct.pack_into('<HH',raw,0x1bc,0,0);struct.pack_into('<H',raw,0x1e6,0);struct.pack_into('<HH',raw,0x198,1,1)
updates=[];replies=[];last={}
for step in range(a.seconds*2+1):
 row=2+step%16;text=(f'FRAME {step:04d} ROW {row:02d} '+''.join(chr(65+(step+i)%26) for i in range(79))).encode()[:79]
 updates.append((step*.5,f'\x1b[{row};1H'.encode()+text+b'\x1b[6n'));replies.append(f'\x1b[{row};80R'.encode());last[row]=text
# Open/close the real command window while the receive stream continues.
keys='p900 enter p3500 a-z p1500 escape p1500 r e a d y enter '
remaining=(a.seconds+10)*1000
while remaining:delay=min(60000,remaining);keys+=f'p{delay} ';remaining-=delay
keys+='a-x'
name=a.label+'-stream';assert not (ROOT/'build/connection-dos'/name).exists()
native=harness.run(name,'success',keys,prm=bytes(raw),com=3,irq=5,cpu='8086',working_drive='d',
 arguments='@D:\\TEST.PRM /D:CaseTest:23 /I:3',timeout=a.seconds+45,flow_updates=tuple(updates))
folder=ROOT/'build/connection-dos'/name;wire=(folder/'serial.bin').read_bytes().replace(b'\x11',b'').replace(b'\x13',b'')
actual=re.findall(rb'\x1b\[\d+;\d+R',wire)
assert native['passed'],native
assert actual==[b'\x1b[1;16R']+replies,(len(actual),len(replies))
assert wire.count(b'ready\r')==1 and wire.count(b'\x1b[?1;2c')==1
assert (folder/'flow-payload.bin').read_bytes()==b''.join(chunk for _,chunk in updates)
screen=(folder/'SCREEN.BIN').read_bytes()
for row,text in last.items():
 at=(row-1)*160;assert screen[at:at+158:2]==text,(row,'glyphs');assert screen[at+1:at+158:2]==bytes([7])*79,(row,'attributes')
r=dict(passed=True,acceptance_duration=a.seconds>=300,seconds=a.seconds,frames=len(updates),terminal_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),checks=['every CPR in order','all scheduled receive bytes','final glyphs and attributes','modal return','keyboard ready once','PRM unchanged','UART/vector restoration'],native_result=str((folder/'result.json').relative_to(ROOT)),scope='Actual DOS8086 COM3/IRQ5 with BOTH flow selected; synthetic paced UART peer, not live BBS/SIP/audio or physical throughput.')
(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS endurance:',a.seconds,'seconds,',len(updates),'frames')
