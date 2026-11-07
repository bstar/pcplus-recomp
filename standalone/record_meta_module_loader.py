#!/usr/bin/env python3
"""Bind the matched META loader, composed parent, runtime refusals and exports."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('direct','fault','refusals','probe','probe-DOS','source-proof','parent','parent-proof','disabled','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={};values={}
 for name in ('direct','fault','refusals','probe_DOS','source_proof','parent_proof'):
  folder=getattr(a,name).resolve();assert folder.is_relative_to(ROOT/'build');v=json.loads((folder/'result.json').read_text());assert v['passed'];values[name]=v;receipts[str((folder/'result.json').relative_to(ROOT))]=sha(folder/'result.json')
  for n,h in v['sources'].items():assert sha(ROOT/n)==h and(n not in sources or sources[n]==h);sources[n]=h
 d,f,r,live,cold,parent_cold=(values[n]for n in ('direct','fault','refusals','probe_DOS','source_proof','parent_proof'))
 for name,v in (('direct',d),('fault',f)):
  assert v['faults']==(name=='fault')and v['cpu']=='8086'and v['original_inputs']==[]
  assert sha(getattr(a,name).resolve()/'METAEDIT.EXE')==v['parent_sha256']==cold['binaries'][name]
  assert sha(getattr(a,name).resolve()/'PCMETA.OVL')==v['overlay']['sha256']==cold['component_overlays'][name]
  assert v['overlay']['bank_bytes']==21619 and v['overlay']['relocations']==17 and v['new_loader_DGROUP_bytes']==0
  assert 'PASS 3069 checks;'in v['logs']and 'PASS loader 68 checks;'in v['logs']
  assert v['loader_segments']['meta_loader']['FILE_CODE']==1379 and v['loader_segments']['meta_loader_fs']=={'FILE_CODE':112}and v['loader_segments']['meta_loader_path']=={'CONFIG_CODE':20}
 assert len(r['cases'])==cold['refusal_cases']==20 and len({c['case']for c in r['cases']})==20
 assert r['producers']['direct']['parent_sha256']==d['parent_sha256']and r['producers']['fault']['parent_sha256']==f['parent_sha256']
 assert cold['ancestor_git_unavailable']and cold['source_count']==733 and cold['parent_DOS_checks']==live['checks']==19
 pm={}
 for name in ('parent','probe','disabled'):
  folder=getattr(a,name).resolve();assert folder.is_relative_to(ROOT/'build');v=json.loads((folder/'manifest.json').read_text());assert sha(folder/'TERMINAL.EXE')==v['binary_sha256'];pm[name]=v;receipts[str((folder/'manifest.json').relative_to(ROOT))]=sha(folder/'manifest.json')
  for n,h in v['sources'].items():assert sha(ROOT/n)==h and(n not in sources or sources[n]==h);sources[n]=h
 parent,probe,disabled=(pm[n]for n in ('parent','probe','disabled'))
 assert parent['experimental_meta_editor_module']and not parent['diagnostic_meta_loader_probe']and probe['diagnostic_meta_loader_probe']and not disabled['experimental_meta_editor_module']
 assert parent_cold['ancestor_git_unavailable']and parent_cold['source_count']==725 and parent_cold['binary_sha256']==parent['binary_sha256']
 assert {c['case']for c in parent_cold['runs']}=={'save','serviced','readonly','portbusy'}and all(all(c['checks'].values())for c in parent_cold['runs'])
 for key,filename,proof_key in (('meta_editor_overlay','PCMETA.OVL','meta_overlay_sha256'),('line_port_overlay','PCLINE.OVL','overlay_sha256')):
  assert parent[key]['sha256']==sha(a.parent.resolve()/filename)==parent_cold[proof_key]
 assert probe['binary_sha256']==live['parent_sha256']==cold['binaries']['probe']and probe['meta_editor_overlay']['sha256']==live['overlay_sha256']==cold['parent_overlay_sha256']
 assert probe['line_port_overlay']['sha256']==live['line_overlay_sha256']==cold['parent_line_overlay_sha256']
 assert parent['meta_editor_overlay']['bank_bytes']==21612 and parent['meta_editor_overlay']['relocations']==17
 assert disabled['binary_sha256']=='ff6bb369a8b3693cefc357fec901ae576139cafe8915f8e60818ddcdde2e5399'
 now,old=parent['memory_layout'],disabled['memory_layout'];caps=('near_bytes','far_bytes','history_bytes','snapshot_bytes','redisplay_snapshot_bytes','native_reset_private_stack_bytes','native_reset_shadow_bytes','native_reset_workspace_bytes','far_ui_storage_bytes')
 assert all(now[n]==old[n]for n in caps)and now['minimum_allocated_module_bytes']==480608 and old['minimum_allocated_module_bytes']==479024
 assert now['resident_code_bytes']==65024 and parent['data_stack_bytes']==disabled['data_stack_bytes']==65520
 assert now['meta_loader_retained']and not now['meta_editor_UI_bound']and now['meta_overlay_DGROUP_bytes']==0
 for n in ('standalone/record_meta_module_loader.py','docs/META_MODULE_LOADER.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,loader_implemented=True,full_parent_probe_verified=True,normal_editor_UI_bound=False,live_action_adoption=False,installed_changed=False,physical_runtime_verified=False,component_parents={n:v['parent_sha256']for n,v in (('direct',d),('fault',f))},component_modules={n:v['overlay']['sha256']for n,v in (('direct',d),('fault',f))},normal_parent_sha256=parent['binary_sha256'],normal_meta_sha256=parent['meta_editor_overlay']['sha256'],normal_line_sha256=parent['line_port_overlay']['sha256'],probe_parent_sha256=probe['binary_sha256'],disabled_parent_sha256=disabled['binary_sha256'],workflow_assertions_each=3069,loader_checks_each=68,full_parent_checks=19,refusal_cases=20,isolated_sources=cold['source_count'],normal_parent_isolated_sources=parent_cold['source_count'],exact_relocated_code_sha256={n:v['exact_relocated_code_sha256']for n,v in (('direct',d),('fault',f))},parent_bank_bytes=21612,component_bank_bytes=21619,fixups_each=17,loader_FILE_bytes=1379,loader_kernel_FILE_bytes=112,loader_path_CONFIG_bytes=20,DGROUP_additions=0,minimum_retained_bytes=480608,baseline_retained_bytes=479024,capacities_unchanged={n:now[n]for n in caps},sources=sources,receipts=receipts,original_inputs=[],limitations=['Explicit caller arena grant; ordinary live arbitration/menu/Alt-M/frame and internal IO handoff are not integrated.','Closed-lease proposal/runtime comparison and atomic live action adoption remain open.','Startup-only actual parent and synthetic-peer regressions; connected Meta modal UART/BBS/physical acceptance and original pixel equality remain open. Installed RCE81708 untouched.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS matched META receipt:three exact source-built EXEs;733/725-source exports;full-parent save/reload;20 refusals;disabled exact')
if __name__=='__main__':main()
