#!/usr/bin/env python3
"""Rebuild the ALARM-capable DOS compiler from declared source in an empty tree."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--test',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();test=a.test.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(exist_ok=False);fresh=out/'source';fresh.mkdir()
 expected=json.loads((test/'result.json').read_text());assert expected['passed'] and expected['original_inputs']==[]
 sources=dict(expected['sources']);sources['standalone/prove_aspect_alarm_compiler_source.py']=sha(Path(__file__))
 for name,digest in sources.items():
  path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('analysis','build','.git')
  assert sha(ROOT/name)==digest,name
  dest=fresh/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
 assert len([f for f in fresh.rglob('*') if f.is_file()])==len(sources)
 with (out/'build.log').open('w') as log:
  subprocess.run([sys.executable,'standalone/build_aspect_compiler_dos.py'],cwd=fresh,stdout=log,stderr=log,check=True)
  subprocess.run([sys.executable,'standalone/test_aspect_alarm_compiler.py','--compiler-dir',str(fresh/'build/aspect-compiler-dos'),'--output',str(fresh/'build/tests')],cwd=fresh,stdout=log,stderr=log,check=True)
 actual=json.loads((fresh/'build/tests/result.json').read_text())
 assert actual['passed'] and actual['binary_sha256']==expected['binary_sha256'] and actual['cases']==expected['cases']
 assert sha(fresh/'build/aspect-compiler-dos/ASPCOMP.EXE')==expected['binary_sha256']
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 result=dict(passed=True,sources=sources,source_files=len(sources),binary_sha256=actual['binary_sha256'],cases=len(actual['cases']),test_result_sha256=sha(fresh/'build/tests/result.json'),original_inputs=[],scope=__doc__+' Exact executable and all78 original/presentation ALARM host/DOS cases. No original binary, private file, previous object or Git metadata; pinned Nix environment supplied by caller. Does not repeat full corpus/checked-stack/VM/physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS cold ALARM compiler:',len(sources),'source files;78 repeated cases')
if __name__=='__main__':main()
