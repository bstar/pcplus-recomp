#!/usr/bin/env python3
"""Rebuild/replay Meta controller and actual VGA popup from public source only."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from build_meta_dialog import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','vga','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();vga=a.vga.resolve();out=a.output.resolve()
 assert all(v.is_relative_to(ROOT/'build') for v in (build,vga,out)) and not out.exists()
 expected=json.loads((build/'result.json').read_text());screen=json.loads((vga/'result.json').read_text());assert expected['passed'] and screen['passed']
 out.mkdir();fresh=out/'source';sources={**expected['sources'],**screen['sources']}
 for name,h in sources.items():
  path=Path(name);assert not path.is_absolute() and '..' not in path.parts and path.parts[0] not in ('build','analysis','original','originals','install','.git')
  assert path.suffix.lower() not in ('.exe','.com','.obj','.prm','.fon','.img','.db')
  source=ROOT/path;assert sha(source)==h;target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 with (out/'build.log').open('w') as log:
  for command in (['standalone/build_meta_dialog.py','--output','build/model'],['standalone/test_meta_dialog_vga.py','--build','build/model','--output','build/vga']):
   subprocess.run([sys.executable,*command],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 actual=json.loads((fresh/'build/model/result.json').read_text());video=json.loads((fresh/'build/vga/result.json').read_text())
 assert actual==expected and video['passed'] and video['checks']==screen['checks'] and video['demo_sha256']==screen['demo_sha256']
 for n,h in sources.items():assert sha(ROOT/n)==sha(fresh/n)==h
 result=dict(passed=True,sources=sources,source_count=len(sources),binary_sha256=actual['binary_sha256'],demo_sha256=video['demo_sha256'],cases=actual['cases'],key_states=actual['key_states'],VGA_checks=video['checks'],original_inputs=[],ancestor_git_unavailable=True,
  scope=__doc__+' Exact model/prototype EXEs, complete controller replay and actual DOS VGA checks repeat in a minimal export without originals/private data/prior objects/Git metadata. Outer pinned Nix supplies tools; UI decoration is authored, real file/terminal/UART/hardware acceptance separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS isolated Meta dialog:',len(sources),'source files,exact EXEs,controller and VGA replay')


if __name__=='__main__':main()
