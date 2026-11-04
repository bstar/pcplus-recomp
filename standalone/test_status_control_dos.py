#!/usr/bin/env python3
"""Actual8086 DOS normal Ctrl-]/Alt-Z status controls and serial area reports.
Synthetic loopback serial peer; no online resize, BBS, SIP or physical claim.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True);a=p.parse_args()
 assert re.fullmatch('[a-z0-9-]+',a.label);binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text());assert m['experimental_status_control'] and m['experimental_window_size_report'];assert sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 out=ROOT/'build/status-control-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
 folder=ROOT/'build/connection-dos'/a.label;assert not folder.exists()
 raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5);struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
 struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,0,0);struct.pack_into('<H',raw,0x196,0);struct.pack_into('<H',raw,0x1e6,0)
 harness.BINARY=binary;response=b'\x1b[18t\x1b[25;80H\x1b[6n\x1b[1;16H'
 result=harness.run(a.label,'direct','p900 enter p1500 a p500 c-] p500 b p500 a-z p400 c-] p400 c p700 a-x',prm=bytes(raw),com=3,irq=5,cpu='8086',working_drive='d',arguments='@D:\\TEST.PRM /I:3',timeout=25,online_triggers=((b'a',response),(b'b',response),(b'c',response)))
 wire=(folder/'serial.bin').read_bytes();sizes=re.findall(rb'\x1b\[8;(\d+);(\d+)t',wire)
 result['checks'].update(three_requested_area_reports=sizes==[(b'24',b'80'),(b'25',b'80'),(b'24',b'80')],CPR_hidden_area=b'\x1b[25;80R' in wire,CPR_visible_area=wire.count(b'\x1b[24;80R')==2,Ctrl_bracket_never_transmitted=b'\x1d' not in wire)
 result['passed']=all(result['checks'].values())
 record=dict(passed=result['passed'],checks=result['checks'],terminal_sha256=sha(binary),terminal_manifest_sha256=sha(binary.parent/'manifest.json'),area_reports=[list(map(lambda b:int(b),s)) for s in sizes],parent_result=str((folder/'result.json').relative_to(ROOT)),sources={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/modem_fixtures.py',ROOT/'standalone/test_terminal.py']},artifacts={str(p.relative_to(ROOT)):sha(p) for p in [folder/'serial.bin',folder/'SCREEN.BIN',folder/'BEFORE.BIN',folder/'AFTER.BIN',folder/'result.json']},scope=__doc__)
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');assert record['passed'],json.dumps(record,indent=2)
 print('PASS actual DOS BIOS Ctrl-] and Alt-Z, real UART size24/25/24 and CPR clamping, sampled hardware restoration')
if __name__=='__main__':main()
