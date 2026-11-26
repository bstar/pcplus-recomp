#!/usr/bin/env python3
"""Actual 8086 DOS parent online in each admitted ANSI-family profile.

The --ansi-profiles parent imports the PRM terminal id, reaches the synthetic
modem's CONNECT, then (after a typed byte) receives a BBS-style VT100 screen:
DEC line drawing, SGR, a scroll region, DECSC/DECRC and origin mode, followed
by primary DA, secondary DA and DSR-CPR queries. The replies must be exactly
the recovered per-id ones and the drawn screen the same in every profile.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Recovered reports: primary from the DA table, secondary from the native
# L_e9ec branch (ids 4 and 11 '1;10;0', id5 '24;10;0', id9 '4', otherwise none).
PRIMARY={2:b'1;2',3:b'6',4:b'62;2',5:b'63;2',6:b'1;2',7:b'1;2',8:b'1;0',9:b'7;5;1',10:b'1;2',11:b'62;2'}
SECONDARY={4:b'1;10;0',5:b'24;10;0',9:b'4',11:b'1;10;0'}
LABEL={2:'VT100',3:'VT102',4:'VT220',5:'VT320',6:'ANSI',7:'IBM PC',8:'WYSE 75',9:'ATT 605',10:'ATT 4410',11:'TVI 922'}
REFUSAL={False:'Configuration terminal profile must be ANSI or VT220.',True:'Terminal profile must be an ANSI-family id (2 to 11).'}
BBS=(b'\x1b[2J\x1b[H\x1b[0;1;37;44m MODERN BBS \x1b[0m\r\n'
     b'\x1b(0lqqqqk\x1b(B\r\n\x1b(0x\x1b(BMENU\x1b(0x\x1b(B\r\n\x1b(0mqqqqj\x1b(B\r\n'
     b'\x1b[5;20r\x1b[20;1H\x1b7\x1b[1;31mSAVED\x1b8\x1b[0m\r\nscroll\r\n\x1b[r'
     b'\x1b[10;10H\x1b[K[M]ail [F]iles [G]oodbye: ')
QUERY=b'\x1b[c\x1b[>c\x1b[6n'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True)
 p.add_argument('--profile',type=int,choices=range(33),required=True)
 p.add_argument('--expect-refused',action='store_true',help='Startup must refuse the PRM profile with exit 7 and no modem traffic');a=p.parse_args()
 binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text())
 assert sha(binary)==m['binary_sha256'];widened=bool(m.get('experimental_ansi_profiles'))
 assert a.expect_refused==(a.profile not in (range(2,12) if widened else (4,6)))
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 harness.BINARY=binary;label=f'ansi-{sha(binary)[:8]}-{a.profile}'+('-refused' if a.expect_refused else '');out=ROOT/'build/ansi-profiles-dos'/label;out.mkdir(parents=True,exist_ok=False)
 raw=bytearray(fixture(timeout=5));struct.pack_into('<H',raw,0x194,a.profile)
 # Display, mouse and sound words the full parent imports (the fixture's A5A5
 # sentinel stops its display-startup transaction). The minimal parent ignores them.
 for off,value in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',raw,off,value)
 if a.expect_refused:
  result=harness.run(label,'reject','p3000',prm=bytes(raw),com=1,cpu='8086',working_drive='d',expected=7,
   arguments='@D:\\TEST.PRM /D:CaseTest:23',timeout=30)
  screen=(ROOT/'build/connection-dos'/label/'screen.txt').read_text()
  checks=dict(harness=result['passed'],message=REFUSAL[widened] in screen)
  record=dict(passed=all(checks.values()),profile=a.profile,refused=True,checks=checks,terminal_sha256=sha(binary),original_inputs=[],
   parent_result=str((ROOT/'build/connection-dos'/label/'result.json').relative_to(ROOT)))
  (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
  assert record['passed'],(checks,result['checks'],screen)
  print('PASS refused profile',a.profile);return
 result=harness.run(label,'success','p900 enter p5000 z p2500 a-x',prm=bytes(raw),com=1,cpu='8086',working_drive='d',
  profile=a.profile,arguments='@D:\\TEST.PRM /D:CaseTest:23',timeout=30,online_triggers=((b'z',((0,BBS+QUERY),)),))
 folder=ROOT/'build/connection-dos'/label;wire=(folder/'serial.bin').read_bytes()
 screen=(folder/'SCREEN.BIN').read_bytes();rows=[screen[i*160:i*160+160:2].decode('cp437') for i in range(25)]
 primary=b'\x1b[?'+PRIMARY[a.profile]+b'c';secondary=b'\x1b[>'+SECONDARY.get(a.profile,b'')+b'c'
 checks=dict(harness=all(v for k,v in result['checks'].items() if k!='immediate_banner_not_dropped'),primary_da_twice=wire.count(primary)==2,
  no_other_primary_da=len(re.findall(rb'\x1b\[\?[0-9;]*c',wire))==2,
  secondary_da_once=wire.count(secondary)==1 and len(re.findall(rb'\x1b\[>[0-9;]*c',wire))==1,
  cpr_after_menu=b'\x1b[10;36R' in wire,
  line_drawing=(rows[1][:6],rows[2][:6],rows[3][:6])==(('\u250c\u2500\u2500\u2500\u2500\u2510','\u2502MENU\u2502','\u2514\u2500\u2500\u2500\u2500\u2518') if m.get('experimental_dec_graphics') else ('lqqqqk','xMENUx','mqqqqj')),
  scroll_region=rows[17].startswith('SAVED') and rows[18].startswith('scroll'),
  menu=rows[9].startswith('         [M]ail [F]iles [G]oodbye:'))
 record=dict(passed=all(checks.values()),profile=a.profile,checks=checks,terminal_sha256=sha(binary),wire_sha256=sha(folder/'serial.bin'),
  drawn_rows_sha256=hashlib.sha256('\n'.join(rows[:24]).encode()).hexdigest(),status_row=rows[24].rstrip(),screen_rows=rows,
  parent_result=str((folder/'result.json').relative_to(ROOT)),original_inputs=[],
  checker_inputs={str(q.relative_to(ROOT)):sha(q) for q in [Path(__file__),ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/modem_fixtures.py']},
  scope=__doc__.strip()+' Actual COM1 UART in DOSBox-X 8086; synthetic modem peer; no physical modem, BBS deployment or VT52/DECANM switch.')
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
 assert record['passed'],json.dumps(dict(checks=checks,status=rows[24],rows=rows[:12],harness=result['checks']),indent=1)
 print('PASS ansi profile',a.profile,LABEL[a.profile])
if __name__=='__main__':main()
