#!/usr/bin/env python3
"""Actual 8086 DOS parent switching ANSI -> VT52 -> ANSI with the host.

A --vt52 parent is online in an admitted ANSI-family profile. After a typed
byte the synthetic peer sends DECANM (ESC[?2l) and a VT52 screen: home/erase,
ESC Y addressing (including the clamp), ESC F/G graphics, cursor moves, EL,
an ANSI CSI that VT52 must not interpret, and ESC Z. The terminal must reply
ESC / Z and send VT52 cursor keys. On the typed Up key the peer sends ESC <,
then ANSI CUP, primary DA and CPR, which must be answered as the configured
profile again; the next Up key must be the ANSI one. ESC < is a clearing
reset (native 20a4(1)), so --stay runs the same VT52 screen without leaving
and checks the drawn rows instead.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PRIMARY={2:b'1;2',3:b'6',4:b'62;2',5:b'63;2',6:b'1;2',7:b'1;2',8:b'1;0',9:b'7;5;1',10:b'1;2',11:b'62;2'}
Y=lambda row,col:b'\x1bY'+bytes((32+row,32+col))
VT52=(b'\x1b[2J\x1b[HANSI FIRST\r\n\x1b[?2l'
      b'\x1bH\x1bJVT52 MODE'
      +Y(2,4)+b'\x1bFlqqk\x1bG'
      +Y(4,0)+b'ABC\x1bD\x1bDX'
      +Y(6,0)+b'\x1b[1mBOLD'
      +Y(8,0)+b'LINE8 TAIL\x1bD\x1bD\x1bD\x1bD\x1bK\x1bAU'
      +Y(60,120)+b'Q'
      +b'\x1bZ'+Y(10,0)+b'PRESS UP')
LEAVE=b'\x1b<\x1b[1;20HANSI OK\x1b[c\x1b[6n'

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True)
 p.add_argument('--profile',type=int,choices=range(2,12),default=2)
 p.add_argument('--stay',action='store_true',help='Stay in VT52 and check the drawn screen');a=p.parse_args()
 binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text())
 assert sha(binary)==m['binary_sha256'] and m.get('experimental_vt52') and m.get('experimental_ansi_profiles')
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 harness.BINARY=binary;label=f'vt52-{sha(binary)[:8]}-{a.profile}'+('-stay' if a.stay else '');out=ROOT/'build/vt52-dos'/label;out.mkdir(parents=True,exist_ok=False)
 raw=bytearray(fixture(timeout=5));struct.pack_into('<H',raw,0x194,a.profile)
 # Display, mouse and sound words the full parent imports (see test_ansi_profiles_dos.py).
 for off,value in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',raw,off,value)
 result=harness.run(label,'success','p900 enter p5000 z p3000 up p3000 up p2500 a-x',prm=bytes(raw),com=1,cpu='8086',working_drive='d',
  profile=a.profile,arguments='@D:\\TEST.PRM /D:CaseTest:23',timeout=40,
  online_triggers=((b'z',((0,VT52),)),)+(()if a.stay else((b'\x1bA',((0,LEAVE),)),)))
 folder=ROOT/'build/connection-dos'/label;wire=(folder/'serial.bin').read_bytes()
 screen=(folder/'SCREEN.BIN').read_bytes();rows=[screen[i*160:i*160+160:2].decode('cp437') for i in range(25)]
 primary=b'\x1b[?'+PRIMARY[a.profile]+b'c'
 tail=wire[wire.find(b'\x1bA')+2:] if b'\x1bA' in wire else b''
 box=('\u250c\u2500\u2500\u2510' if m.get('experimental_dec_graphics') else 'lqqk')
 common=dict(harness=all(v for k,v in result['checks'].items() if k!='immediate_banner_not_dropped'),
  identify_reply=wire.count(b'\x1b/Z')==1 and wire.find(b'\x1b/Z')<wire.find(b'\x1bA'))
 if a.stay:checks=dict(common,
  vt52_cursor_keys=wire.count(b'\x1bA')==2 and not re.search(rb'\x1b[\[O]A',wire),
  primary_da_banner_only=len(re.findall(rb'\x1b\[\?[0-9;]*c',wire))==1,
  home_and_erase=rows[0].startswith('VT52 MODE') and not any('ANSI FIRST' in r for r in rows),
  graphics=rows[2][4:8]==box,
  cursor_left=rows[4].startswith('AXC'),
  csi_not_interpreted=rows[6].startswith('1mBOLD'),
  erase_line_and_up=rows[8].rstrip()=='LINE8' and rows[7][6]=='U',
  # Clamped to csi_last_row/screen_last_column: row 24 (25-row minimal parent) or 23 (status geometry).
  address_clamp=sum(rows[r][79]=='Q' for r in (23,24))==1 and not any('Q' in rows[r] for r in range(23)),
  final_text=rows[10].startswith('PRESS UP'))
 else:checks=dict(common,
  vt52_cursor_key=wire.count(b'\x1bA')==1,
  ansi_cursor_key_after_exit=bool(re.search(rb'\x1b[\[O]A',tail)),
  primary_da_twice=wire.count(primary)==2 and len(re.findall(rb'\x1b\[\?[0-9;]*c',wire))==2,
  cpr_after_exit=b'\x1b[1;27R' in tail and len(re.findall(rb'\x1b\[[0-9;]*R',wire))==2,
  clearing_reset=rows[0].rstrip()=='                   ANSI OK' and not any(r.strip() for r in rows[1:24]))
 record=dict(passed=all(checks.values()),profile=a.profile,checks=checks,terminal_sha256=sha(binary),wire_sha256=sha(folder/'serial.bin'),
  status_row=rows[24].rstrip(),screen_rows=rows,parent_result=str((folder/'result.json').relative_to(ROOT)),original_inputs=[],
  checker_inputs={str(q.relative_to(ROOT)):sha(q) for q in [Path(__file__),ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/modem_fixtures.py']},
  scope=__doc__.strip()+' Actual COM1 UART in DOSBox-X 8086; synthetic modem peer; no physical terminal, modem or BBS.')
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
 assert record['passed'],json.dumps(dict(checks=checks,status=rows[24],rows=rows[:12]+[rows[23]],harness=result['checks'],wire=repr(wire[-300:])),indent=1)
 print('PASS vt52','screen' if a.stay else 'switch','from profile',a.profile)
if __name__=='__main__':main()
