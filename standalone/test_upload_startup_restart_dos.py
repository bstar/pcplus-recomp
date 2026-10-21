#!/usr/bin/env python3
"""Actual DOS receiver holds handshake through restarted ANSI sequences."""
import argparse,hashlib,json
from pathlib import Path
from test_terminal_upload_startup_dos import StartupPeer
from test_terminal_upload_dos import ROOT,BINARY,OUT,run_case,payload
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sha256',required=True);p.add_argument('--label',required=True);a=p.parse_args()
 assert a.label.replace('-','').isalnum() and sha(BINARY)==a.sha256
 recipes=[dict(name='CSI-restart',data=payload(128),banner_parts=[(b'\x1b[\x1b[5G',.35)]),
  dict(name='ESC-restart',data=payload(128),banner_parts=[(b'\x1b\x1b[5C',.35)]),
  dict(name='charset-restart',data=payload(128),banner_parts=[(b'\x1b(\x1b[5G',.35)]),
  dict(name='CSI-to-OSC',data=payload(128),banner_parts=[(b'\x1b[\x1b]titleG',1.3),(b'\x07',.3)]),
  dict(name='OSC-keeps-embedded-CSI',data=payload(128),banner_parts=[(b'\x1b]title\x1b[5G',1.3),(b'\x1b\\',.3)]),
  dict(name='CSI-restart-checksum',data=payload(128),checksum=True,banner_parts=[(b'\x1b[\x1b[5G',.35)])]
 rows=[run_case(r,sha=a.sha256,label=a.label,after_ms=10000,peer_class=StartupPeer) for r in recipes]
 paths=['standalone/test_upload_startup_restart_dos.py','standalone/test_terminal_upload_startup_dos.py','standalone/test_terminal_upload_dos.py','standalone/test_terminal_transfer_dos.py','standalone/test_terminal.py']
 result=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,cases=rows,inputs={n:sha(ROOT/n) for n in paths},scope='Six actual source-built DOS independent-peer startup cases. The receiver withholds its real C/NAK until interrupted CSI/ESC/charset or OSC/ST sequences finish; no premature packet may appear. Each case requires exact source/padding/CRC or checksum/EOT controls, parser/keyboard recovery, unchanged source and hardware restoration. No actual BBS/audio/physical claim.')
 with (OUT/a.label/'restart-checks.json').open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=result['passed'],cases=len(rows))));assert result['passed']

if __name__=='__main__':main()
