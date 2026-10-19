#!/usr/bin/env python3
"""Production terminal/child EXECUTE retains renderer lease and changed policy."""
import json,sys
from pathlib import Path
import test_aspect_status_dos as status
ROOT=status.ROOT;OUT=ROOT/'build/aspect-chain-status-dos'
BASE_DEFINITIONS=status.definitions
BASE_ADAPTER=status.renderer.adapter
TARGET=('integer saved\nproc main\nfetch break saved\nif saved == 1234\n'
 'transmit "CHAINOK^M"\nelse\ntransmit "BADPOLICY^M"\nendif\n'
 'pause 1\ntransmit $D_PWORD\ntransmit "^M"\nendproc\n')
def definitions():
 base=BASE_DEFINITIONS()[0]
 source='proc main\nwaitfor "LOGIN:" 5\nset break 1234\nset whencase on\nexecute "next"\nendproc\n'
 return [dict(base,name='renderer-chain-policy',source=source)]
def adapter():
 harness=BASE_ADAPTER();run=harness.run
 def chained(name,*args,**kwargs):
  kwargs['files']['NEXT.ASX']=status.renderer.compile_source(TARGET)
  kwargs['files']['NEXT.ASP']=TARGET.encode('cp437')
  return run(name,*args,**kwargs)
 harness.run=chained
 return harness
def main():
 status.OUT=OUT;status.definitions=definitions;status.renderer.adapter=adapter
 status.__file__=__file__
 result=status.run_product()
 label=sys.argv[sys.argv.index('--label')+1];folder=OUT/label
 report=json.loads((folder/'checks.json').read_text())
 for case in report['cases']:
  path=folder/case['case'];wire=(path/'serial.bin').read_bytes()
  case['checks'].update(chained_break_override_retained=wire.count(b'CHAINOK\r')==1 and b'BADPOLICY' not in wire,
   target_ASX_staged=status.renderer.sha(path/'NEXT.ASX')==__import__('hashlib').sha256(status.renderer.compile_source(TARGET)).hexdigest())
  case['passed']=all(case['checks'].values())
  (path/'result.json').write_text(json.dumps(case,indent=2)+'\n')
 report.update(passed=all(c['passed'] for c in report['cases']),target_source=TARGET,
  reused_status_checker_sha256=status.renderer.sha(Path(status.__file__).with_name('test_aspect_status_dos.py')),
  scope='Actual production DOS parent/child EXECUTE with resident capability3. Changed BREAK1234 and WHENCASE survive replacement; policy inheritance does not overwrite the change on reopen. Target PAUSE samples actual parent status; known initial LOGIN label remains until label operation is implemented. Original query/history/keyboard/owner/IRQ/JFT checks retained. No physical modem or source compile claim.')
 (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 assert report['passed'],report
 return result
if __name__=='__main__':raise SystemExit(main())
