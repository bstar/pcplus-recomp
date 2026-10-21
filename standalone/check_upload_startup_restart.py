#!/usr/bin/env python3
"""A restarted ANSI escape must not become an upload handshake."""
import argparse,hashlib,json
from pathlib import Path
from check_terminal_upload_startup import Startup,ROOT,BINARY
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 global BINARY
 canonical=ROOT/'build/terminal/terminal-upload-startup-restart.json'
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=canonical);p.add_argument('--baseline',action='store_true');p.add_argument('--binary',type=Path);a=p.parse_args()
 if a.binary:
  import check_transport
  BINARY=a.binary.resolve();assert BINARY.is_relative_to(ROOT/'build')
  check_transport.BINARY=BINARY;check_transport.MAP=BINARY.parent/'terminal.map'
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and (out==canonical or not out.exists());assert not a.baseline or out!=canonical;digest=sha(BINARY)
 recipes=[('CSI_restarted_by_ESC',b'\x1b[\x1b[5G',[(60,b'C',True)],True),
  ('ESC_restarted_by_ESC',b'\x1b\x1b[5C',[(60,b'C',True)],True),
  ('charset_restarted_by_ESC',b'\x1b(\x1b[5G',[(60,b'C',True)],True),
  ('CSI_restarted_as_OSC',b'\x1b[\x1b]0;G',[(24,b'\x07',False),(60,b'C',True)],True),
  ('OSC_preserves_embedded_ESC_CSI',b'\x1b]title\x1b[5G',[(24,b'\x1b\\',False),(60,b'C',True)],True),
  ('restarted_CSI_then_checksum',b'\x1b[\x1b[5G',[(60,b'\x15',True)],False)]
 cases=[]
 for label,noise,schedule,crc in recipes:
  m=Startup(noise,b'',schedule=schedule,crc=crc);error=None
  try:
   m.upload();checks=dict(receiver_handshake_precedes_transmission=m.handshake_offered,complete_native_transfer=not m.get('terminal_transfer_fault') and m.accepted==len(m.frames)==m.eots==1,source_closed=not m.handles,ANSI_state_retired=m.get('terminal_upload_startup_ansi')==0)
  except AssertionError as e:error=str(e);checks=dict(native_workflow_completed=False)
  cases.append(dict(name=label,passed=all(checks.values()),checks=checks,error=error,handshake_offered=m.handshake_offered,elapsed_ticks=m.tick))
 assert sha(BINARY)==digest
 result=dict(passed=all(c['passed'] for c in cases),binary_sha256=digest,cases=cases,inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'standalone/check_terminal_upload_startup.py',ROOT/'standalone/check_terminal_upload_live.py',ROOT/'standalone/check_terminal_transfer_live.py']},scope='Actual linked native sender and real UART ISR with independent modeled receiver holding its handshake until60ticks. A restarted CSI/ESC/charset or CSI-to-OSC must not expose an ANSI final C/G as a protocol control. OSC/ST handling and checksum selection are separate cases. No product callback replaced; not actual DOS/audio/physical evidence.')
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],cases=len(cases),failed=[c['name'] for c in cases if not c['passed']])));assert not result['passed'] if a.baseline else result['passed']

if __name__=='__main__':main()
