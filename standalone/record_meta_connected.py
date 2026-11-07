#!/usr/bin/env python3
"""Bind connected Meta acceptance and paired release-blocking capacity evidence."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('enigma','synchronet','synchronet-core','enigma-controls','synchronet-controls','observers','candidate','module','control','resize-candidate','resize-module','resize-control','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def read(path):
  path=path.resolve();assert path.is_relative_to(ROOT)
  r=json.loads(path.read_text());receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h and(n not in sources or sources[n]==h),n;sources[n]=h
  return r
 parent='b92cdae7a4a9770451b076d12175e05280e64252cd0b6d45cb63510b58e7fcbb';connected={}
 for name in ('enigma','synchronet'):
  folder=getattr(a,name).resolve();r=read(folder/'proxy-integration.json');meta=read(folder/'meta-front-audit.json');cells=read(folder/'size-probe-screen-audit.json');screen=read(folder/'screen-reference-audit.json')
  assert r['passed']and meta['passed']and cells['passed']and screen['passed'] and r['binary_sha256']==meta['binary_sha256']==cells['binary_sha256']==parent
  for n,h in r['product_inputs'].items():
   assert sha(ROOT/n)==h,n
   if not n.startswith('build/'):sources[n]=h
  assert cells['different_cells']==screen['different_cells']==0 and cells['matched_cells']==1920 and cells['NAWS']==[[80,24]]
  assert all(meta['checks'].values())
  if name=='synchronet':assert r['checks']['Meta_observer_in_UMB']and r['meta_observer_segment']>=0xa000
  else:assert read(folder/'semantic-audit.json')['checks']['no_post_saved']
  controls=read(getattr(a,name+'_controls').resolve()/'result.json');assert controls['passed']and len(controls['cases'])==10
  for c in controls['cases']:assert c['rejected']==(c['case']!='unchanged')
  for n,h in controls['capture_inputs'].items():assert sha(folder/n)==h
  for n in ('METAVIEW.BIN','serial-received.bin','BEFORE.BIN','AFTER.BIN','SCREEN.BIN'):receipts[str((folder/n).relative_to(ROOT))]=sha(folder/n)
  assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
  connected[name]=dict(passed=True,checks=meta['checks'],cells=1920,different_cells=0,actual_CPR=cells['actual_CPR'],negative_controls=9,observer_segment=r.get('meta_observer_segment'),scope=r['scope'])
 # The core run preceded the optional harness edits. Verify its two original
 # public source versions from the committed Git object, rather than silently
 # treating current source hashes as those historical inputs.
 core=read(a.synchronet_core.resolve()/'proxy-integration.json')
 assert core['passed']and core['binary_sha256']==parent and '--cpu'in core['command']and core['command'][core['command'].index('--cpu')+1]=='8086'
 import subprocess,hashlib
 archived={}
 for n,h in core['product_inputs'].items():
  if sha(ROOT/n)==h:continue
  assert n in ('lab/bbs/test_synchronet_screen_reference_dos.py','lab/bbs/audio_synchronet_editor_keys.asm'),n
  old=subprocess.check_output(['git','show','4b84579:'+n],cwd=ROOT)
  assert hashlib.sha256(old).hexdigest()==h,n
  archived[n]=dict(commit='4b84579',sha256=h)
 ordinary={};traces={}
 for name in ('candidate','module','control'):
  r=read(getattr(a,name).resolve()/'result.json');assert r['cpu']=='8086'and not r.get('exit_watch')and r['passed']==(name=='control') and len(r['checks'])==30
  assert r['held_streams']and r['streams_around_child']and r['emulate_profile_switch']
  assert r['interpreter_sha256']=='5c641ac458494d8d6d7cb048d13dc531830689a4e401df7011092057c37ef066'
  ordinary[name]=dict(binary_sha256=r['binary_sha256'],passed=r['passed'],checks=r['checks'])
  t=read(getattr(a,'resize_'+name).resolve()/'result.json');assert t['cpu']=='386'and t['exit_watch_high'] and t['heap_resize_watch']and t['exit_watch']['resident_segment']>=0xa000 and t['passed']==(name=='control') and t['binary_sha256']==r['binary_sha256']
  failures=[v for v in t['exit_watch']['allocations']if v['carry']]
  assert bool(failures)==(name!='control')and all(v['ax']==8 for v in failures)
  traces[name]=dict(passed=t['passed'],failures=failures,exit_codes=[v['exit']for v in t['exit_watch']['exits']],observer_segment=t['exit_watch']['resident_segment'])
  path=ROOT/'build/connection-dos'/getattr(a,'resize_'+name).name/'EXITSTAT.BIN';receipts[str(path.relative_to(ROOT))]=sha(path)
 assert ordinary['candidate']['binary_sha256']==parent
 assert ordinary['control']['binary_sha256']=='ff6bb369a8b3693cefc357fec901ae576139cafe8915f8e60818ddcdde2e5399'
 assert traces['candidate']['failures'][0]['paragraphs']==8547 and traces['candidate']['failures'][0]['bx']==8536
 assert traces['module']['failures'][0]['paragraphs']==254 and traces['module']['failures'][0]['bx']==9
 o=read(a.observers.resolve()/'result.json');assert o['passed']and len(o['cases'])==6
 for n,h in o['captures'].items():assert sha(ROOT/n)==h;receipts[n]=h
 for n in ('standalone/record_meta_connected.py','docs/META_CONNECTED.md'):sources[n]=sha(ROOT/n)
 result=dict(evidence_verified=True,connected_modal_gates_passed=True,capacity_regression_confirmed=True,release_eligible=False,installed_changed=False,physical_acceptance=False,parent_sha256=parent,connected=connected,synchronet_unobserved_8086_core=dict(passed=True,checks=core['checks'],prior_harness_sources=archived),ordinary_capacity=ordinary,separate_allocation_traces=traces,unchanged_helper_variants=o['cases'],sources=sources,receipts=receipts,original_inputs=[],limitations=['250ms key framing and20ms pacing; no immediate/unframed, physical CTS or SIP/audio acceptance.','Observed Synchronet run uses386/UMB; ordinary unobserved8086 core pass is separate.','Bounded memory traces are diagnostics, not complete peak requirements or ordinary acceptance.','Loader-only and full Meta residency regressions must be fixed before release; full goal remains active.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('Verified two connected Meta round trips; paired capacity regression confirmed; release ineligible')
if __name__=='__main__':main()
