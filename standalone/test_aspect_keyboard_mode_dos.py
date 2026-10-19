#!/usr/bin/env python3
"""Observe the actual child BIOS mode under the selected parent BIOS policy."""
import inspect,json,sys
from pathlib import Path
import test_aspect_status_dos as status
ROOT=status.ROOT;OUT=ROOT/'build/aspect-keyboard-mode-dos'
BASE=status.definitions
BASE_ADAPTER=status.renderer.adapter
TARGET='proc main\npause 1\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n'
def definitions():
 base=BASE()[0];cases=[]
 for mode in (0,16):
  for chain in (False,True):
   source='proc main\nwaitfor "LOGIN:" 5\nset whencase on\n'+('execute "next"\nendproc\n' if chain else TARGET.split('proc main\n')[1])
   rows=[]
   for old in base['expected_status_rows']:
    row=bytearray(old)
    if chain:row[2:30:2]=b'NEXT.ASX'.ljust(14)
    rows.append(bytes(row))
   cases.append(dict(base,name='BIOS-'+str(mode)+('-chain' if chain else '-direct'),source=source,when_value=mode,BIOS_mode=mode,chain=chain,expected_status_rows=rows))
 return cases
def adapter():
 harness=BASE_ADAPTER();run=harness.run
 def staged(name,*args,**kwargs):
  if name.endswith('-chain'):kwargs['files']['NEXT.ASX']=status.renderer.compile_source(TARGET)
  return run(name,*args,**kwargs)
 harness.run=staged;return harness
def main():
 status.OUT=OUT;status.definitions=definitions;status.renderer.adapter=adapter
 source=inspect.getsource(status.run_product)
 old="when=child_word('_runtime_when_case_sensitive')"
 assert source.count(old)==1;source=source.replace(old,"when=child_word('_runtime_keyboard_mode')")
 old='SETWHENCASE_value=when=='
 assert source.count(old)==1;source=source.replace(old,'inherited_BIOS_mode=when==')
 old="case['profile']);extra=' /A:NETWORK'"
 assert source.count(old)==1;source=source.replace(old,"case['profile']);extra=' /A:NETWORK /B:'+('ENHANCED' if case['BIOS_mode'] else 'STANDARD')")
 scope=dict(status.__dict__);scope['__file__']=__file__
 exec(compile(source,__file__,'exec'),scope)
 result=scope['run_product']()
 label=sys.argv[sys.argv.index('--label')+1];path=OUT/label/'checks.json'
 report=json.loads(path.read_text());report.update(checker_sha256=status.renderer.sha(Path(__file__)),reused_status_checker_sha256=status.renderer.sha(Path(status.__file__)),scope='Actual production DOS parent selects STANDARD/ENHANCED; passive timer observes actual child runtime BIOS mode while PAUSE runs, both directly and after EXECUTE. Existing status-row, renderer/query, UART/IRQ/JFT/owner and parent keyboard-return checks retained. No physical BIOS or full local-key dispatch claim.')
 path.write_text(json.dumps(report,indent=2)+'\n')
 assert report['passed'];return result
if __name__=='__main__':raise SystemExit(main())
