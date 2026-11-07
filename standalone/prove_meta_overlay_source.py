#!/usr/bin/env python3
"""Rebuild disk-loaded Meta diagnostics and full-parent probe from public sources."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('direct','fault','probe','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir();fresh=out/'source';sources={};bases={}
 for name in ('direct','fault','probe'):
  folder=getattr(a,name).resolve();assert folder.is_relative_to(ROOT/'build');v=json.loads((folder/('manifest.json'if name=='probe'else'result.json')).read_text());bases[name]=v
  if name=='probe':assert v['diagnostic_meta_loader_probe']and sha(folder/'TERMINAL.EXE')==v['binary_sha256']
  else:assert v['passed']and v['faults']==(name=='fault')and sha(folder/'METAEDIT.EXE')==v['parent_sha256']
  for n,h in v['sources'].items():assert n not in sources or sources[n]==h;sources[n]=h
 for n in ('standalone/prove_meta_overlay_source.py','standalone/line_port_profile.json','standalone/test_meta_overlay_rejections.py','standalone/test_meta_loader_parent_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/directory_test_support.py'):sources[n]=sha(ROOT/n)
 for n,h in sources.items():
  path=Path(n);assert not path.is_absolute()and '..'not in path.parts and path.parts[0]not in ('build','analysis','install','.git')and path.suffix.lower()not in ('.exe','.com','.obj','.img','.prm','.dir','.xlt','.db')and sha(ROOT/path)==h,n
  target=fresh/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,target)
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out));assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 def run(label,args):
  with(out/(label+'.log')).open('w')as log:subprocess.run([sys.executable,*args],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
  print(label,'PASS',flush=True)
 for name in ('direct','fault'):
  run(name,['standalone/build_meta_overlay.py',*(['--faults']if name=='fault'else[]),'--output','build/'+name]);v=json.loads((fresh/'build'/name/'result.json').read_text());b=bases[name]
  assert v['parent_sha256']==b['parent_sha256']and v['overlay']==b['overlay']and v['loader_segments']==b['loader_segments']and v['new_loader_DGROUP_bytes']==0
  assert 'PASS 3069 checks;'in v['logs']and 'PASS loader 68 checks;'in v['logs']
 flags=json.loads((fresh/'standalone/line_port_profile.json').read_text())+['--line-port-overlay','--meta-loader-probe']
 run('parent',['standalone/build_terminal.py',*flags,'--output-dir','build/probe']);assert sha(fresh/'build/probe/TERMINAL.EXE')==bases['probe']['binary_sha256']
 for leaf,key in (('PCMETA.OVL','meta_editor_overlay'),('PCLINE.OVL','line_port_overlay')):assert sha(fresh/'build/probe'/leaf)==bases['probe'][key]['sha256']
 run('parent-DOS',['standalone/test_meta_loader_parent_dos.py','--terminal','build/probe/TERMINAL.EXE','--output','build/parent-DOS']);parent=json.loads((fresh/'build/parent-DOS/result.json').read_text());assert parent['passed']
 run('refusals',['standalone/test_meta_overlay_rejections.py','--direct','build/direct','--fault','build/fault','--output','build/refusals']);refusals=json.loads((fresh/'build/refusals/result.json').read_text());assert refusals['passed']and len(refusals['cases'])==20
 for n,h in sources.items():assert sha(ROOT/n)==sha(fresh/n)==h,n
 result=dict(passed=True,source_count=len(sources),binaries={n:(v['binary_sha256']if n=='probe'else v['parent_sha256'])for n,v in bases.items()},component_overlays={n:bases[n]['overlay']['sha256']for n in ('direct','fault')},parent_overlay_sha256=bases['probe']['meta_editor_overlay']['sha256'],parent_line_overlay_sha256=bases['probe']['line_port_overlay']['sha256'],parent_DOS_checks=parent['checks'],refusal_cases=len(refusals['cases']),sources=sources,original_inputs=[],ancestor_git_unavailable=True,scope=__doc__+' Three exact EXEs/three exact META payloads and parent PCLINE; normal reload workflows, actual parent save/read/callback lease and20 refusal cases. Outer pinned Nix supplies tools. No normal menu/live UART/arena arbitration/physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS Meta disk loader source export:',len(sources),'sources;all three EXEs and DOS gates')
if __name__=='__main__':main()
