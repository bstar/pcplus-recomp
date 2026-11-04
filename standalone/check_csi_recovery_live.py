#!/usr/bin/env python3
"""Execute linked parser recovery after malformed or timed-out CSI input.
Only BIOS/UART/tick boundaries are modeled; no parser routine is replaced.
"""
import argparse,hashlib,json
from pathlib import Path
import check_transport as transport
from check_reset_live import fixture
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 records=[]
 for profile in [4,6]:
  for tick in [0,0xfff0]:
   for name,payload,error in [('empty-timeout',b'',4),('digits-timeout',b'12',4),('digit-buffer',b'0'*32+b'H',1),('numeric-overflow',b'65536H',2),('parameter-capacity',b';'*17+b'H',3)]:
    m,_=fixture(profile=profile);m.tick=tick
    m.feed(b'\x1b['+payload);assert m.get('ansi_parse_error')==error,(profile,name)
    # No RIS or direct fixture reset between the bad sequence and its successor.
    for query in [b'\x1b[6n',b'\x1b[2;3HOK\x1b[6n',b'\x1b[?25h\x1b[6n']:
     m.tx.clear();m.feed(query);m.drain()
     assert not m.get('ansi_parse_error'),(profile,name,query)
     # Capacity rejection leaves the following ';H' as ordinary input; this
     # test preserves that behavior rather than silently discarding the tail.
     expected=b'\x1b[2;5R' if b'OK' in query or b'?25' in query else b'\x1b[6;20R' if name=='parameter-capacity' else b'\x1b[6;18R'
     assert bytes(m.tx)==expected,(profile,name,query,bytes(m.tx))
    assert m.get('ansi_parameter_canary')==0xa55a and not m.get('terminal_quit')
    assert (m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(1,4)
    assert m.cells()[82:84]==[0x074f,0x074b]
    records.append(dict(profile=profile,initial_tick=tick,fault=name,error=error,fresh_queries=3,passed=True))
 report=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),cases=records,faults=len(records),fresh_queries=3*len(records),checker_sha256=sha(Path(__file__)),scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS CSI recovery',len(records),'faults',3*len(records),'fresh queries')
if __name__=='__main__':main()
