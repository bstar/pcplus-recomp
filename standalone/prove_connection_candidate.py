#!/usr/bin/env python3
"""Run the tracked candidate builder from an original-free public source export."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from package_connection_test import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--recipe',type=Path,default=ROOT/'standalone/connection_candidate_recipe.json');a=p.parse_args()
 build=a.build.resolve();out=a.output.resolve();assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 expected=json.loads((build/'result.json').read_text());assert expected['passed'] and expected['original_inputs']==[]
 recipe=a.recipe.resolve();assert recipe.is_relative_to(ROOT) and sha(recipe)==expected['recipe_sha256']
 package=json.loads((build/'package/manifest.json').read_text());revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',revision],cwd=ROOT,text=True).splitlines()
 names=set(package['sources'])|set(expected['sources'])|{n for n in tracked if n.startswith('standalone/') and n.endswith('.py')}
 out.mkdir();fresh=out/'source';sources={}
 for name in sorted(names):
  path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ['build','analysis','original','originals','install','.git']
  assert path.suffix.lower() not in ['.exe','.com','.obj','.prm','.fon','.img','.db']
  data=subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT);target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);target.chmod((ROOT/path).stat().st_mode&0o777)
  sources[name]=sha(target);assert sources[name]==sha(ROOT/path),name
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 with (out/'build.log').open('w') as log:subprocess.run([sys.executable,'standalone/build_connection_candidate.py','--recipe',str(recipe.relative_to(ROOT)),'--output-dir','build/reviewed'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 actual=json.loads((fresh/'build/reviewed/result.json').read_text());assert actual['passed'] and actual['files']==expected['files'] and actual['archive_sha256']==expected['archive_sha256']
 for n,h in sources.items():assert sha(ROOT/n)==sha(fresh/n)==h,n
 result=dict(passed=True,source_commit=revision,source_base_commit=expected['source_base_commit'],source_count=len(sources),sources=sources,files=actual['files'],archive_sha256=actual['archive_sha256'],original_inputs=[],ancestor_git_unavailable=True,
  scope=__doc__+' Executes the tracked Python builder inside the pinned Nix environment with no prior build objects, originals, private configuration or Git metadata in its source export. The shell wrapper/Nix environment bootstrap is separately exercised in the working checkout. Five executables,ten package files and deterministic archive must match the reviewed build.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS tracked builder:',len(sources),'public files; exact five executables,ten package files and ZIP')
if __name__=='__main__':main()
