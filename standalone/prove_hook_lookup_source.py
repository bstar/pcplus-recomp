#!/usr/bin/env python3
"""Reproduce lookup, trap probes, controls and interpreters without originals."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from build_guarded_helper import ROOT,LOOKUP,GUARDED,CONTROL
from prove_guarded_helper_source import sha
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 products={name:'TERMINAL.EXE'for name in[CONTROL,GUARDED,LOOKUP,*[LOOKUP+'-probe-'+str(i)for i in range(5)]]}
 products.update({'aspect-register-parent':'ASPECT.EXE','aspect-runner':'ASPECT.EXE','aspect-compiler-dos':'ASPCOMP.EXE'})
 sources={};expected={}
 for folder,leaf in products.items():
  base=ROOT/'build'/folder;m=json.loads((base/'manifest.json').read_text())
  assert not m.get('original_inputs')and sha(base/leaf)==m['binary_sha256'];expected[folder]=sha(base/leaf)
  for name,digest in m['sources'].items():
   assert sha(ROOT/name)==digest and(name not in sources or sources[name]==digest),name
   sources[name]=digest
 assert expected[CONTROL]=='a024383fa0171baa88ca317c27b01461f14abd2c9c33cec364975c27a5483679'
 assert expected[GUARDED]=='429d3e964e7042d8768295469b297ed28c556f5cdb26c6563e4559bb1f91a2c6'
 assert expected['aspect-runner']=='183f852dfe0a992faa29515e124eb3b6570e44578bdc25880a8a792a2bf7da3f'
 for name in['standalone/build_guarded_helper.py','standalone/prove_hook_lookup_source.py']:sources[name]=sha(ROOT/name)
 fresh=out/'source'
 for name,digest in sources.items():
  path=Path(name);assert not path.is_absolute()and'..'not in path.parts and path.parts[0]not in('build','analysis')
  assert path.suffix.lower()not in('.exe','.com','.obj','.o','.img','.prm','.dir','.xlt')
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
 assert not(fresh/'build').exists()
 commands=[[sys.executable,'standalone/build_guarded_helper.py','--lookup','--probes','--controls'],
  [sys.executable,'standalone/build_guarded_helper.py'],[sys.executable,'standalone/build_aspect_runner.py'],
  [sys.executable,'standalone/build_aspect_process.py','--notice-bank','--notice-sound','--notice-input','--notice-help','--help-resource','--serial-bank','--register-handoff'],
  [sys.executable,'standalone/build_aspect_compiler_dos.py']]
 with(out/'build.log').open('w')as log:
  for command in commands:subprocess.run(command,cwd=fresh,stdout=log,stderr=log,check=True,timeout=240)
 actual={folder:sha(fresh/'build'/folder/leaf)for folder,leaf in products.items()};assert actual==expected,(actual,expected)
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 result=dict(passed=True,products=actual,sources=sources,source_files=len(sources),commands=commands,original_inputs=[],
  checker_sha256=sha(Path(__file__)),build_log_sha256=sha(out/'build.log'),scope=__doc__)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS lookup source:',len(sources),'sources;',len(products),'products')
if __name__=='__main__':main()
