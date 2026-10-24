#!/usr/bin/env python3
"""Seal the experimental display transaction, retaining the failed compiler gate."""
import argparse,hashlib,json
from pathlib import Path
from prove_reset_live_source import ROOT,BASE,FULL
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proof',type=Path,required=True)
 p.add_argument('--nested',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 proof_dir=a.proof.resolve();assert proof_dir.is_relative_to(ROOT/'build');proof=load(proof_dir/'result.json')
 assert proof['passed']and not proof['original_inputs'];sources=dict(proof['sources']);custody={};models={};dos={}
 def bind(path):
  path=path.resolve();assert path.is_relative_to(ROOT);custody[str(path.relative_to(ROOT))]=sha(path)
 def source_set(mapping):
  for name,digest in mapping.items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
 source_set(sources);bind(proof_dir/'result.json')
 for label,digest in proof['logs'].items():
  path=proof_dir/(label+'.log');assert sha(path)==digest;bind(path)
 for name,digest in proof['reports'].items():
  path=proof_dir/'source'/name;report=load(path);assert report['passed']and sha(path)==digest;bind(path)
  source_set(report['sources'])
  if name.endswith('reset-live-checks.json'):
   assert report['successes']==22 and report['native_fault_rollbacks']==5 and report['refusals']==58
   assert report['checker_sha256']==sha(ROOT/'standalone/check_reset_live.py')and report['peer_width_still_unbound']
   assert report['memory_layout']['native_reset_transaction_bridge_verified']and report['memory_layout']['native_reset_backup_bytes']==3840
   models[name]={key:report[key]for key in ['binary_sha256','successes','native_fault_rollbacks','refusals','real_UART_ISR_in_private_context','root_near_and_owned_shadow_preserved_on_failure','status_row_update_preserved','RIS_baseline_preserved','memory_layout']}
  elif '/DOS-'in name:
   assert all(report['checks'].values())and report['transaction_status']==0
   assert report['checker_sha256']==sha(ROOT/'standalone/test_reset_live_dos.py')
   assert report['observer_base_sha256']==sha(ROOT/'standalone/line_attributes_watch.asm')
   for artifact,expected in report['artifacts'].items():
    file=proof_dir/'source'/artifact;assert sha(file)==expected;bind(file)
   dos[name]=report['checks']
 assert len(models)==2 and len(dos)==2
 failed_path=a.nested.resolve()/'result.json';failed=load(failed_path);assert failed_path.is_relative_to(ROOT/'build')
 assert not failed['passed']and failed['products']['TERMINAL.EXE']==proof['products'][FULL]
 assert failed['products']['ASPECT.EXE']=='495d4852275bb7f14c897c8ea9fcaee4620c939690402898fd0c3c6e64723dd7'
 source_set(failed['sources']);bind(failed_path)
 for artifact,digest in failed['artifacts'].items():
  file=ROOT/artifact;assert sha(file)==digest;bind(file)
 checks=failed['checks'];assert not checks['expected_script_output']and not checks['exact_LOGON.ASX']
 assert all(checks[key]for key in ['connection_passed','post_child_parser','PRM_unchanged','hardware_restored','existing_logs_preserved','temporary_logs_retired'])
 screen=ROOT/'build/connection-dos'/failed['connection']['case']/'screen.txt'
 assert 'compile error 3 (lexer0 output0)'in screen.read_text()
 assert 'file or output error (error 5, opcode 00, step 0)'in screen.read_text()
 cold=load(ROOT/'build'/FULL.removesuffix('-transaction')/'manifest.json')
 current=load(ROOT/'build'/FULL/'manifest.json')
 assert current['binary_sha256']==proof['products'][FULL]
 delta=current['memory_layout']['minimum_allocated_module_bytes']-cold['memory_layout']['minimum_allocated_module_bytes'];assert delta==1504
 result=dict(status='display transaction checkpoint verified; nested compiler admission failed',accepted_for_deployment=False,
  source_files=len(sources),sources=sources,source_only_products=proof['products'],models=models,DOS_commits=dos,
  nested_compiler=dict(passed=False,products=failed['products'],checks=checks,
   failure='ASPCOMP starts but reports heap error3 at source line1; ASPECT propagates error5'),added_branded_module_bytes=delta,
  artifacts=custody,recorder_sha256=sha(Path(__file__)),original_inputs=[],limitations=[
   'Explicit plain24-row profiles4/6 API; normal peer width requests still trap.',
   'DOS witness normalizes rows and calls after a BIOS cursor operation; faults and private-stack ISR checks use a hardware model.',
   'Protected fields, other rows/margins, broader modal/script/scroll workflows and width-changing BBS acceptance remain open.',
   'New transaction parent fails nested compilation; prior cold-only parent with compact ASPECT passed.',
   'No physical modem/card deployment; staged package and card unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('RECORDED live display transaction: models/source/DOS commits verified; nested compiler FAIL; deployment refused')
if __name__=='__main__':main()
