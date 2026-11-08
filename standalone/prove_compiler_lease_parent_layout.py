#!/usr/bin/env python3
"""Cold rebuild of the experimental full-parent compiler-module layout.

Exact layout/module reproduction only; child startup/bridge acceptance is false.
"""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();parent=a.parent.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads((parent/'manifest.json').read_text());assert m.get('original_inputs',[])==[] and m['kind']=='source-only-interactive-dos-terminal'
 assert m['experimental_compiler_lease_module']['production_bridge_admission'] is False
 assert sha(parent/'TERMINAL.EXE')==m['binary_sha256']
 sources=dict(m['sources'])
 for name in ['standalone/keymap_connection_candidate_recipe.json','standalone/prove_compiler_lease_parent_layout.py']:
  sources[name]=sha(ROOT/name)
 out.mkdir();fresh=out/'source'
 for name,digest in sources.items():
  n=Path(name);assert not n.is_absolute() and '..' not in n.parts
  assert n.parts[0] in ('src','standalone','reconstruction') and n.suffix in ('.asm','.c','.h','.inc','.json','.py')
  assert sha(ROOT/n)==digest,name
  target=fresh/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes())
 env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(out))
 assert subprocess.run(['git','rev-parse','--show-toplevel'],cwd=fresh,env=env,capture_output=True).returncode
 recipe=json.loads((fresh/'standalone/keymap_connection_candidate_recipe.json').read_text())
 with (out/'replay.log').open('w') as log:
  subprocess.run([sys.executable,'standalone/build_terminal.py',*recipe['terminal_flags'],'--aspect-get-display','--aspect-get-policy','--compiler-lease-module','--output-dir','build/parent'],cwd=fresh,env=env,stdout=log,stderr=log,check=True)
 replay=fresh/'build/parent';r=json.loads((replay/'manifest.json').read_text())
 for key in ['binary_sha256','experimental_compiler_lease_module','memory_layout','line_port_overlay','meta_editor_overlay']:
  assert r[key]==m[key],key
 artifacts={}
 for leaf in ['TERMINAL.EXE','PCCOMP.OVL','PCLINE.OVL','PCMETA.OVL']:
  assert sha(parent/leaf)==sha(replay/leaf),leaf;artifacts[leaf]=sha(replay/leaf)
 for name,digest in sources.items():assert sha(ROOT/name)==sha(fresh/name)==digest,name
 report=dict(passed=True,compatibility_accepted=False,production_integrated=False,physical_verified=False,
  original_inputs=[],ancestor_git_unavailable=True,source_count=len(sources),sources=sources,artifacts=artifacts,
  module=r['experimental_compiler_lease_module'],near_bytes=r['data_stack_bytes'],
  scope=__doc__+' Rebuild matches complete parent memory map and rebased Line/Port/Meta modules; it does not run the child or establish runtime overlay ownership.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PASS cold parent/module layout:',len(sources),'sources; compatibility remains unaccepted')
if __name__=='__main__':main()
