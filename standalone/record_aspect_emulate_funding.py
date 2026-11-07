#!/usr/bin/env python3
"""Bind EMULATE memory funding, equivalent handoff checks and restored capacity."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={}
 def load(name):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed'],name;receipts[name]=sha(path)
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n;sources[n]=h
  return r
 parent=ROOT/'build/emulate-parent-fixed-buffers-20261107';m=json.loads((parent/'manifest.json').read_text());product=sha(parent/'TERMINAL.EXE')
 assert product==m['binary_sha256'] and m['experimental_aspect_emulate_policy']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 linked=load('build/emulate-parent-funded-abi-checks-20261107/result.json');assert linked['parent_sha256']==product and len(linked['cases'])==306
 helpers={}
 for label,folder,count in [('device','emulate-script-device-buffer-final-equivalence-20261107',113580),('word','emulate-script-word-buffer-final-equivalence-20261107',65536),('buffers','emulate-script-buffer-final-equivalence-20261107',2686976)]:
  r=load('build/'+folder+'/result.json');assert r['cases']==count and not r['original_inputs']
  for n,h in r['artifacts'].items():assert sha(ROOT/'build'/folder/n)==h,n
  helpers[label]=count
 text=(ROOT/'build/emulate-script-device-buffer-final-equivalence-20261107/test.c').read_text()
 assert 'for(n=0;n<256;++n)if(original_character(n)!=compact_character(n))return 2;'in text
 capacities=[]
 for folder,cpu,held,count in [('emulate-parent-fixed-buffers-capacity-20261107','8086',True,27),('emulate-parent-funded-capacity-8086-20261107','8086',False,26),('emulate-parent-funded-capacity-386-20261107','386',True,27)]:
  r=load('build/'+folder+'/result.json');assert r['binary_sha256']==product and r['cpu']==cpu and r['held_streams']==held and len(r['checks'])==count and all(r['checks'].values())
  assert r['clock_queries'] and r['nested_child_count']==3
  capacities.append(dict(cpu=cpu,held_streams=held,checks=count));child=r['interpreter_sha256']
 cold=load('build/emulate-parent-funded-cold-20261107/result.json');assert cold['parent_sha256']==product and cold['child_sha256']==child and cold['cases']==306
 repeated=ROOT/'build/emulate-parent-funded-cold-20261107/source/build/tests/result.json'
 assert sha(repeated)==cold['repeated_result_sha256'] and json.loads(repeated.read_text())['cases']==linked['cases']
 assert sha(ROOT/'build/emulate-parent-funded-cold-20261107/inventory.json')==cold['inventory_sha256']
 for label,c in cold['repeated_suites'].items():
  path=ROOT/'build/emulate-parent-funded-cold-20261107/source/build'/label/'result.json';r=json.loads(path.read_text())
  assert r['passed'] and sha(path)==c['sha256']
  if label!='capacity':assert c['cases']==helpers[label]
  else:assert c['cases']==27 and r['held_streams'] and r['cpu']=='8086'
 control=ROOT/'build/emulate-funding-ordinary-control-20261107';c=json.loads((control/'manifest.json').read_text())
 assert c['binary_sha256']==sha(control/'TERMINAL.EXE')=='689bdce91c267320b4aad9136a530ab8ce90f733f4a540197e53e6ce4074df06' and not c['experimental_aspect_emulate_policy']
 for n,h in c['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 historical=ROOT/'docs/validation/aspect-emulate-parent.json';old=json.loads(historical.read_text());assert not old['passed'] and not old['release_accepted'] and len(old['summary']['capacity_failures'])==7;receipts[str(historical.relative_to(ROOT))]=sha(historical)
 new=m['memory_layout'];base=c['memory_layout'];old_min=old['summary']['minimum_including_PSP']
 assert old_min-(new['minimum_allocated_module_bytes']+256)==208
 assert new['minimum_allocated_module_bytes']-base['minimum_allocated_module_bytes']==48 and new['near_bytes']==base['near_bytes']==65504
 assert new['resident_CS_extent_bytes']==65460 and base['resident_CS_extent_bytes']==65452
 sources['standalone/record_aspect_emulate_funding.py']=sha(Path(__file__))
 report=dict(passed=True,parent_component_capacity_accepted=True,release_accepted=False,RPC_bound=False,VM_opcode_bound=False,installed_changed=False,
  parent_sha256=product,interpreter_sha256=child,control_sha256=c['binary_sha256'],sources=sources,receipts=receipts,
  summary=dict(linked_cases=306,device_cases=113580,character_cases=256,word_cases=65536,buffer_cases=2686976,capacities=capacities,cold_source_files=cold['source_files'],cold_repeated_capacity=27,minimum_including_PSP=new['minimum_allocated_module_bytes']+256,minimum_saved=208,minimum_growth_over_control=48,near_bytes=65504,resident_code_bytes=65460),
  original_inputs=[],limitations=['Only the parent component is accepted for continued integration. No child RPC/opcode binding, actual DOS profile switch, fatal-reset fault injection, sustained-RX latency, current BBS/package or physical acceptance.',
   'Pure C helper comparisons use actual DOS8086 source branches. Device/character, word and extent checks are separate from whole path/namespace resolution; the buffer matrix does not enumerate all2^32 pairs or dereference arbitrary pointers.',
   'Held streams/nested children pass in the specified8086/386 configurations. A48-byte minimum increase remains; this is not a universal memory-headroom or peak guarantee.',
   'Cold export repeats all306 linked cases and three helper suites plus8086 held capacity, not the whole root CPU matrix. Public HEAD plus declared overlays; no originals/private configuration/prior objects/Git ancestry.',
   'Ordinary689 parent and installed R59A85A8 remain unchanged. Full original feature inventory stays open.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS EMULATE funding and capacity',report['summary'])
if __name__=='__main__':main()
