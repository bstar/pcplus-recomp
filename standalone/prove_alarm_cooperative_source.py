#!/usr/bin/env python3
"""Rebuild the native/cooperative DOS diagnostic from only its declared sources."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('test','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();test=a.test.resolve();out=a.output.resolve();assert all(p.is_relative_to(ROOT/'build') for p in (test,out));out.mkdir(exist_ok=False);fresh=out/'source';fresh.mkdir()
 expected=json.loads((test/'result.json').read_text());assert expected['passed']
 sources={**expected['sources'],'standalone/prove_alarm_cooperative_source.py':sha(Path(__file__))}
 for n,h in sources.items():
  p=Path(n);assert not p.is_absolute() and '..' not in p.parts and p.parts[0] not in ('build','analysis','.git')
  assert p.suffix in ('.c','.h','.asm','.inc','.py') and sha(ROOT/n)==h,n
  target=fresh/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
 assert len([f for f in fresh.rglob('*') if f.is_file()])==len(sources)
 (fresh/'build').mkdir();rebuilt=fresh/'build/proof'
 with (out/'build.log').open('w') as log:subprocess.run([sys.executable,str(fresh/'standalone/test_alarm_cooperative_dos.py'),'--output',str(rebuilt)],cwd=fresh,stdout=log,stderr=log,check=True)
 actual=json.loads((rebuilt/'result.json').read_text());assert actual['passed'] and (actual['cases'],actual['checks'])==(expected['cases'],expected['checks'])
 assert sha(rebuilt/'ALARM.EXE')==sha(test/'ALARM.EXE') and sha(rebuilt/'harness.c')==sha(test/'harness.c')
 for n,h in sources.items():assert sha(ROOT/n)==sha(fresh/n)==h,n
 result=dict(passed=True,binary_sha256=sha(rebuilt/'ALARM.EXE'),cases=actual['cases'],checks=actual['checks'],sources=sources,source_files=len(sources),original_inputs=[],scope=__doc__+' Empty source tree without originals/private settings/previous objects/Git metadata. Caller supplies pinned Nix tools; no separate bootstrap claim. Exact DOS8086 executable and full fault/cleanup suite repeated.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS cold cooperative alarm:',len(sources),'source files;',actual['cases'],'DOS cases')
if __name__=='__main__':main()
