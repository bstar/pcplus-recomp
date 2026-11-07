#!/usr/bin/env python3
"""Bind serviced Alt-M parent, live UART cases and isolated public-source proof."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('parent','disabled','source-proof','cases-prefix','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--cases-suffix',required=True)
 a=p.parse_args();sources={};receipts={}
 def read(path):
  v=json.loads(path.read_text());receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in v.get('sources',{}).items():assert sha(ROOT/n)==h and(n not in sources or sources[n]==h);sources[n]=h
  return v
 parent=read(a.parent.resolve()/'manifest.json');disabled=read(a.disabled.resolve()/'manifest.json');proof=read(a.source_proof.resolve()/'result.json')
 assert parent['experimental_meta_editor'] and parent['memory_layout']['meta_editor_UI_bound'] and proof['passed'] and proof['ancestor_git_unavailable']
 assert proof['binary_sha256']==parent['binary_sha256']==sha(a.parent.resolve()/'TERMINAL.EXE')
 assert disabled['binary_sha256']==sha(a.disabled.resolve()/'TERMINAL.EXE')=='ff6bb369a8b3693cefc357fec901ae576139cafe8915f8e60818ddcdde2e5399'
 for key,n,pk in (('meta_editor_overlay','PCMETA.OVL','meta_overlay_sha256'),('line_port_overlay','PCLINE.OVL','overlay_sha256')):assert parent[key]['sha256']==sha(a.parent.resolve()/n)==proof[pk]
 runs=[]
 for case in ('edit','save','reference','browser','load','reload','cancel','missing'):
  path=Path(str(a.cases_prefix.resolve())+case+a.cases_suffix)/'result.json'
  v=read(path);assert v['passed']and v['case']==case and v['binary_sha256']==parent['binary_sha256']and all(v['checks'].values());runs.append(dict(case=case,checks=v['checks']))
 assert {v['case']for v in proof['runs']}=={'save','serviced','readonly','portbusy'}
 assert {v['case']for v in proof['meta_runs']}=={'save','cancel','missing'}
 now,old=parent['memory_layout'],disabled['memory_layout']
 caps=('near_bytes','far_bytes','history_bytes','snapshot_bytes','redisplay_snapshot_bytes','native_reset_private_stack_bytes','native_reset_shadow_bytes','native_reset_workspace_bytes','far_ui_storage_bytes')
 assert all(now[n]==old[n]for n in caps)and now['meta_overlay_DGROUP_bytes']==0
 for n in ('standalone/record_meta_front.py','docs/META_FRONTEND.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,normal_AltM_UI_bound=True,live_action_adoption=True,installed_changed=False,physical_runtime_verified=False,parent_sha256=parent['binary_sha256'],meta_sha256=parent['meta_editor_overlay']['sha256'],line_sha256=parent['line_port_overlay']['sha256'],disabled_sha256=disabled['binary_sha256'],runs=runs,source_count=proof['source_count'],isolated_Meta_cases=[r['case']for r in proof['meta_runs']],isolated_LinePort_cases=[r['case']for r in proof['runs']],minimum_retained_bytes=now['minimum_allocated_module_bytes'],baseline_retained_bytes=old['minimum_allocated_module_bytes'],resident_code_bytes=now['resident_code_bytes'],bank_code_bytes=parent['meta_editor_overlay']['bank_bytes'],bank_fixups=parent['meta_editor_overlay']['relocations'],capacities_unchanged={n:now[n]for n in caps},sources=sources,receipts=receipts,original_inputs=[],limitations=['DOS8086 synthetic UART and passive VGA evidence, no physical Enigma/Boca acceptance or original pixel equality.','Frozen-history entry, other geometries and directory-resource-cache adoption remain open.','Checked Bind/Load/Save are synchronous foreground operations; no per-DOS-call latency guarantee.','Existing component close-fault coverage; no physical file fault injection or deployment in this milestone.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS Alt-M frontend receipt:',proof['source_count'],'sources; eight live cases; isolated three Meta/four Line-Port cases')
if __name__=='__main__':main()
