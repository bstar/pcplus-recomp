#!/usr/bin/env python3
"""Run the full maintained VM diagnostic with sparse numeric storage only."""
import argparse,json,sys
from pathlib import Path
import build_aspect_runtime as builder
import check_aspect_runtime as checker
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists()
 builder.OUT=checker.OUT=out;original=builder.subprocess.run;commands=[]
 def run(arguments,*args,**kwargs):
  arguments=list(map(str,arguments));name=Path(arguments[0]).name
  if name=='nasm'and('-fobj'in arguments or('-f'in arguments and arguments[arguments.index('-f')+1]=='obj')):
   arguments.insert(1,'-DASPECT_DEFER_NUMERIC_BANKS');commands.append(arguments)
  if name=='wcl':
   arguments[1:1]=['-dASPECT_DEFER_NUMERIC_BANKS',str(ROOT/'src/aspect/numeric_bank_runtime.c')];commands.append(arguments)
  return original(arguments,*args,**kwargs)
 builder.subprocess.run=run
 try:builder.main()
 finally:builder.subprocess.run=original
 path=out/'manifest.json';m=json.loads(path.read_text())
 for name in ('src/aspect/numeric_bank_runtime.c','src/aspect/numeric_bank_runtime.h','standalone/test_numeric_groups_runtime.py'):m['sources'][name]=sha(ROOT/name)
 m['experimental_deferred_numeric_banks']=True;m['numeric_storage_compile_commands']=commands;path.write_text(json.dumps(m,indent=2)+'\n')
 saved=sys.argv;sys.argv=[str(ROOT/'standalone/check_aspect_runtime.py')]
 try:checker.main()
 finally:sys.argv=saved
 checks=json.loads((out/'checks.json').read_text());assert checks['passed']and checks['supported_slot_count']==107
 result=dict(passed=True,binary_sha256=checks['binary_sha256'],DOS_summary=checks['DOS_summary'],supported_slots=checks['supported_slot_count'],sources=m['sources'],checker_sha256=sha(ROOT/'standalone/check_aspect_runtime.py'),base_checks_sha256=sha(out/'checks.json'),manifest_sha256=sha(path),original_inputs=[],scope=__doc__+' Only OMF assembly/C get the deferred-numeric flag and source backend. Original flat recovery units, fixture predictions and full checker remain unchanged. Serial/clock/carrier are inherited diagnostic models; this is not the ALARM opcode, a product build, BBS or physical acceptance.')
 (out/'numeric-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS full deferred numeric runtime',result['DOS_summary'])
if __name__=='__main__':main()
