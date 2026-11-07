#!/usr/bin/env python3
"""Rebuild composed Meta workflow/VGA probe and native dialog gate from export."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','vga','native','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();sources={};expected=[]
 for folder in (a.build,a.vga,a.native):
  folder=folder.resolve();assert folder.is_relative_to(ROOT/'build');v=json.loads((folder/'result.json').read_text());assert v['passed'];expected.append(v);sources.update(v['sources'])
 out.mkdir();fresh=out/'source'
 for name,h in sources.items():
  path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] in ('src','standalone') and path.suffix in ('.c','.h','.asm','.py','.json') and sha(ROOT/path)==h
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 commands=[['standalone/build_meta_editor_flow.py','--output','build/flow'],['standalone/test_meta_editor_vga.py','--build','build/flow','--output','build/vga'],['standalone/build_meta_dialog.py','--output','build/native']]
 with (out/'build.log').open('w') as log:
  for command in commands:subprocess.run([sys.executable,*command],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 flow=json.loads((fresh/'build/flow/result.json').read_text());vga=json.loads((fresh/'build/vga/result.json').read_text());native=json.loads((fresh/'build/native/result.json').read_text())
 assert flow==expected[0] and native==expected[2] and vga['checks']==expected[1]['checks'] and vga['demo_sha256']==expected[1]['demo_sha256']
 result=dict(passed=True,source_count=len(sources),sources=sources,binary_sha256=flow['binary_sha256'],demo_sha256=vga['demo_sha256'],logs=flow['logs'],VGA_checks=vga['checks'],native_binary_sha256=native['binary_sha256'],native_cases=native['cases'],native_states=native['key_states'],original_inputs=[],ancestor_git_unavailable=True,scope=__doc__+' Exact EXEs and complete workflow/native checks, plus repeated actual VGA checks. Outer pinned Nix supplies tools. No original/private/prior objects or ancestor Git; not a terminal/hardware result.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS isolated composed Meta editor:',len(sources),'sources, exact workflow/VGA/native EXEs and replay')
if __name__=='__main__':main()
