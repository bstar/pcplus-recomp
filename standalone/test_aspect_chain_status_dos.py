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
TARGETS={'renderer-chain-policy':TARGET,'renderer-chain-half':TARGET.replace('transmit $D_PWORD','set duplex full\ntransmit $D_PWORD')}
def definitions():
 base=BASE_DEFINITIONS()[0]
 source='proc main\nwaitfor "LOGIN:" 5\nset break 1234\nset whencase on\nexecute "next"\nendproc\n'
 rows=[]
 for row in base['expected_status_rows']:
  value=bytearray(row)
  value[2:30:2]=b'NEXT.ASX'.ljust(14)
  rows.append(bytes(value))
 full=dict(base,name='renderer-chain-policy',source=source,expected_status_rows=rows)
 half_rows=[]
 for row in rows:
  value=bytearray(row);cell=row[::2].index(b'FDX');value[cell*2]=ord('H');half_rows.append(bytes(value))
 # HALF echoes CHAINOK+CR through the native console; CR resets the column.
 half=dict(base,name='renderer-chain-half',source=source.replace('execute "next"','set duplex half\nexecute "next"'),expected_status_rows=half_rows,post_reply=status.renderer.ESC+b'[1;1R')
 return [full,half]
def adapter():
 harness=BASE_ADAPTER();run=harness.run
 def chained(name,*args,**kwargs):
  target=TARGETS[name]
  kwargs['files']['NEXT.ASX']=status.renderer.compile_source(target)
  kwargs['files']['NEXT.ASP']=target.encode('cp437')
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
   target_label_displayed=case['status_characters'].startswith(' NEXT.ASX'),
   target_ASX_staged=status.renderer.sha(path/'NEXT.ASX')==__import__('hashlib').sha256(status.renderer.compile_source(TARGETS[case['case']])).hexdigest())
  case['passed']=all(case['checks'].values())
  (path/'result.json').write_text(json.dumps(case,indent=2)+'\n')
 report.update(passed=all(c['passed'] for c in report['cases']),target_sources=TARGETS,
  reused_status_checker_sha256=status.renderer.sha(Path(status.__file__).with_name('test_aspect_status_dos.py')),
  scope='Actual production DOS parent/child EXECUTE with resident capability4. Changed BREAK1234 and WHENCASE survive replacement; policy inheritance does not overwrite the change on reopen. Target PAUSE samples actual parent status; target NEXT label is displayed while the invocation filename remains LOGIN. Original query/history/keyboard/owner/IRQ/JFT checks retained. No physical modem or source compile claim.')
 (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 assert report['passed'],report
 return result
if __name__=='__main__':raise SystemExit(main())
