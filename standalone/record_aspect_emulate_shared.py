#!/usr/bin/env python3
"""Bind shared client guards/completion, restored EMULATE capacity and cold proof."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha
from record_aspect_emulate_rpc import minimum

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={}
 def load(name):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed'],name;receipts[name]=sha(path)
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n;sources[n]=h
  return r
 products={}
 for name,folder in [('TERMINAL.EXE','emulate-rpc-parent-20261107'),('ASPECT.EXE','emulate-rpc-child-checked-20261107')]:
  root=ROOT/'build'/folder;m=json.loads((root/'manifest.json').read_text());assert sha(root/name)==m['binary_sha256']
  for n,h in m['sources'].items():assert Path(n).parts[0]not in ('analysis','build','.git') and sha(ROOT/n)==h,n;sources[n]=h
  products[name]=dict(sha256=m['binary_sha256'],minimum_including_PSP=minimum(root/name))
 assert products['ASPECT.EXE']['minimum_including_PSP']==131136 and products['TERMINAL.EXE']['minimum_including_PSP']==479760
 model=load('build/emulate-response-complete-equivalence-20261107/result.json');assert model['cases']==38400
 for n,h in model['artifacts'].items():assert sha(ROOT/'build/emulate-response-complete-equivalence-20261107'/n)==h,n
 capacities=[]
 for folder,cpu,held,count in [('emulate-rpc-checked-capacity-20261107','386',True,30),('emulate-rpc-checked-capacity-8086-20261107','8086',False,29)]:
  r=load('build/'+folder+'/result.json')
  assert r['binary_sha256']==products['TERMINAL.EXE']['sha256'] and r['interpreter_sha256']==products['ASPECT.EXE']['sha256']
  assert r['cpu']==cpu and r['held_streams']==held and r['emulate_profile_switch'] and r['clock_queries'] and r['nested_child_count']==3
  assert len(r['checks'])==count and all(r['checks'].values()) and r['checks']['both_profile_DA_pairs'] and r['checks']['profile_reset_replaces_old_view']
  capacities.append(dict(cpu=cpu,held=held,checks=count))
  root=ROOT/'build/connection-dos'/folder
  wire=(root/'serial.bin').read_bytes();assert wire.count(b'PROFILE4\r\x1b[?62;2cPROFILE6\r\x1b[?1;2c')==2
  for n in ('serial.bin','SCREEN.BIN','FIRST.ASX','NEST.LOG'):
   receipts[str((root/n).relative_to(ROOT))]=sha(root/n)
 alarm=load('build/emulate-rpc-checked-alarm-xoff-20261107/checks.json');assert alarm['profile']==6 and len(alarm['cases'])==1
 assert alarm['products']=={n:r['sha256']for n,r in products.items()}
 assert alarm['cases'][0]['case']=='XOFF' and alarm['cases'][0]['passed'] and all(alarm['cases'][0]['checks'].values())
 cold=load('build/emulate-rpc-shared-final-cold-20261107/result.json')
 assert cold['parent_sha256']==products['TERMINAL.EXE']['sha256'] and cold['child_sha256']==products['ASPECT.EXE']['sha256'] and cold['cases']==306
 assert sha(ROOT/'build/emulate-rpc-shared-final-cold-20261107/inventory.json')==cold['inventory_sha256']
 parent_test=load('build/emulate-rpc-shared-parent-checks-20261107/result.json');assert len(parent_test['cases'])==306
 path=ROOT/'build/emulate-rpc-shared-final-cold-20261107/source/build/tests/result.json';assert sha(path)==cold['repeated_result_sha256'] and json.loads(path.read_text())['cases']==parent_test['cases']
 for name,expected in [('device',113580),('word',65536),('buffers',2686976),('responses',38400),('capacity',30)]:
  c=cold['repeated_suites'][name];path=ROOT/'build/emulate-rpc-shared-final-cold-20261107/source/build'/name/'result.json';r=json.loads(path.read_text())
  assert r['passed'] and sha(path)==c['sha256'] and c['cases']==expected
  if name=='capacity':assert r['emulate_profile_switch'] and r['cpu']=='386' and r['held_streams']
 controls={}
 for folder,expected in [('emulate-rpc-response-control-20261107','b4f0aecc7a6538920711c2fa866324d2ddad856883a437cbb2f125cd0e26efbe'),('aspect-runner','91256a7b873b3ff65dd0b4df177f2dfaff2ee72860db5b3b4fd44c481f1d364b')]:
  root=ROOT/'build'/folder;m=json.loads((root/'manifest.json').read_text());assert sha(root/'ASPECT.EXE')==m['binary_sha256']==expected
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
  controls[folder]=expected
 prior=ROOT/'docs/validation/aspect-emulate-rpc.json';old=json.loads(prior.read_text());assert not old['passed'] and len(old['summary']['capacity_failures'])==8;receipts[str(prior.relative_to(ROOT))]=sha(prior)
 assert old['products']['ASPECT.EXE']['minimum_including_PSP']-products['ASPECT.EXE']['minimum_including_PSP']==208
 for n in ('standalone/record_aspect_emulate_shared.py','standalone/record_aspect_emulate_rpc.py','standalone/package_connection_test.py'):sources[n]=sha(ROOT/n)
 report=dict(passed=True,capacity_accepted=True,release_accepted=False,installed_changed=False,products=products,controls=controls,sources=sources,receipts=receipts,
  summary=dict(model_cases=38400,linked_parent_cases=306,capacity_profiles=capacities,ALARM_XOFF_cases=1,cold_source_files=cold['source_files'],cold_profile_checks=30,child_minimum_saved=208,combined_minimum=610896),original_inputs=[],
  limitations=['Differential C clients use modeled scalar bridge/client-check/serial boundaries. They compare results/call counts/traces/policy/probes, not actual stack-threshold equivalence, timing or all VM state.',
   'DOS profile/capacity and selected ALARM error use actual bridge/VM with synthetic peers. Physical modem/audio/CTS, expanded negative version/MCB/lease/WHEN/fatal-reset, sustained-RX timing and current Enigma/Synchronet/package gates remain open.',
   'Cold public export repeats306 linked cases, three handoff helper suites,38400 differential cases and386 held profile/capacity. It does not repeat root8086 or ALARM XOFF. No originals/private configuration/prior objects/Git ancestry.',
   'Ordinary b4f0/91256 controls remain exact; installed R59A85A8 unchanged. Capacity acceptance is limited to named configurations, not universal peak/headroom or full parity.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS shared client EMULATE funding',report['summary'])
if __name__=='__main__':main()
