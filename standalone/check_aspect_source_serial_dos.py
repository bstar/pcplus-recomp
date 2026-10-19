#!/usr/bin/env python3
"""Actual nested DOS compiler while UART IRQ/ASIO session ownership stays live."""
import json,struct
from pathlib import Path
import test_aspect_script_serial_dos as serial
ROOT=serial.ROOT;OUT=ROOT/'build/aspect-source-serial-dos'
def main():
 OUT.mkdir(exist_ok=True);binary=ROOT/'build/aspect-runner/ASPECT.EXE';digest=serial.sha(binary)
 start='integer value,saved\nstring filename\nproc main\nvalue=42\nset break 1234\ntransmit "READY"\nfilename="NEXT.ASP"\nexecute filename\ntransmit "BAD"\nendproc\n'
 target='; padding for a real compiler interval\n'*2000+'integer value,saved\nproc main\nfetch break saved\nif value==42 && saved==1234\ntransmit "STATEOK"\nelse\ntransmit "BADSTATE"\nendif\nwaitfor "END" 5\ntransmit "DONE^M"\nendproc\n'
 cases=[]
 for flow in ('N','S','H','B'):
  pause=b'\x13' if flow in ('S','B') else b'';resume=b'\x11' if pause else b''
  # S/B peer deliberately delivers in-flight data after XOFF. The IRQ must
  # retain it across real compiler execution; END consumed, TRAIL handed back.
  cases.append(dict(name='sourceflow'+flow,source=start,hex=serial.compile_source(start).hex(),source_scripts={'NEXT.ASP':target},
   serial=dict(input_hex=b'ENDTRAIL'.hex(),send_after_tx_hex=(b'READY'+pause).hex()),
   expected=dict(tx_hex=(resume+b'READY'+pause+resume+b'STATEOKDONE\r'+pause).hex(),stdout_hex='',returned_hex=b'TRAIL'.hex())))
 for flow in ('S','H','B'):
  pause=b'\x13' if flow in ('S','B') else b'';resume=b'\x11' if pause else b''
  cases.append(dict(name='pressure'+flow,source=start,hex=serial.compile_source(start).hex(),source_scripts={'NEXT.ASP':target},compiler_wait_ticks=36,
   serial=dict(input_hex=(b'A'*3200+b'ENDTRAIL').hex(),send_after_tx_hex=(b'READY'+pause).hex()),
   expected=dict(tx_hex=(resume+b'READY'+pause+b'STATEOK'+resume+b'DONE\r'+pause).hex(),stdout_hex='',returned_hex=b'TRAIL'.hex())))
 (OUT/'predictions.json').write_text(json.dumps(cases,indent=2)+'\n');results=[]
 for flow,case in zip(('N','S','H','B','S','H','B'),cases):
  driver=serial.build_driver(OUT/('driver'+flow),flow)
  result=serial.run(case,binary,OUT,driver);results.append(result)
  compiled=OUT/case['name']/'NEXT.ASX'
  assert compiled.read_bytes()==serial.compile_source(target)
  assert not list((OUT/case['name']).glob('LPC*.LOG'))
  if case.get('compiler_wait_ticks'):
   before,after=struct.unpack('<II',(OUT/case['name']/'COMPTIME.BIN').read_bytes());assert after-before>=36
  print(case['name'],result['checks'])
 assert serial.sha(binary)==digest
 report=dict(passed=all(r['passed'] for r in results),runner_sha256=digest,compiler_sha256=serial.sha(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'),checker_sha256=serial.sha(Path(__file__)),reused_checker_sha256=serial.sha(Path(serial.__file__)),cases=results,original_inputs=[],scope='Actual production nested DOS compiler and8086 ASPECT UART IRQ across N/S/H/B flow. Checked proactive XOFF/XON for S/B, raw IRQ reception, retained numeric/BREAK state, native compiled bytecode, exact unread ASIO return, vectors/PIC/MCR/guards. No resident-renderer, physical modem or external BBS claim.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'],[(r['name'],r['checks']) for r in results if not r['passed']]
if __name__=='__main__':main()
