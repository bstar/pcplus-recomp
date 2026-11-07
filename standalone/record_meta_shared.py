#!/usr/bin/env python3
"""Bind a shared Meta source checkpoint without declaring release acceptance."""
import argparse,json,re
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-tag',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert re.fullmatch(r'[A-Za-z0-9_-]+',a.run_tag);tag=a.run_tag;receipts={};sources={}
 def folder(name):return ROOT/'build'/('meta-shared-'+name+'-'+tag)
 def read(path,passed=True):
  path=path.resolve();assert path.is_relative_to(ROOT)
  r=json.loads(path.read_text());receipts[str(path.relative_to(ROOT))]=sha(path)
  if passed:assert r['passed'],path
  for n,h in r.get('sources',r.get('inputs',{})).items():
   assert sha(ROOT/n)==h and(n not in sources or sources[n]==h),n
   sources[n]=h
  return r
 parent=folder('help');m=read(parent/'manifest.json',False);package=read(parent/'package.json')
 assert m['experimental_meta_shared_runtime']and m['memory_layout']['meta_shared_runtime']
 digest=sha(parent/'TERMINAL.EXE');assert digest==m['binary_sha256']==package['products']['TERMINAL.EXE']
 for n,h in package['products'].items():assert sha(parent/n)==h;receipts[str((parent/n).relative_to(ROOT))]=h
 d=read(folder('disabled')/'manifest.json',False)
 assert d['binary_sha256']==sha(folder('disabled')/'TERMINAL.EXE')=='ff6bb369a8b3693cefc357fec901ae576139cafe8915f8e60818ddcdde2e5399'
 now,old=m['memory_layout'],d['memory_layout'];caps=('near_bytes','far_bytes','history_bytes','snapshot_bytes','redisplay_snapshot_bytes','native_reset_private_stack_bytes','native_reset_shadow_bytes','native_reset_workspace_bytes','far_ui_storage_bytes')
 assert all(now[n]==old[n]for n in caps)and now['minimum_allocated_module_bytes']<old['minimum_allocated_module_bytes']
 cold=read(folder('source')/'result.json');assert cold['ancestor_git_unavailable']and cold['binary_sha256']==digest
 assert cold['meta_overlay_sha256']==m['meta_editor_overlay']['sha256']and cold['overlay_sha256']==m['line_port_overlay']['sha256']
 assert len(cold['runs'])==4 and len(cold['meta_runs'])==3
 pressure=read(folder('held-meta')/'result.json');assert pressure['binary_sha256']==digest and pressure['cpu']=='8086'and not pressure.get('exit_watch')and pressure['meta_editor_around_scripts']
 assert len(pressure['checks'])==32 and all(pressure['checks'].values())and pressure['checks']['Meta_adoption_before_and_after_scripts']
 assert pressure['held_streams']and pressure['streams_around_child']and pressure['emulate_profile_switch']
 drive=ROOT/'build/connection-dos'/folder('held-meta').name
 wire=(drive/'serial.bin').read_bytes();assert wire.count(b'META1')==wire.count(b'META2')==1
 for n in ('serial.bin','SCREEN.BIN','BEFORE.BIN','AFTER.BIN','ACTIONS.KEY'):receipts[str((drive/n).relative_to(ROOT))]=sha(drive/n)
 help_result=read(folder('global-help')/'result.json');assert help_result['case']=='repeat'and help_result['products']==package['products']and all(help_result['checks'].values())
 reference=read(ROOT/'build/reference-dos'/('meta-shared-reference-'+tag)/'result.json');assert reference['binary_sha256']==digest and reference['checks']['all_39_commands_visible']
 ui=[]
 for case in ('edit','save','reference','browser','load','reload','cancel','missing','reference-cancel','reference-help','script-cancel','info-cancel'):
  r=read(folder(case)/'result.json');assert r['binary_sha256']==digest and r['case']==case and all(r['checks'].values());ui.append(dict(case=case,checks=r['checks']))
 for case in ('reference','browser'):
  r=read(folder('line-'+case)/'result.json');assert r['binary_sha256']==digest and all(r['checks'].values())
 faults=[]
 for module in ('line','meta'):
  for fault in ('missing','short','corrupt','extra'):
   r=read(folder(module+'-'+fault+'-fault')/'result.json');assert r['parent_sha256']==digest and r['module']==module and r['fault']==fault and all(r['checks'].values());faults.append(dict(module=module,fault=fault,checks=r['checks']))
 bbs={}
 for server,short in [('enigma','enigma'),('synchronet','sync')]:
  capture=ROOT/'build/bbs-lab/results'/server/('meta-shared-'+short+'-modal-'+tag)
  r=read(capture/'proxy-integration.json');meta=read(capture/'meta-front-audit.json');cells=read(capture/'size-probe-screen-audit.json');read(capture/'screen-reference-audit.json')
  assert r['binary_sha256']==meta['binary_sha256']==cells['binary_sha256']==digest and cells['different_cells']==0 and cells['matched_cells']==1920 and cells['NAWS']==[[80,24]]
  for n,h in r['product_inputs'].items():assert sha(ROOT/n)==h,n
  assert all(meta['checks'].values())and(capture/'BEFORE.BIN').read_bytes()==(capture/'AFTER.BIN').read_bytes()
  controls=read(folder(short+'-controls')/'result.json');assert len(controls['cases'])==10
  for v in controls['cases']:assert v['rejected']==(v['case']!='unchanged')
  for n,h in controls['capture_inputs'].items():assert sha(capture/n)==h
  for n in ('METAVIEW.BIN','SCREEN.BIN','BEFORE.BIN','AFTER.BIN'):receipts[str((capture/n).relative_to(ROOT))]=sha(capture/n)
  bbs[server]=dict(passed=True,checks=meta['checks'],matched_cells=1920,different_cells=0,CPR=cells['actual_CPR'],observer_segment=r.get('meta_observer_segment'),scope=r['scope'])
 core=read(ROOT/'build/bbs-lab/results/synchronet'/('meta-shared-sync-core-'+tag)/'proxy-integration.json')
 assert core['binary_sha256']==digest and core['command'][core['command'].index('--cpu')+1]=='8086'
 for n,h in core['product_inputs'].items():assert sha(ROOT/n)==h,n
 for n in ('standalone/record_meta_shared.py','docs/META_SHARED_RUNTIME.md'):sources[n]=sha(ROOT/n)
 report=dict(checkpoint_verified=True,capacity_gate_restored=True,release_eligible=False,installed_changed=False,physical_verified=False,parent_sha256=digest,products=package['products'],disabled_sha256=d['binary_sha256'],retained_bytes=now['minimum_allocated_module_bytes'],control_retained_bytes=old['minimum_allocated_module_bytes'],capacities_unchanged={n:now[n]for n in caps},bank_code_bytes=m['meta_editor_overlay']['bank_bytes'],bank_fixups=m['meta_editor_overlay']['relocations'],source_export_files=cold['source_count'],ordinary_pressure_checks=32,ui_cases=ui,module_refusals=faults,global_Help_repeated=True,reference_commands=39,connected=bbs,Synchronet_unobserved_8086_core=True,sources=sources,receipts=receipts,original_inputs=[],limitations=['Source-only shared-runtime checkpoint, not release/deployment or full original feature parity.','Connection/reconnect/transfer/carrier-loss must be repeated on these exact products.','Shared close/fixup fault injection and wider arena/history/arbitration cases remain open; independent loader tests are not a substitute.','Observed Synchronet386/UMB is distinct from ordinary8086 core and capacity tests.250ms framing/20ms pacing; physical CTS/SIP/audio acceptance remains open.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('Verified shared Meta:',now['minimum_allocated_module_bytes'],'retained bytes;32 pressure checks;12 UI;8 refusals;two BBS references;no release claim')
if __name__=='__main__':main()
