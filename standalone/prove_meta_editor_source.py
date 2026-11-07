#!/usr/bin/env python3
"""Rebuild and replay the Meta Keys components from a minimal source export."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from build_meta_editor import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();out=a.output.resolve();assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 expected=json.loads((build/'result.json').read_text());assert expected['passed'] and expected['original_inputs']==[]
 out.mkdir();fresh=out/'source';sources={}
 for name,h in expected['sources'].items():
  path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('build','analysis','original','originals','install','.git')
  assert path.suffix.lower() not in ('.exe','.com','.obj','.img','.prm','.fon','.db')
  source=ROOT/path;assert sha(source)==h;target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());sources[name]=h
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 with (out/'build.log').open('w') as log:
  subprocess.run([sys.executable,'standalone/build_meta_editor.py','--output','build/recovered'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 actual=json.loads((fresh/'build/recovered/result.json').read_text());assert actual==expected
 for n,h in sources.items():assert sha(ROOT/n)==sha(fresh/n)==h
 result=dict(passed=True,sources=sources,source_count=len(sources),binary_sha256=actual['binary_sha256'],field_keys=actual['field_keys'],row_scenarios=actual['row_scenarios'],defaults_cases=actual['defaults_cases'],original_inputs=[],ancestor_git_unavailable=True,
  scope=__doc__+' Minimal source export has no originals/private data/prior objects/Git metadata. Outer pinned Nix supplies tools; exact DOS EXE and replay report match. External UI services remain modeled.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS isolated Meta Keys:',len(sources),'source files,exact EXE and DOS replay')


if __name__=='__main__':main()
