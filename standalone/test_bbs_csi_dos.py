#!/usr/bin/env python3
"""Actual 8086 DOS parent answering modern BBS terminal probes and CSI forms.

After a typed byte the synthetic peer sends the cursor-position size probes
Synchronet/Mystic/ENiGMA-style hosts use (CSI s, CSI 255B/255C, CSI 6n, CSI u
and CSI 999;999H), DSR 5n, DA, secondary DA and XTWINOPS 18t queries, then
drawn rows exercising ECH, CHA, SCO save/restore, cursor hide/show, EL 1/2,
CNL, SGR blink/bold, CP437 blocks, SyncTERM/CTerm private and intermediate
sequences (CSI = 255 h, CSI 0;40 SP D, CSI < 1 h, CSI 1:2 m, CSI ! p, a BEL
inside CSI = ... c), and HPA/HPR/VPR/VPA. A --bbs-csi parent must consume the
unknown sequences and move for HPA..VPA; any other parent must show the
recovered native result (the unconsumed tail printed, those finals ignored).
"""
import argparse,hashlib,json,struct
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
E=b'\x1b['
PROBE=(E+b'2J'+E+b'HR1'
 +E+b's'+E+b'255B'+E+b'255C'+E+b'6n'+E+b'u'+b'S'
 +E+b'999;999H'+E+b'6n'
 +E+b'3;1HABCDEFGHIJ'+E+b'3;3H'+E+b'3X'
 +E+b'4;1H'+E+b'40GX'
 +E+b'5;10H'+E+b's'+E+b'6;1HY'+E+b'uZ'
 +E+b'7;1H'+E+b'?25l'+E+b'?33h'+E+b'=255h'+E+b'?25hok7'
 +E+b'8;1H0123456789'+E+b'8;5H'+E+b'1K'
 +E+b'10;1Hvpa'+E+b'12dV'
 +E+b'13;1H'+E+b'1;5;33;44mICE'+E+b'0m'
 +E+b'14;1HC'+E+b'EN'
 +E+b'17;1Hmid'+E+b'2Ktwo'
 +E+b'18;1H'+E+b'1;31m\xc9\xcd\xbb\xb0\xb1\xb2\xdb'+E+b'm'
 +E+b'19;1Hfnt'+E+b'0;40 D'+E+b'<1h'+E+b'1:2m'+E+b'!pX'+E+b'=1;2\x07cZ'
 +E+b'21;1H'+E+b'30`H'+E+b'5aR'+E+b'1e'+E+b'25dV'
 +E+b'5n'+E+b'0c'+E+b'18t'+E+b'>c'
 +E+b'20;1Hdone')
REPLIES=b'\x1b[24;80R\x1b[24;80R\x1b[0n'

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True)
 p.add_argument('--profile',type=int,default=6);a=p.parse_args()
 binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text())
 assert sha(binary)==m['binary_sha256'];bbs=bool(m.get('experimental_bbs_csi'))
 assert m.get('experimental_window_size_report'),'the probe includes XTWINOPS 18t; use a --window-size-report parent'
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 harness.BINARY=binary;label=f'bbs-csi-{sha(binary)[:8]}-{a.profile}';out=ROOT/'build/bbs-csi-dos'/label;out.mkdir(parents=True,exist_ok=False)
 raw=bytearray(fixture(timeout=5));struct.pack_into('<H',raw,0x194,a.profile)
 # Display, mouse and sound words the full parent imports (see test_ansi_profiles_dos.py).
 for off,value in [(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:struct.pack_into('<H',raw,off,value)
 result=harness.run(label,'success','p900 enter p5000 z p3500 a-x',prm=bytes(raw),com=1,cpu='8086',working_drive='d',
  profile=a.profile,arguments='@D:\\TEST.PRM /D:CaseTest:23',timeout=40,online_triggers=((b'z',((0,PROBE),)),))
 folder=ROOT/'build/connection-dos'/label;wire=(folder/'serial.bin').read_bytes()
 screen=(folder/'SCREEN.BIN').read_bytes();rows=[screen[i*160:i*160+160:2].decode('cp437').rstrip() for i in range(25)]
 attr=lambda r,c:screen[r*160+c*2+1]
 tail=wire[wire.rfind(b'z')+1:]
 common=dict(harness=all(v for k,v in result['checks'].items() if k!='immediate_banner_not_dropped'),
  size_probe_replies=tail.startswith(REPLIES),
  da_and_window_replies=b'\x1b[8;24;80t' in tail and b'\x1b[>' in tail and tail.count(b'c')>=2,
  sco_save_restore=rows[0]=='R1S' and rows[4]=='         Z' and rows[5]=='Y',
  ech=rows[2]=='AB   FGHIJ',cha=rows[3]==' '*39+'X',el1=rows[7]=='     56789',el2=rows[16]=='   two',
  cnl=rows[13]=='C' and rows[14]=='N',
  sgr_blink_bold=rows[12]=='ICE' and attr(12,0)==0x9e,
  cp437=rows[17]=='\u2554\u2550\u2557\u2591\u2592\u2593\u2588' and attr(17,0)==0x0c,
  final=rows[19]=='done')
 if bbs:checks=dict(common,
  private_sequences_consumed=rows[6]=='ok7',
  intermediates_consumed=rows[18]=='fntXZ',
  vpa_keeps_column=rows[9]=='vpa' and rows[11]=='   V',
  hpa_hpr=rows[20]==' '*29+'H'+' '*5+'R',
  vpr_vpa_clamp=rows[23]==' '*36+'V' or rows[24]==' '*36+'V')
 else:checks=dict(common,
  native_private_tail_printed=rows[6]=='255hok7',
  native_intermediate_tails_printed=rows[18]=='fntD1h2mpX1;2cZ',
  native_vpa_ignored=rows[9]=='vpaV',
  native_hpa_hpr_vpr_vpa_ignored=rows[20]=='HRV')
 record=dict(passed=all(checks.values()),bbs_csi=bbs,profile=a.profile,checks=checks,terminal_sha256=sha(binary),wire_sha256=sha(folder/'serial.bin'),
  replies=repr(tail),screen_rows=rows,parent_result=str((folder/'result.json').relative_to(ROOT)),original_inputs=[],
  checker_inputs={str(q.relative_to(ROOT)):sha(q) for q in [Path(__file__),ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/modem_fixtures.py']},
  scope=__doc__.strip()+' Actual COM1 UART in DOSBox-X 8086; synthetic modem peer; no physical terminal, modem or BBS.')
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
 assert record['passed'],json.dumps(dict(checks=checks,rows=rows,replies=repr(tail),harness=result['checks']),indent=1)
 print('PASS bbs csi','maintained' if bbs else 'native','profile',a.profile)
if __name__=='__main__':main()
