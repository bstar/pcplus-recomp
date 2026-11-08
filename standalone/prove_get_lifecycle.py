#!/usr/bin/env python3
"""Cold public-source replay of the full DOS runtime GET lifetime diagnostic."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from build_aspect_runtime import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('build','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();out=a.output.resolve()
 assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 manifest=json.loads((build/'manifest.json').read_text());checks=json.loads((build/'checks.json').read_text())
 assert checks['passed'] and checks['original_inputs']==[] and manifest['GET_lifecycle']
 assert checks['binary_sha256']==manifest['binary_sha256']==sha(build/'EXECUTE.EXE')
 assert checks['manifest_sha256']==sha(build/'manifest.json')
 sources=dict(manifest['sources'])
 for name in ('standalone/check_aspect_runtime.py','standalone/prove_get_lifecycle.py'):
  sources[name]=sha(ROOT/name)
 out.mkdir();fresh=out/'source'
 for name,digest in sources.items():
  path=Path(name)
  assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('build','analysis','original','originals','.git')
  assert path.suffix.lower() not in ('.exe','.com','.obj','.img','.db','.prm','.fon')
  assert sha(ROOT/path)==digest
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
 assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 with (out/'replay.log').open('w') as log:
  subprocess.run([sys.executable,'standalone/check_aspect_runtime.py','--get-lifecycle','--output','build/lifecycle'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 actual=fresh/'build/lifecycle'
 assert json.loads((actual/'manifest.json').read_text())==manifest
 assert json.loads((actual/'checks.json').read_text())==checks
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest
 result=dict(passed=True,source_count=len(sources),sources=sources,binary_sha256=checks['binary_sha256'],DOS_summary=checks['DOS_summary'],original_inputs=[],ancestor_git_unavailable=True,
  scope=__doc__+' Exact executable, manifest and DOS checks. GET ownership/recovery peers controlled; full application/hardware acceptance remains open.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS isolated GET lifecycle:',len(sources),'public sources; exact EXE/manifest/DOS checks')

if __name__=='__main__':main()
