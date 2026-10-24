#!/usr/bin/env python3
"""Seal generalized explicit width transactions and ordinary-display child admission."""
import argparse,hashlib,json
from pathlib import Path
from prove_reset_live_source import ROOT,BASE,FULL

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 directory=a.proof.resolve();assert directory.is_relative_to(ROOT/'build')
 proof=load(directory/'result.json');assert proof['passed']and proof['nested_compiler_verified']and not proof['original_inputs']
 sources=proof['sources'];custody={};models={};dos={};nested={};banks={};compiler={}
 def bind(path,digest=None):
  path=path.resolve();assert path.is_relative_to(ROOT)
  actual=sha(path);assert digest is None or actual==digest,path
  custody[str(path.relative_to(ROOT))]=actual
 for name,digest in sources.items():assert sha(ROOT/name)==sha(directory/'source'/name)==digest,name
 bind(directory/'result.json')
 for label,digest in proof['logs'].items():bind(directory/(label+'.log'),digest)
 for name,digest in proof['reports'].items():
  path=directory/'source'/name;bind(path,digest);report=load(path);assert report['passed']
  for source,expected in report.get('sources',{}).items():assert sources[source]==expected,source
  if name.endswith('reset-live-checks.json'):
   assert(report['successes'],report['general_row_commits'],report['native_fault_rollbacks'],report['refusals'])==(25,112,20,62)
   layout=report['memory_layout']
   assert layout['native_reset_transaction_bridge_verified']and layout['native_reset_backup_bytes']==4000
   assert layout['native_reset_projection_fields_verified']==34
   assert(layout['native_reset_image_offset'],layout['native_reset_private_stack_bytes'],layout['native_reset_shadow_bytes'])==(0,4096,6600)
   assert layout['native_reset_workspace_end']-layout['native_reset_shadow_end']==24
   assert report['peer_width_still_unbound']and report['real_UART_ISR_in_private_context']and report['RIS_baseline_preserved']
   assert report['checker_sha256']==sha(ROOT/'standalone/check_reset_live.py')
   models[name]={key:report[key]for key in ['binary_sha256','successes','general_row_commits','native_fault_rollbacks','refusals','memory_layout']}
  elif name.endswith('native-bank-parent-checks.json'):
   assert len(report['malformed_layout_refusals'])==4
   banks[name]={key:report[key]for key in ['binary_sha256','malformed_layout_refusals','actual_PROGRAM_retention_verified','workspace_owner_refusals']}
  elif '/DOS-'in name:
   assert all(report['checks'].values())and report['transaction_status']==0
   assert report['content_rows']==(25 if report['hidden_status_fixture']else 24)
   assert report['checker_sha256']==sha(ROOT/'standalone/test_reset_live_dos.py')
   dos[name]={key:report[key]for key in ['binary_sha256','content_rows','hidden_status_fixture','checks']}
  elif '/nested/'in name:
   assert all(report['checks'].values())
   assert report['products']['TERMINAL.EXE']==proof['products'][FULL]
   assert report['products']['ASPECT.EXE']==proof['child_products']['aspect-register-parent-custom-irq']
   assert report['products']['ASPCOMP.EXE']==proof['child_products']['aspect-compiler-dos']
   if report['case']=='explicit':assert report['log_collisions']==32
   nested[report['case']]={key:report[key]for key in ['products','checks','port','log_collisions']}
  elif 'allocator/'in name:
   assert all('failures0'in value for value in report['summaries'].values())
   compiler['allocator']=report['summaries']
  elif name.endswith('/stack-checks.json'):
   assert report['candidate_CLI_stack_bytes']==report['checked_CLI_stack_bytes']==24576
   assert report['checked_API_stack_bytes']==16384 and report['checked_CLI_cases']==18
   assert report['checked_fault_CLI_stack_bytes']==24576
   assert report['compiler_sha256']==proof['child_products']['aspect-compiler-dos']
   compiler['stack']={key:report[key]for key in ['checked_API_stack_bytes','checked_CLI_stack_bytes','checked_CLI_cases','depth_cases']}
  elif name=='build/compiler-stack/checks.json':
   assert(report['case_count'],report['accepted'],report['rejected'])==(2043,1077,966)
   assert report['binary_sha256']==proof['child_products']['aspect-compiler-dos']
   cases=load(path.parent/'cases.json');bind(path.parent/'cases.json',report['case_manifest_sha256'])
   for i,case in enumerate(cases):
    for leaf,key in [(f'P{i:05}.ASP','source_sha256'),(f'P{i:05}.ASX','asx_sha256')]:assert sha(path.parent/'tests'/leaf)==case[key]
   compiler['corpus']=dict(cases=2043,accepted=1077,rejected=966)
  elif 'compiler-workspace/'in name:
   assert report['borrowed_cycles']==400 and report['metadata_tail_bytes_tested']==[0,16,256,1024]and report['borrowed_metadata_logical_faults']
   assert report['summary'].endswith('FAILURES 0')
   compiler['workspace']=report['summary']
  else:raise AssertionError(name)
  for artifact,expected in report.get('artifacts',{}).items():bind(path.parent/artifact if 'allocator/'in name else directory/'source'/artifact,expected)
 assert set(compiler)=={'allocator','stack','corpus','workspace'}
 assert len(models)==2 and len(dos)==4 and len(banks)==3 and set(nested)=={'explicit','fallback','chain','rejected'}
 result=dict(status='general row and startup width checkpoint verified',accepted_for_deployment=False,source_files=len(sources),sources=sources,
  source_only_products=proof['products'],child_products=proof['child_products'],models=models,DOS_commits=dos,bank_ownership=banks,nested_compiler=nested,compiler_memory=compiler,
  artifacts=custody,recorder_sha256=sha(Path(__file__)),original_inputs=[],limitations=[
   'Explicit plain-profile4/6 transaction only; normal peer width requests remain unbound.',
   'Valid row counts1..25 and margins admitted; width resets margins to full content and clamps saved coordinates.',
   'Visible legacy startup25 adopts24 content rows; hidden status allows25. Actual DOS checks cover both startup cases on both parents.',
   'Rollback faults and private-stack UART interrupt timing use the hardware model.',
   'Nested compilation uses ordinary display, not an active132-column application/script renderer.',
   'Protected fields, broader UI/scroll/child composition and width-changing BBS sessions remain open.',
   'No physical modem verification or card deployment.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('RECORDED row/startup width checkpoint: two models, four DOS commits, ownership and four nested compiler cases')
if __name__=='__main__':main()
