#!/usr/bin/env python3
"""Bind production Meta bank ABI, linked parent callbacks and clean-source gates."""
import argparse,hashlib,json
from pathlib import Path
from build_path_session import object_segments
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('direct','fault','bank-proof','callbacks','parent-proof','parent','disabled','control-bank','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={};values={}
 for n in ('direct','fault','bank_proof','callbacks','parent_proof','control_bank'):
  path=getattr(a,n).resolve();assert path.is_relative_to(ROOT/'build');v=json.loads((path/'result.json').read_text());assert v['passed'];values[n]=v;receipts[str((path/'result.json').relative_to(ROOT))]=sha(path/'result.json')
  for s,h in v['sources'].items():assert sha(ROOT/s)==h and (s not in sources or sources[s]==h);sources[s]=h
 direct,fault,bank,callbacks,parent_proof,control=(values[n] for n in ('direct','fault','bank_proof','callbacks','parent_proof','control_bank'))
 assert callbacks['diagnostic_sha256']==direct['binary_sha256']
 for n,v in (('direct',direct),('fault',fault)):
  assert v['parent_services'] and v['direct_kernel']==(n=='direct') and v['cpu']=='8086' and v['original_inputs']==[]
  assert v['binary_sha256']==bank['binaries'][n]==sha(getattr(a,n).resolve()/'METAEDIT.EXE')
  assert v['logs']==bank['logs'][n] and 'PASS bank memory 35332 checks;' in v['logs']['NORMAL.LOG'] and 'PASS bank kernel 166 checks;' in v['logs']['NORMAL.LOG'] and 'PASS 3069 checks;state 12870;' in v['logs']['NORMAL.LOG']
  assert v['calculated_product_payload_bytes']==21619 and v['editor_owned_DGROUP_bytes']==0
  assert v['new_parent_service_segments']=={'meta_bank_resident':{'_TEXT':44},'meta_bank_resource':{'CONFIG_CODE':20}}
 assert 'PASS fatal 981 checks;' in fault['logs']['FATAL.LOG'] and 'FATAL.LOG' not in direct['logs']
 assert bank['source_count']==56 and bank['ancestor_git_unavailable'] and parent_proof['source_count']==707 and parent_proof['ancestor_git_unavailable']
 parent=a.parent.resolve();disabled=a.disabled.resolve();assert all(q.is_relative_to(ROOT/'build')for q in (parent,disabled))
 pm=json.loads((parent/'manifest.json').read_text());dm=json.loads((disabled/'manifest.json').read_text());old=json.loads((ROOT/'docs/validation/meta-editor-bank.json').read_text())
 assert pm['experimental_meta_services'] and not dm['experimental_meta_services'] and sha(parent/'TERMINAL.EXE')==pm['binary_sha256']==callbacks['linked_parent_sha256']==parent_proof['binary_sha256']
 assert sha(parent/'PCLINE.OVL')==parent_proof['overlay_sha256']==pm['line_port_overlay']['sha256']
 assert dm['binary_sha256']==sha(disabled/'TERMINAL.EXE')==callbacks['parent_sha256']=='ff6bb369a8b3693cefc357fec901ae576139cafe8915f8e60818ddcdde2e5399'
 assert control['binary_sha256']==old['direct_sha256']==sha(a.control_bank.resolve()/'METAEDIT.EXE')
 assert {r['case']for r in parent_proof['runs']}=={'save','serviced','readonly','portbusy'} and all(all(r['checks'].values())for r in parent_proof['runs'])
 live,base=pm['memory_layout'],dm['memory_layout'];capacity_names=('near_bytes','far_bytes','history_bytes','snapshot_bytes','redisplay_snapshot_bytes','native_reset_private_stack_bytes','native_reset_shadow_bytes','native_reset_workspace_bytes','far_ui_storage_bytes')
 assert all(live[n]==base[n]for n in capacity_names)
 assert live['resident_code_bytes']-base['resident_code_bytes']==44 and live['minimum_allocated_module_bytes']-base['minimum_allocated_module_bytes']==64
 assert pm['data_stack_bytes']==dm['data_stack_bytes']==65520
 sizes=object_segments(parent/'key_actions_dos.obj');assert sizes['_TEXT']['bytes']==611 and all(n=='_TEXT' or not s['bytes']for n,s in sizes.items())
 assert len(callbacks['existing_services']['callbacks'])==7 and len(callbacks['new_services']['callbacks'])==4 and len(callbacks['linked_parent_new_services']['callbacks'])==4
 assert sum(len(callbacks[n]['invalid_variants_rejected'])for n in ('existing_services','new_services','linked_parent_new_services'))==30
 for s in ('standalone/record_meta_parent_services.py','standalone/check_meta_parent_bindings.py','standalone/build_path_session.py','docs/META_PARENT_SERVICES.md'):sources[s]=sha(ROOT/s)
 result=dict(passed=True,terminal_services_linked=True,terminal_editor_integrated=False,installed_changed=False,physical_runtime_verified=False,parent_sha256=pm['binary_sha256'],parent_overlay_sha256=pm['line_port_overlay']['sha256'],disabled_parent_unchanged_sha256=dm['binary_sha256'],bank_binaries=bank['binaries'],memory_assertions_each=35332,kernel_assertions_each=166,workflow_assertions_each=3069,fatal_assertions=981,product_payload_bytes=21619,state_bytes=12870,new_TEXT_bytes=44,new_CONFIG_bytes=20,linked_CONFIG_bytes_with_alignment=32,minimum_retained_bytes=live['minimum_allocated_module_bytes'],retained_increase_bytes=64,resident_TEXT_spare_bytes=512,CONFIG_spare_bytes=2305,DGROUP_spare_bytes=16,capacities_unchanged={n:live[n]for n in capacity_names},isolated_bank_source_files=56,isolated_parent_source_files=707,parent_DOS_cases=[r['case']for r in parent_proof['runs']],invalid_callback_variants_rejected=30,original_inputs=[],sources=sources,receipts=receipts,limitations=['Production adapters linked in full parent; editor bank still lacks matched loader, exclusive arena lifetime, Alt-M/menu/admission/live action adoption.','Synthetic peer and source-only DOS checks; no connected modern BBS or physical acceptance of this new parent. Installed RCE81708 unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS Meta services receipt:full parent links;56/707-source rebuilds;four DOS cases;disabled parent exact;installed unchanged')
if __name__=='__main__':main()
