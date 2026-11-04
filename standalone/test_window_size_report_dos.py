#!/usr/bin/env python3
"""Actual8086 DOS parent replies to delayed CSI18t after synthetic modem connect."""
import argparse,hashlib,json,re,struct
from pathlib import Path
import test_connection_dos as harness
from modem_fixtures import fixture
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True);a=p.parse_args()
 assert re.fullmatch('[a-z0-9-]+',a.label)
 binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text());assert m['experimental_window_size_report'] and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 harness.BINARY=binary;out=ROOT/'build/window-size-report-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
 raw=bytearray(fixture(timeout=5));struct.pack_into('<HH',raw,0,2,5)
 struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5)
 struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<HH',raw,0x1bc,0,0)
 struct.pack_into('<H',raw,0x196,0);struct.pack_into('<H',raw,0x1e6,0)
 # The query follows an actual typed byte, so delayed fragments are measured
 # from an established parent/parser rather than an emulator startup guess.
 chunks=((0,b'\x1b[31m\x1b[3;12r\x1b[?6h\x1b[4;5H\x1b['),(.03,b'1'),(.06,b'8t\x1b[6n\x1b[?18t\x1b[18;1t\x1b[?6l\x1b[r\x1b[1;16H'))
 result=harness.run(a.label,'success','p900 enter p5000 z p1500 a-x',prm=bytes(raw),com=3,irq=5,cpu='8086',working_drive='d',
  arguments='@D:\\TEST.PRM /D:CaseTest:23 /I:3',timeout=30,online_triggers=((b'z',chunks),))
 assert result['passed'],result
 folder=ROOT/'build/connection-dos'/a.label;wire=(folder/'serial.bin').read_bytes()
 assert wire.count(b'\x1b[8;24;80t')==1 and b'\x1b[4;5R' in wire
 assert wire.count(b'ATZ\r')==wire.count(b'ATDCaseTest:23\r')==1
 assert (folder/'TEST.PRM').read_bytes()==raw and sha(binary)==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 record=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),parent_result=str((folder/'result.json').relative_to(ROOT)),parent_result_sha256=sha(folder/'result.json'),wire_sha256=sha(folder/'serial.bin'),screen_sha256=sha(folder/'SCREEN.BIN'),
  checker_inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/modem_fixtures.py',ROOT/'standalone/test_terminal.py']},
  scope=__doc__+' Actual COM3/3E8/IRQ5 UART, configured init/dial, keyboard, parser/CPR/size reply and hardware restoration. Peer sends delayed query bytes, never a fabricated terminal reply. No SynthModem/SIP/BBS/analog/physical or deployment acceptance.')
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS actual DOS delayed size query, origin-relative CPR and report exactly once')
if __name__=='__main__':main()
