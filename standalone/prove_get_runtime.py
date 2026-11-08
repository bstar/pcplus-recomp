#!/usr/bin/env python3
"""Reproduce the GET editor lifecycle diagnostic from declared public sources."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--client',action='store_true',help='Reproduce the renderer-client diagnostic instead of the editor session')
 for n in ('build','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 expected=json.loads((a.build/'result.json').read_text());assert expected['passed'] and expected['original_inputs']==[]
 out.mkdir();fresh=out/'source'
 for n,d in expected['sources'].items():
  path=Path(n);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('src','standalone') and path.suffix in ('.c','.h','.asm','.py')
  assert sha(ROOT/path)==d,n
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 with (out/'build.log').open('w') as log:subprocess.run([sys.executable,'standalone/build_get_display_client.py' if a.client else 'standalone/build_get_runtime.py','--output','build/session'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 actual=json.loads((fresh/'build/session/result.json').read_text());assert actual==expected
 for n,d in expected['sources'].items():assert sha(ROOT/n)==sha(fresh/n)==d,n
 report=dict(passed=True,original_inputs=[],ancestor_git_unavailable=True,sources=expected['sources'],source_count=len(expected['sources']),binary_sha256=expected['binary_sha256'],transcript=expected['transcript'],scope=__doc__+' Exact diagnostic and complete report, far storage outside DGROUP and separate field code bank. Same modeled peer boundaries; no originals/private data/prior objects/ancestor Git. Not full interpreter, application/BBS/physical acceptance.')
 if a.client:report['scope']='Isolated actual DOS renderer client with modeled parent replies; exact EXE and report, no originals/private data/prior objects/ancestor Git. Not real parent/interpreter/serial/BBS/physical acceptance.'
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS isolated GET client:' if a.client else 'PASS isolated GET session:',len(expected['sources']),'public sources; exact EXE/report')
if __name__=='__main__':main()
