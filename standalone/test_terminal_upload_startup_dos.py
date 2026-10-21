#!/usr/bin/env python3
"""Actual DOS upload while the independent receiver supplies startup banners."""
import argparse,hashlib,json,time
from pathlib import Path
from test_terminal_upload_dos import ROOT,BINARY,OUT,UploadPeer,run_case,payload

class StartupPeer(UploadPeer):
 def negotiate(self):
  time.sleep(1.9)
  for data,pause in self.recipe['banner_parts']:
   self.send(data);self.log('startup-banner',hex=data.hex())
   deadline=time.monotonic()+pause
   while time.monotonic()<deadline and not self.stop.is_set():
    self.receive()
    assert not self.pending,'DOS sent a packet before the independent receiver handshake'
  self.checks['no_packet_during_banner']=True
  deadline=time.monotonic()+10;next_send=0
  while time.monotonic()<deadline and not self.stop.is_set():
   if time.monotonic()>=next_send:
    self.send(b'\x15' if self.recipe.get('checksum') else b'C');next_send=time.monotonic()+.5
   self.receive()
   if self.pending:
    self.checks['actual_upload_started']=self.pending[0] in (1,2,4)
    return
  raise TimeoutError('DOS failed to upload after the actual receiver handshake')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sha256',required=True);p.add_argument('--label',required=True);a=p.parse_args()
 assert a.label.replace('-','').isalnum() and hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256
 recipes=[dict(name='plain-CRC-over10K',data=payload(11521),banner_parts=[(b'\r\nStart XMODEM-1K/CRC transfer now (Ctrl-X to abort):\r\n',.3)]),
  dict(name='ANSI-CRC',data=payload(117)+b'\x00\x1a\xff',banner_parts=[(b'\x1b[35mWaiting for Upload\x1b[5C\x1b[3G\x1b[0m\r\n',.3)]),
  dict(name='split-CSI-checksum',data=payload(1024),checksum=True,banner_parts=[(b'\x1b[5',1.3),(b'C\r\n',.3)])]
 rows=[run_case(r,sha=a.sha256,label=a.label,after_ms=10000,peer_class=StartupPeer) for r in recipes]
 result=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,cases=rows,
  inputs={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),ROOT/'standalone/test_terminal_upload_dos.py',ROOT/'standalone/test_terminal_transfer_dos.py',ROOT/'standalone/test_terminal.py']},
  scope='Actual source-built DOS in DOSBox with independent synthetic receiver startup banners and held handshake. Plain/ANSI/CSI-split text must emit no premature packet, then exact CRC/checksum/padding/EOT-NAK-ACK, read-only source, real parser/keyboard recovery and UART/IRQ/PIC restoration. Not a real BBS, audio or physical modem test.')
 with (OUT/a.label/'startup-checks.json').open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=result['passed'],cases=len(rows))));assert result['passed']

if __name__=='__main__':main()
