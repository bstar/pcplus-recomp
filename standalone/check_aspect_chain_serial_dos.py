#!/usr/bin/env python3
"""Production DOS EXECUTE across a live UART/ASIO lease with an independent peer."""
import json
from pathlib import Path
import test_aspect_script_serial_dos as serial
ROOT=serial.ROOT;OUT=ROOT/'build/aspect-chain-serial-dos'
def main():
 binary=ROOT/'build/aspect-runner/ASPECT.EXE'
 digest=serial.sha(binary);manifest=binary.parent/'manifest.json'
 assert json.loads(manifest.read_text())['binary_sha256']==digest
 source='proc main\ntransmit "READY"\nwaitfor "LOGIN:" 5\nset break 1234\nexecute "next"\ntransmit "BAD"\nendproc\n'
 target='integer saved\nproc main\nfetch break saved\nif saved == 1234\ntransmit "POLICYOK"\nelse\ntransmit "BADPOLICY"\nendif\nwaitfor "END" 5\ntransmit "DONE^M"\nendproc\n'
 cases=[dict(name='livechain',source=source,scripts={'NEXT.ASX':target},hex=serial.compile_source(source).hex(),
  serial=dict(input_hex=b'LOGIN:ENDTRAIL'.hex(),send_after_tx_hex=b'READY'.hex()),
  expected=dict(tx_hex=b'READYPOLICYOKDONE\r'.hex(),stdout_hex='',returned_hex=b'TRAIL'.hex())),
  dict(name='missingchain',source='proc main\nexecute "absent"\nendproc\n',scripts={},
   hex=serial.compile_source('proc main\nexecute "absent"\nendproc\n').hex(),serial=dict(input_hex='',send_after_tx_hex=''),
   expected=dict(tx_hex='',stdout_hex='',exit_code=1))]
 OUT.mkdir(parents=True,exist_ok=True)
 # Record authored sources/predictions before either product execution.
 (OUT/'predictions.json').write_text(json.dumps(cases,indent=2)+'\n')
 driver=serial.build_driver(OUT)
 results=[serial.run(case,binary,OUT,driver) for case in cases]
 assert serial.sha(binary)==digest
 report=dict(passed=all(c['passed'] for c in results),runner_sha256=digest,
  runner_manifest_sha256=serial.sha(manifest),checker_sha256=serial.sha(Path(__file__)),
  reused_checker_sha256=serial.sha(Path(serial.__file__)),predictions_sha256=serial.sha(OUT/'predictions.json'),
  cases=results,original_inputs=[],scope='Actual production8086DOS child, COM1/38400 TCP peer and retained ASIOv1 parent. Script replacement retains UART/raw unread suffix and changed BREAK duration, restores IRQ/PIC/MCR/guard on success and missing target. No renderer, physical modem or complete compiler claim.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 assert report['passed'],report
if __name__=='__main__':main()
