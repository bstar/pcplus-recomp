#!/usr/bin/env python3
"""Rebuild experimental GET bridge and client tests from declared public sources."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('bridge','client','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 bridge=json.loads((a.bridge/'result.json').read_text());client=json.loads((a.client/'result.json').read_text())
 assert bridge['passed'] and len(bridge['cases'])==35 and client['passed'] and '271 checks' in client['transcript']
 sources={}
 for report in (bridge,client):
  for n,d in report['sources'].items():
   assert n not in sources or sources[n]==d,n
   sources[n]=d
 for n in ('standalone/keymap_connection_candidate_recipe.json','standalone/prove_get_display_bridge.py'):
  sources[n]=sha(ROOT/n)
 out.mkdir();fresh=out/'source'
 for n,d in sources.items():
  path=Path(n);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('src','standalone','reconstruction')
  assert path.suffix in ('.py','.asm','.c','.h','.inc','.json') and sha(ROOT/path)==d,n
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 def run(args):
  with (out/'build.log').open('a') as log:subprocess.run([sys.executable,*args],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 recipe=json.loads((fresh/'standalone/keymap_connection_candidate_recipe.json').read_text())
 run(['standalone/build_terminal.py',*recipe['terminal_flags'],'--aspect-get-display','--output-dir','build/parent'])
 assert sha(fresh/'build/parent/TERMINAL.EXE')==bridge['parent_sha256']
 run(['standalone/check_get_display_bridge.py','--product','build/parent','--output','build/check'])
 actual=json.loads((fresh/'build/check/result.json').read_text());assert actual==bridge
 run(['standalone/build_get_display_client.py','--output','build/client'])
 actual_client=json.loads((fresh/'build/client/result.json').read_text());assert actual_client==client
 for n,d in sources.items():assert sha(ROOT/n)==sha(fresh/n)==d,n
 result=dict(passed=True,original_inputs=[],ancestor_git_unavailable=True,source_count=len(sources),sources=sources,parent_sha256=bridge['parent_sha256'],client_sha256=client['binary_sha256'],bridge_cases=35,client_checks=271,scope=__doc__+' Exact parent and diagnostic client EXEs and reports. Independent parent CPU replay and DOS client with modeled peer services; not actual pair/interpreter GET, connected serial/BBS, package or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS public source export:',len(sources),'inputs; exact parent/client and reports')
if __name__=='__main__':main()
