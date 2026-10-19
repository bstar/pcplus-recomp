#!/usr/bin/env python3
"""Actual8086DOS unread/read replay on existing real IRQ/preload fixtures.

Reuse owned v3 parent/peer setup in a distinct output folder. The generated
probe checks each read's raw-cell one-shot rollback; no UART peer is modeled.
"""
import hashlib,json
from pathlib import Path
import test_aspect_serial_preload_dos as fixture

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 fixture.OUT=fixture.ROOT/'build/aspect-serial-unread-dos'
 old='if(aspect_serial_read()!=c)return 89;'
 new=('if(aspect_serial_read()!=c)return 89;'
      'if(aspect_serial_unread()!=0)return 90;'
      'if(aspect_serial_unread()!=ASPECT_SERIAL_STATE)return 91;'
      'if(aspect_serial_read()!=c)return 92;')
 assert fixture.PROBE.count(old)==1
 fixture.PROBE=fixture.PROBE.replace(old,new)
 old='if(c!=(mode==2?(raw[i]&127):raw[i]))return 86;'
 new=('if(c!=(mode==2?(raw[i]&127):raw[i]))return 86;'
      'if(aspect_serial_unread()!=0)return 93;'
      'if(aspect_serial_unread()!=ASPECT_SERIAL_STATE)return 94;'
      'if(aspect_serial_read()!=c)return 95;')
 assert fixture.PROBE.count(old)==1
 fixture.PROBE=fixture.PROBE.replace(old,new)
 fixture.main()
 path=fixture.OUT/'checks.json';report=json.loads(path.read_text())
 report.update(checker_sha256=sha(Path(__file__)),fixture_checker_sha256=sha(Path(fixture.__file__)),
               generated_parent_sha256=sha(fixture.OUT/'parent.c'),generated_probe_sha256=sha(fixture.OUT/'probe.c'),
               scope='Actual8086DOS checked UART owner, one-shot raw unread/read for every preloaded byte and4 live IRQ bytes, separate COM1/COM2 peers. Ring wrapping, table mode,7-bit dequeue and exact raw ASIO suffix; IF0/overflow-race proof is the separate linked CPU suite.')
 path.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
