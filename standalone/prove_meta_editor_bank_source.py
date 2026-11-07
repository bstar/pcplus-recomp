#!/usr/bin/env python3
"""Rebuild both Meta bank diagnostics from source-only exports; exact DOS EXEs."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def audit_summary(v):
 return {name:{k:report[k] for k in ('near','far','indirect')} for name,report in v['call_audit']['objects'].items()}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('direct','fault','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir();fresh=out/'source';bases={};sources={}
 for mode in ('direct','fault'):
  build=getattr(a,mode).resolve();assert build.is_relative_to(ROOT/'build')
  v=json.loads((build/'result.json').read_text());assert v['passed'] and v['direct_kernel']==(mode=='direct') and sha(build/'METAEDIT.EXE')==v['binary_sha256'];bases[mode]=v
  for n,h in v['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
 for n,h in sources.items():
  path=Path(n);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('src','standalone') and path.suffix in ('.h','.c','.py','.asm','.inc') and sha(ROOT/path)==h
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 for mode,expected in bases.items():
  with (out/(mode+'.log')).open('w') as log:subprocess.run([sys.executable,'standalone/build_meta_editor_bank.py',*(['--direct'] if mode=='direct' else []),*(['--parent-services'] if expected.get('parent_services') else []),'--output','build/'+mode],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
  actual=json.loads((fresh/'build'/mode/'result.json').read_text())
  # Object/debug-listing filenames legitimately differ between exports.
  for k in expected:
   if k!='call_audit':assert actual[k]==expected[k],(mode,k)
  assert actual['call_audit']['cross_CS_challenges_rejected']==expected['call_audit']['cross_CS_challenges_rejected'] and audit_summary(actual)==audit_summary(expected)
 result=dict(passed=True,binaries={mode:v['binary_sha256'] for mode,v in bases.items()},source_count=len(sources),sources=sources,logs={mode:v['logs'] for mode,v in bases.items()},original_inputs=[],ancestor_git_unavailable=True,scope=__doc__+' Both exact executables and DOS checks repeat using outer pinned Nix tools. No parent application or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS isolated Meta banks:',len(sources),'sources;two exact EXEs and DOS workflows')
if __name__=='__main__':main()
