#!/usr/bin/env python3
"""Bind optional Help storage lifetime checks, cold rebuild and remaining failures."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
 receipts={}
 def read(name):
  p=ROOT/name;receipts[name]=sha(p);return json.loads(p.read_text())
 child=read('build/deferred-help-child-20261108/manifest.json')
 control=read('build/deferred-help-disabled-control-20261108/manifest.json')
 for folder,m in [('deferred-help-child-20261108',child),('deferred-help-disabled-control-20261108',control)]:
  assert sha(ROOT/'build'/folder/'ASPECT.EXE')==m['binary_sha256']
  assert m['original_inputs']==[]
  for name,h in m['sources'].items():assert sha(ROOT/name)==h,name
 assert child['experimental_deferred_help_resource']
 assert control['binary_sha256']=='96ea98c9537f3d54b20d02fd8a5f5ec93849f2b01e0485b1a0b867ad199671ab'
 a,b=control['GET_bank_layout'],child['GET_bank_layout']
 assert a['DGROUP_bytes']-b['DGROUP_bytes']==3424
 assert a['minimum_DOS_bytes_including_PSP']-b['minimum_DOS_bytes_including_PSP']==2912
 for key in ['stack_bytes','GET_code_bytes','editor_code_bytes','field_state_bytes']:
  assert a[key]==b[key]
 components=[]
 for folder,count,deferred in [('deferred-help-component-20261108',84,True),('deferred-help-legacy-component-20261108',49,False)]:
  c=read('build/'+folder+'/result.json')
  assert c['passed'] and all(c['checks'].values()) and c['self_checks']==count
  assert c['deferred']==deferred and c['original_inputs']==[]
  for name,h in c['sources'].items():assert sha(ROOT/name)==h,name
  components.append(dict(deferred=deferred,checks=count))
 source=read('build/deferred-help-source-20261108/checks.json')
 assert source['passed'] and len(source['cases'])==2 and source['CONNECTED_probe']
 assert source['source_compiler_residency_verified']
 assert all(c['runner_sha256']==child['binary_sha256'] and all(c['checks'].values()) for c in source['cases'])
 proof=read('build/deferred-help-source-export-20261108/result.json')
 assert proof['passed'] and proof['original_inputs']==[] and proof['DOS_cases']==2
 assert proof['artifacts']['ASPECT.EXE']==child['binary_sha256']
 for name,h in proof['sources'].items():assert sha(ROOT/name)==h,name
 capacity=read('build/deferred-help-capacity-20261108/result.json')
 assert not capacity['passed'] and capacity['cpu']=='8086' and not capacity.get('exit_watch')
 assert capacity['interpreter_sha256']==child['binary_sha256']
 assert capacity['held_streams'] and capacity['streams_around_child'] and capacity['checks']['held_files_preserved']
 assert not capacity['checks']['three_nested_children']
 screen=ROOT/'build/connection-dos/deferred-help-capacity-20261108/screen.txt'
 assert 'out of memory (error 8, opcode 9B, step 20)' in screen.read_text()
 receipts[str(screen.relative_to(ROOT))]=sha(screen)
 live=read('build/notice-help/deferred-help-full-v5-20261108/result.json')
 assert not live['passed'] and live['child_sha256']==child['binary_sha256']
 assert live['child_input']['notice_service']==4 and live['help']['help_seen']==0
 assert live['checks']['hardware_restored'] and live['checks']['binary_unchanged']
 result=dict(schema=1,checkpoint_verified=True,package_eligible=False,
  child_sha256=child['binary_sha256'],disabled_sha256=control['binary_sha256'],
  measured_layout=dict(before=a,after=b,DGROUP_saved=3424,DOS_minimum_saved=2912),
  component_checks=components,full_parent_source_cases=2,cold_source_files=len(proof['sources']),
  capacity_passed=False,six_held_files_preserved=True,live_Help_passed=False,
  receipts=receipts,recorder_sha256=sha(Path(__file__)),
  installed_changed=False,selector_changed=False,physical_verified=False,
  limits=['Optional storage placement only; Help page sizes, six512B file buffers and8192B stack unchanged.',
   'Capacity now opens/preserves all six files but fails PROGRAM preparation with heap error8.',
   'Full-parent Help attempt returns memory service4 without opening Help; not acceptance.',
   'Early Help attempts used stale adapter/port/partial-PRM fixtures and are excluded.',
   'Cold source proof covers exact artifacts and two source compilations, not full capacity or physical hardware.'])
 (ROOT/'docs/validation/deferred-help-storage.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Verified3424B DGROUP/2912B DOS saving;84+49 component checks;2 cold DOS replays; capacity and live Help still open')


if __name__=='__main__':main()
