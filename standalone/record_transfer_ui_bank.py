#!/usr/bin/env python3
"""Seal build capacity, bridge validation and transfer/mouse behavior together."""
import argparse,hashlib,json,re
from pathlib import Path
from terminal_memory import inspect_terminal_memory
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 baseline=a.baseline.resolve();target=a.output.resolve();assert baseline.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 old=load(baseline);assert old['expected_baseline_reproduced'] and old['source_checkpoint'].startswith('c154f20')
 assert len(old['cases'])==3 and old['cases'][0]['binary_sha256'].startswith('3b0deeeb')
 for row in old['cases']:
  assert sha(baseline.parent/row['log'])==row['log_sha256']
  if row['name']!='terminal':assert row['exit_code']!=0 and row['resident_overflow_bytes']==146
 captures={str(baseline.relative_to(ROOT)):sha(baseline)}
 for row in old['cases']:captures[str((baseline.parent/row['log']).relative_to(ROOT))]=row['log_sha256']
 builds={};native_flat={}
 provenance=load(ROOT/'reconstruction/transfer_send/provenance.json')
 for name in ('terminal','terminal-mouse','terminal-mouse-process','terminal-traps-mouse'):
  out=ROOT/'build'/name;binary=out/'TERMINAL.EXE';m=load(out/'manifest.json');guard=load(out/'terminal-transfer-ui-bank.json');memory=inspect_terminal_memory(binary,out/'terminal.map')
  assert guard['passed'] and len(guard['cases'])==19 and all(c['passed'] for c in guard['cases'])
  assert sha(binary)==m['binary_sha256']==guard['binary_sha256']
  assert memory==m['memory_layout'] and memory['resident_code_spare_bytes']>=400
  assert memory['transfer_ui_far_entries_verified']==4 and memory['transfer_ui_resident_callbacks_verified']==3
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
  for n,h in guard['inputs'].items():assert sha(ROOT/n)==h,n
  assert guard['map_sha256']==sha(out/'terminal.map')
  for leaf in ('session','cancel'):
   unit=next(u for u in provenance['units'] if u['source']==leaf+'.asm');flat=out/'native-sender'/('transfer_send_'+leaf+'.bin')
   assert sha(flat)==unit['sha256'] and flat.stat().st_size==unit['bytes'];native_flat[leaf]=unit['sha256']
  builds[name]=dict(binary_sha256=sha(binary),resident_bytes=memory['resident_code_bytes'],resident_spare=memory['resident_code_spare_bytes'],data_stack_bytes=m['data_stack_bytes'],bridge_controls=len(guard['cases']))
  for p in (out/'manifest.json',out/'terminal.map',out/'terminal-transfer-ui-bank.json'):captures[str(p.relative_to(ROOT))]=sha(p)
 current=builds['terminal']['binary_sha256'];linked={}
 for name,count in [('terminal-upload-startup.json',43),('terminal-upload-live-checks.json',54),('terminal-upload-cancel-boundary.json',37),('terminal-transfer-live-checks.json',44),('terminal-ymodem-live-checks.json',23),('terminal-zmodem-live-checks.json',78),('zmodem-cancel-checks.json',5)]:
  p=ROOT/'build/terminal'/name;r=load(p);assert r['passed'] and r['binary_sha256']==current
  got=r['inputs'] if isinstance(r.get('inputs'),int) else len(r['cases']);assert got==count,(name,got)
  linked[name]=count;captures[str(p.relative_to(ROOT))]=sha(p)
 policy=ROOT/'build/terminal-mouse/mouse-policy.json';mp=load(policy);assert mp['passed'] and mp['binary_sha256']==builds['terminal-mouse']['binary_sha256'] and len(mp['cases'])==31
 captures[str(policy.relative_to(ROOT))]=sha(policy)
 actual={}
 for kind,folder,report,expected in [('startup',ROOT/'build/terminal-upload-dos'/a.label,'startup-checks.json',current),('mouse',ROOT/'build/terminal-mouse-tests'/a.label,'checks.json',builds['terminal-mouse']['binary_sha256'])]:
  r=load(folder/report);assert r['passed'] and r['binary_sha256']==expected and len(r['cases'])==3
  assert all(c['passed'] and all(c['checks'].values()) for c in r['cases'])
  for n,h in r.get('inputs',r.get('sources',{})).items():assert sha(ROOT/n)==h,n
  actual[kind]=dict(cases=r['cases'],binary_sha256=expected)
  for p in folder.rglob('*'):
   if p.is_file():captures[str(p.relative_to(ROOT))]=sha(p)
 paths=['src/terminal/transfer_ui.asm','src/terminal/transfer_ui_bridge.asm','standalone/terminal_memory.py','standalone/check_transfer_ui_bank.py','standalone/build_terminal.py','standalone/record_transfer_ui_bank.py','Makefile']
 baseline_listing=(baseline.parent/'terminal/terminal.map').read_text();old_code=int(re.search(r'^_TEXT\s+CODE\s+\S+\s+\S+\s+([0-9a-f]+)',baseline_listing,re.M|re.I)[1],16)
 result=dict(passed=True,transfer_ui_banking_accepted=True,actual_audio_accepted=False,baseline_source_checkpoint=old['source_checkpoint'],baseline_cases=old['cases'],builds=builds,
  prior_resident_bytes=old_code,resident_bytes_saved=old_code-builds['terminal']['resident_bytes'],unchanged_native_flat_sha256=native_flat,linked_transfer_cases=linked,linked_mouse_cases=31,actual_DOS=actual,
  inputs={n:sha(ROOT/n) for n in paths},capture_sha256=captures,recorder_sha256=sha(Path(__file__)),
  scope='Transfer prompt/progress/restore body moved from resident_TEXT to CONFIG_CODE with four unchanged no-argument resident entry APIs and three resident service/keyboard callbacks. Exact far targets/returns/MZ relocations are build-time invariants;18 invalid variants reject for each of four reproduced binaries. Original near-bank3b and146-byte mouse overflows reproduce fromc154f20. All declared linked protocol/mouse cases and six actual DOS startup/mouse/menu/PROGRAM cases pass. DS=SS and retained far extents verify for every build. Actual audio acceptance belongs to the separate frozen3b receipt, not these new binaries. No physical modem, all mouse interactions or F01-F16 completion claim.')
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,builds=len(builds),resident_bytes_saved=result['resident_bytes_saved'],linked_transfer_cases=sum(linked.values()),actual_DOS_cases=6,receipt=str(target))))

if __name__=='__main__':main()
