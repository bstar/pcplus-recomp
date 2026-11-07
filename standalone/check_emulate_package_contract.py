#!/usr/bin/env python3
"""Check real published parent versions and reject mismatched package recipes."""
import argparse,json,subprocess,sys
from pathlib import Path
from package_connection_test import ROOT,sha,render_capability,validate_render_pair

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 roots=[ROOT/'build/alarm-connection-candidate-20261106/terminal',ROOT/'build/emulate-connection-seed-20261107/terminal']
 parents=[]
 for root in roots:
  m=json.loads((root/'manifest.json').read_text());assert sha(root/'TERMINAL.EXE')==m['binary_sha256'];parents.append((render_capability(root/'TERMINAL.EXE'),m))
 children=[json.loads((ROOT/'build/emulate-rpc-response-control-20261107/manifest.json').read_text()),json.loads((ROOT/'build/emulate-connection-seed-20261107/aspect/manifest.json').read_text())]
 cases=[]
 for parent_index,child_index,accepted in [(0,0,True),(1,1,True),(0,1,False),(1,0,False)]:
  cap,m=parents[parent_index];assert cap==[19,20][parent_index]
  try:validate_render_pair(cap,m,children[child_index]);result=True
  except AssertionError:result=False
  assert result==accepted;cases.append(dict(parent=cap,child_emulate=bool(children[child_index].get('experimental_emulate_VM')),accepted=result))
 cap,m=parents[1]
 for flag in ('experimental_aspect_emulate_policy','experimental_aspect_snapshot_lease'):
  changed=dict(m);changed[flag]=False
  try:validate_render_pair(cap,changed,children[1])
  except AssertionError:cases.append(dict(missing_parent_flag=flag,accepted=False))
  else:raise AssertionError(flag)
 recipe=ROOT/'standalone/emulate_connection_candidate_recipe.json';base=json.loads(recipe.read_text())
 for name in ('missing-child','missing-parent','missing-alarm'):
  r=json.loads(json.dumps(base))
  if name=='missing-child':r['aspect_options']['emulate_vm']=False
  elif name=='missing-parent':r['terminal_flags'].remove('--aspect-emulate-policy')
  else:r['aspect_options']['alarm_vm']=False;r['terminal_flags'].remove('--aspect-alarm-policy')
  path=out/(name+'.json');path.write_text(json.dumps(r));target=out/(name+'-build')
  run=subprocess.run([sys.executable,str(ROOT/'standalone/build_connection_candidate.py'),'--recipe',str(path),'--output-dir',str(target)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  assert run.returncode!=0 and not target.exists(),name
  (out/(name+'.log')).write_text(run.stdout+run.stderr);cases.append(dict(recipe=name,accepted=False,build_started=False))
 sources={n:sha(ROOT/n) for n in ('standalone/check_emulate_package_contract.py','standalone/package_connection_test.py','standalone/build_connection_candidate.py','standalone/emulate_connection_candidate_recipe.json')}
 report=dict(passed=True,cases=cases,sources=sources,original_inputs=[],scope=__doc__+' Published version read from real prepare-routine bytes. Metadata cases call packager policy; invalid recipes execute builder validation and must fail before output creation. No mismatched application execution or hardware claim.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS package contract',len(cases),'cases')
if __name__=='__main__':main()
