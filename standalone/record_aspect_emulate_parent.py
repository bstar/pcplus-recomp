#!/usr/bin/env python3
"""Record unbound EMULATE parent checks and the failing capacity gate honestly."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={}
 def load(name,passed=True):
  path=ROOT/name;r=json.loads(path.read_text());assert r.get('passed',passed)==passed,name;receipts[name]=sha(path)
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n;sources[n]=h
  return r
 parent=ROOT/'build/emulate-parent-owner-quarantine-20261107';m=json.loads((parent/'manifest.json').read_text())
 assert m['experimental_aspect_emulate_policy'] and sha(parent/'TERMINAL.EXE')==m['binary_sha256']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 test=load('build/emulate-parent-owner-quarantine-tests-20261107/result.json')
 cold=load('build/emulate-parent-owner-cold-20261107/result.json')
 assert test['parent_sha256']==cold['parent_sha256']==m['binary_sha256']
 assert len(test['cases'])==cold['cases']==294
 repeated=ROOT/'build/emulate-parent-owner-cold-20261107/source/build/tests/result.json'
 assert sha(repeated)==cold['repeated_result_sha256'] and json.loads(repeated.read_text())['cases']==test['cases']
 assert sha(ROOT/'build/emulate-parent-owner-cold-20261107/inventory.json')==cold['inventory_sha256']
 capacity=load('build/emulate-parent-owner-capacity-20261107/result.json',False)
 assert capacity['binary_sha256']==m['binary_sha256'] and capacity['held_streams'] and capacity['clock_queries']
 failures=[n for n,v in capacity['checks'].items()if not v];assert len(failures)==7 and len(capacity['checks'])==27
 control=ROOT/'build/emulate-parent-owner-control-final-20261107';c=json.loads((control/'manifest.json').read_text())
 assert not c['experimental_aspect_emulate_policy'] and sha(control/'TERMINAL.EXE')==c['binary_sha256']=='689bdce91c267320b4aad9136a530ab8ce90f733f4a540197e53e6ce4074df06'
 for n,h in c['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 control_capacity=load('build/emulate-parent-owner-capacity-control-20261107/result.json')
 assert control_capacity['binary_sha256']==c['binary_sha256'] and control_capacity['interpreter_sha256']==capacity['interpreter_sha256']
 assert len(control_capacity['checks'])==27 and all(control_capacity['checks'].values())
 old=c['memory_layout'];new=m['memory_layout'];assert new['near_bytes']==old['near_bytes']==65504
 assert new['minimum_allocated_module_bytes']-old['minimum_allocated_module_bytes']==256
 assert new['resident_CS_extent_bytes']-old['resident_CS_extent_bytes']==8
 for n in ('standalone/record_aspect_emulate_parent.py','standalone/alarm_connection_candidate_recipe.json'):sources[n]=sha(ROOT/n)
 result=dict(passed=False,component_checks_passed=True,release_accepted=False,installed_changed=False,RPC_bound=False,VM_opcode_bound=False,
  parent_sha256=m['binary_sha256'],control_sha256=c['binary_sha256'],sources=sources,receipts=receipts,
  summary=dict(linked_cases=294,cold_source_files=cold['source_files'],cold_repeated_cases=cold['cases'],near_bytes=65504,resident_code_bytes=new['resident_CS_extent_bytes'],minimum_including_PSP=new['minimum_allocated_module_bytes']+256,minimum_growth=256,capacity_checks=27,control_capacity_passed=27,capacity_failures=failures),
  limitations=['Not accepted: held six-stream/real nested-child capacity fails7of27 checks after the256-byte parent growth. Fund memory without reducing capacities, then rerun before RPC/opcode or deployment acceptance.',
   'Linked matrix executes real admission/stage/reset/keymap code with modeled BIOS/DOS/UART and seeded script-owner state. No actual child lease/RPC/VM opcode, real DOS profile reset, sustained receive latency or physical acceptance.',
   'Maintained4/6 transaction, not full original loader or all33 emulations. Keyboard-close ambiguity quarantines this script owner until parent restart; it does not repair every existing setup-reader caller.',
   'Cold public export repeats294 linked cases, not the failing real-DOS capacity suite. Ordinary689 parent and installed package remain unchanged.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('Recorded UNACCEPTED parent:294 linked cases pass,7of27 capacity checks fail')
if __name__=='__main__':main()
