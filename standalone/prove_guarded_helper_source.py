#!/usr/bin/env python3
"""Rebuild guarded/helper products from declared sources in an empty tree."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from build_guarded_helper import ROOT,GUARDED,CONTROL
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 products={name:'TERMINAL.EXE'for name in [CONTROL,GUARDED,*[GUARDED+'-probe-'+str(i)for i in range(5)]]}
 products.update({'aspect-register-parent':'ASPECT.EXE','aspect-compiler-dos':'ASPCOMP.EXE'})
 sources={};expected={}
 for folder,leaf in products.items():
  base=ROOT/'build'/folder;m=json.loads((base/'manifest.json').read_text())
  assert not m.get('original_inputs') and sha(base/leaf)==m['binary_sha256']
  expected[folder]=sha(base/leaf)
  for name,digest in m['sources'].items():
   assert sha(ROOT/name)==digest and (name not in sources or sources[name]==digest),name
   sources[name]=digest
 for name in ['standalone/build_guarded_helper.py','standalone/prove_guarded_helper_source.py']:sources[name]=sha(ROOT/name)
 fresh=out/'source'
 for name,digest in sources.items():
  path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('build','analysis')
  assert path.suffix.lower() not in ('.exe','.com','.obj','.o','.img','.prm','.dir','.xlt')
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
 assert not (fresh/'build').exists()
 commands=[[sys.executable,'standalone/build_guarded_helper.py','--probes','--controls'],
  [sys.executable,'standalone/build_aspect_process.py','--notice-bank','--notice-sound','--notice-input','--notice-help','--help-resource','--serial-bank','--register-handoff'],
  [sys.executable,'standalone/build_aspect_compiler_dos.py']]
 with (out/'build.log').open('w')as log:
  for command in commands:subprocess.run(command,cwd=fresh,stdout=log,stderr=log,check=True,timeout=240)
 actual={folder:sha(fresh/'build'/folder/leaf)for folder,leaf in products.items()}
 assert actual==expected,(actual,expected)
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 result=dict(passed=True,original_inputs=[],products=actual,sources=sources,commands=commands,build_log_sha256=sha(out/'build.log'),checker_sha256=sha(Path(__file__)))
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS original-free guarded helper:',len(sources),'sources',len(products),'products')
if __name__=='__main__':main()
