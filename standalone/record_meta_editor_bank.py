#!/usr/bin/env python3
"""Bind separate-CS Meta bank checks, exact source export and default regression."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('direct','fault','proof','baseline','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={};gates={}
 for n in ('direct','fault','proof','baseline'):
  path=getattr(a,n).resolve();assert path.is_relative_to(ROOT/'build');v=json.loads((path/'result.json').read_text());assert v['passed'];receipts[str((path/'result.json').relative_to(ROOT))]=sha(path/'result.json');gates[n]=v
  for s,h in v['sources'].items():assert sha(ROOT/s)==h and (s not in sources or sources[s]==h);sources[s]=h
 direct,fault,proof,baseline=(gates[n] for n in ('direct','fault','proof','baseline'))
 for name,v in (('direct',direct),('fault',fault)):
  assert v['direct_kernel']==(name=='direct') and v['cpu']=='8086' and v['original_inputs']==[]
  assert v['binary_sha256']==proof['binaries'][name]==sha(getattr(a,name).resolve()/'METAEDIT.EXE')
  assert proof['logs'][name]==v['logs'] and 'PASS bank kernel 166 checks;' in v['logs']['NORMAL.LOG'] and 'PASS 3069 checks;state 12870;' in v['logs']['NORMAL.LOG']
  assert v['calculated_product_payload_bytes']==21475 and v['editor_owned_DGROUP_bytes']==0 and len(v['call_audit']['cross_CS_challenges_rejected'])==4
 assert 'PASS fatal 981 checks;' in fault['logs']['FATAL.LOG'] and 'FATAL.LOG' not in direct['logs']
 assert direct['bank_bytes']==23043 and fault['bank_bytes']==23795 and proof['source_count']==52 and proof['ancestor_git_unavailable']
 prior=json.loads((ROOT/'docs/validation/meta-editor-flow.json').read_text());assert baseline['binary_sha256']==prior['binary_sha256']==sha(a.baseline.resolve()/'METAEDIT.EXE')
 for s in ('standalone/record_meta_editor_bank.py','standalone/prove_meta_editor_bank_source.py','docs/META_EDITOR_BANK.md'):sources[s]=sha(ROOT/s)
 result=dict(passed=True,component_only=True,terminal_changed=False,installed_changed=False,physical_runtime_verified=False,direct_sha256=direct['binary_sha256'],fault_sha256=fault['binary_sha256'],default_controller_unchanged_sha256=baseline['binary_sha256'],kernel_assertions_each=166,workflow_assertions_each=3069,fatal_assertions=981,far_state_bytes=12870,calculated_product_payload_bytes=21475,editor_DGROUP_bytes=0,direct_diagnostic_bank_bytes=23043,fault_diagnostic_bank_bytes=23795,isolated_source_files=52,original_inputs=[],sources=sources,receipts=receipts,limitations=['Diagnostic resident service placement/conventions; production bindings and matched transient loader are not implemented.','No parent menu/Alt-M, atomic adoption, global admission, arena lifetime or parent capacity proof. HELD owners require bank code/state until DOS exit.','No actual VGA/connected UART/BBS/hardware acceptance for these binaries. Installed RCE81708 unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS Meta bank receipt:two DOS EXEs;166/3069/981 checks;52-source exact rebuild;default EXE unchanged')
if __name__=='__main__':main()
