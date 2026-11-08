#!/usr/bin/env python3
"""Cold public-source rebuild of the experimental DOS compiler-tail lease."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('checks','compiler-dir','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 checks=json.loads(a.checks.read_text());assert checks['passed'] and checks['production_integrated'] is False
 compiler=json.loads((a.compiler_dir/'manifest.json').read_text());assert compiler['original_inputs']==[] and compiler['experimental_get_compiler']
 assert checks['compiler_sha256']==sha(a.compiler_dir/'ASPCOMP.EXE')==compiler['binary_sha256']
 sources={}
 for cohort in (checks['sources'],compiler['sources']):
  for n,h in cohort.items():assert n not in sources or sources[n]==h,n;sources[n]=h
 sources['standalone/prove_compiler_lease_source.py']=sha(__file__)
 out.mkdir();fresh=out/'source'
 for n,h in sources.items():
  path=Path(n);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('src','standalone')
  assert path.suffix in ('.c','.h','.asm','.py') and sha(ROOT/path)==h,n
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
 assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 def run(args):
  with (out/'replay.log').open('a') as log:subprocess.run([sys.executable,*args],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 run(['standalone/build_aspect_compiler_dos.py','--get','--output','build/compiler'])
 assert sha(fresh/'build/compiler/ASPCOMP.EXE')==compiler['binary_sha256']
 run(['standalone/test_compiler_lease_dos.py','--compiler-dir','build/compiler','--output','build/lease'])
 replay=json.loads((fresh/'build/lease/result.json').read_text());assert replay['passed']
 for key in ('parent_sha256','client_sha256','compiler_sha256','parent_paragraphs','retained_paragraphs','client_paragraphs','tail_bytes','rounds','client_checks','result'):
  assert checks[key]==replay[key],key
 for n,h in sources.items():assert sha(ROOT/n)==sha(fresh/n)==h,n
 report=dict(passed=True,original_inputs=[],ancestor_git_unavailable=True,source_count=len(sources),sources=sources,
  parent_sha256=replay['parent_sha256'],client_sha256=replay['client_sha256'],compiler_sha256=replay['compiler_sha256'],
  client_checks=sum(row[0] for row in replay['client_checks']),tail_bytes=replay['tail_bytes'],rounds=replay['rounds'],
  result_sha256=sha(fresh/'build/lease/result.json'),production_integrated=False,physical_verified=False,
  scope=__doc__+' Exact generated parent/client/compiler and observed DOS results. Profile-sized synthetic parent, not production bridge/IRQ/outer-loan/BBS acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS compiler lease cold source:',len(sources),'sources;',report['client_checks'],'client checks')
if __name__=='__main__':main()
