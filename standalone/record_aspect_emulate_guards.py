#!/usr/bin/env python3
"""Bind current EMULATE admission, child guards and native DOS rejection recovery."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 sources={};receipts={};products={}
 def bind_sources(items):
  for name,digest in items.items():assert sha(ROOT/name)==digest,name;sources[name]=digest
 def load(name):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed'],name
  receipts[name]=sha(path);bind_sources(r.get('sources',{}));return r
 for name,folder in [('TERMINAL.EXE','emulate-rpc-parent-20261107'),('ASPECT.EXE','emulate-rpc-child-checked-20261107')]:
  root=ROOT/'build'/folder;m=json.loads((root/'manifest.json').read_text());assert sha(root/name)==m['binary_sha256']
  products[name]=m['binary_sha256'];bind_sources(m['sources'])
 parent=load('build/emulate-rpc-admission-final-20261107/result.json');assert parent['binary_sha256']==products['TERMINAL.EXE'] and parent['capability']==20 and len(parent['cases'])==52
 assert parent['checker_sha256']==sha(ROOT/'standalone/check_aspect_render_parent_client.py')
 child=load('build/emulate-rpc-child-guards-final-20261107/result.json');assert child['child_sha256']==products['ASPECT.EXE'] and len(child['cases'])==59
 runs=[]
 for folder,cpu,selector,high in [('emulate-rpc-reject-tty-20261107','386',0,True),('emulate-rpc-reject-wyse100-8086-20261107','8086',32,False)]:
  r=load('build/'+folder+'/result.json');assert r['binary_sha256']==products['TERMINAL.EXE'] and r['interpreter_sha256']==products['ASPECT.EXE']
  assert r['cpu']==cpu and r['emulate_reject']['selector']==selector and r['exit_watch_high']==high
  assert len(r['checks'])==32 and all(r['checks'].values())
  exits=r['exit_watch']['exits'];assert len(exits)==4 and exits[0]['error']==3 and exits[0]['opcode']==47 and all(e['error']==0 for e in exits[1:])
  root=ROOT/'build/connection-dos'/folder
  for name in ('serial.bin','SCREEN.BIN','EXITSTAT.BIN','REJECT.ASX','FIRST.ASX','SIX.ASX','MISSING.ASX','EWATCH.COM'):
   receipts[str((root/name).relative_to(ROOT))]=sha(root/name)
  runs.append(dict(cpu=cpu,selector=selector,checks=32,observer_segment=r['exit_watch']['resident_segment'],first_error=3,first_opcode=47,later_clean_exits=3))
 for name in ('standalone/record_aspect_emulate_guards.py','standalone/check_aspect_render_parent_client.py'):
  sources[name]=sha(ROOT/name)
 selector=ROOT/'build/connection-test-current.json'
 selected=json.loads(selector.read_text());assert selected['installed']
 report=dict(passed=True,release_accepted=False,installed_changed=False,products=products,sources=sources,receipts=receipts,original_inputs=[],
  summary=dict(parent_admission_cases=52,child_guard_cases=59,actual_DOS=runs),
  limitations=['Admission executes the linked parent C validator with authored child allocation/client/callback bytes and modeled near caller. It does not execute the resident bridge or DOS allocator.',
   'Child guards execute linked code with the declared stack extent and authored usable CRT/SP bounds. Scalar parent success/errors and DOS/UART/keyboard boundaries are modeled; actual CRT startup and bridge composition are separate gates.',
   'Actual DOS tests execute ordinary products/native opcode2F, compiler output and real parent renderer against synthetic serial peers. Passive exit observers change memory footprint; these runs are recovery tests, not unobserved capacity evidence.',
   'Unsupported selectors0 and32 tested through native VM; remaining unsupported selectors are covered only by earlier direct linked parent tests. Native modal/WHEN/fatal reset, full far-bridge negative composition and receive latency remain open.',
   'No current-product Enigma/Synchronet/package or physical modem acceptance claimed. Installed R59A85A8 unchanged.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS EMULATE guard checkpoint',report['summary'])
if __name__=='__main__':main()
