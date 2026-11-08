#!/usr/bin/env python3
"""Repeat parent field video/cursor checks from only declared public sources."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from build_script_field import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('build','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();out=a.output.resolve();assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 expected=json.loads((build/'result.json').read_text());assert expected['passed'] and expected['original_inputs']==[] and expected['cases']==103 and expected['CP437_bytes']==255
 out.mkdir();fresh=out/'source'
 for name,digest in expected['sources'].items():
  path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('src','standalone','reconstruction')
  assert path.suffix in ('.asm','.c','.py','.inc') and sha(ROOT/path)==digest
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 with (out/'build.log').open('w') as log:subprocess.run([sys.executable,'standalone/build_script_field.py','--output','build/field',*(['--policy'] if expected.get('parent_policy') else [])],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 actual=json.loads((fresh/'build/field/result.json').read_text());assert actual==expected
 for name,digest in expected['sources'].items():assert sha(ROOT/name)==sha(fresh/name)==digest
 report=dict(passed=True,original_inputs=[],ancestor_git_unavailable=True,sources=expected['sources'],source_count=len(expected['sources']),binary_sha256=actual['binary_sha256'],cases=actual['cases'],CP437_bytes=actual['CP437_bytes'],transcript=actual['transcript'],scope=__doc__+' Exact diagnostic EXE and complete103-case DOS report; no originals/private data/prior objects/ancestor Git. Actual video/BIOS/native cursor, modeled parent admission, diagnostic adapter segment/class aliases. Not RPC/interpreter/whole-parent/physical acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS parent field export:',len(expected['sources']),'public inputs; exact EXE and DOS output')

if __name__=='__main__':main()
