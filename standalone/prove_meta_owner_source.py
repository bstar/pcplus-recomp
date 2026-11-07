#!/usr/bin/env python3
"""Repeat the DOS KEY owner diagnostic from an isolated source export."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();out=a.output.resolve()
 assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 expected=json.loads((build/'result.json').read_text());assert expected['passed'];out.mkdir();fresh=out/'source'
 for name,h in expected['sources'].items():
  path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('src','standalone')
  assert path.suffix in ('.h','.c','.py','.asm') and sha(ROOT/path)==h
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 with (out/'build.log').open('w') as log:subprocess.run([sys.executable,'standalone/build_meta_owner.py','--output','build/check'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 actual=json.loads((fresh/'build/check/result.json').read_text());assert actual==expected
 result=dict(passed=True,binary_sha256=actual['binary_sha256'],source_count=len(expected['sources']),logs=actual['logs'],sources=expected['sources'],original_inputs=[],ancestor_git_unavailable=True,scope=__doc__+' Exact executable and complete checks; outer pinned Nix provides tools. Does not establish live application integration or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS isolated KEY owner:',result['source_count'],'source files, exact EXE and DOS results')
if __name__=='__main__':main()
