#!/usr/bin/env python3
"""Seal bounded scroll metadata, native region repair and DOS consumer checks."""
import argparse,hashlib,json
from pathlib import Path
from prove_scroll_fields_source import ROOT,BASE,FULL

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 directory=a.proof.resolve();assert directory.is_relative_to(ROOT/'build')
 proof=load(directory/'result.json');assert proof['passed']and proof['nested_compiler_verified']and not proof['original_inputs']
 sources=proof['sources'];custody={};models={};dos={};nested={};banks={};compiler={};edits={};ordinary=None;fields={};legacy={};relocation=None
 def bind(path,digest=None):
  path=path.resolve();assert path.is_relative_to(ROOT)
  actual=sha(path);assert digest is None or actual==digest,path
  custody[str(path.relative_to(ROOT))]=actual
 for name,digest in sources.items():assert sha(ROOT/name)==sha(directory/'source'/name)==digest,name
 bind(directory/'result.json')
 for folder,digest in proof['products'].items():
  product=directory/'source/build'/folder/'TERMINAL.EXE'
  bind(product,digest);bind(product.parent/'manifest.json')
  assert load(product.parent/'manifest.json')['binary_sha256']==digest
 for folder,digest in proof['child_products'].items():
  product=directory/'source/build'/folder/('ASPCOMP.EXE'if folder=='aspect-compiler-dos'else'ASPECT.EXE')
  bind(product,digest);bind(product.parent/'manifest.json')
 for label,digest in proof['logs'].items():bind(directory/(label+'.log'),digest)
 for name,digest in proof['reports'].items():
  path=directory/'source'/name;bind(path,digest);report=load(path);assert report['passed']
  for source,expected in report.get('sources',{}).items():assert sources[source]==expected,source
  folder=Path(name).parts[1]
  if folder in proof['products']and'binary_sha256'in report:assert report['binary_sha256']==proof['products'][folder],name
  if name.endswith('scroll-field-checks.json'):
   assert(report['cases'],report['repairs'],report['counted_rectangles'],report['pre_mutation_rejections'],report['transient_descriptor_IRQ_cases'])==(1344,240,21,16,4)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_scroll_fields_live.py')
   fields[name]={key:report[key]for key in ['binary_sha256','cases','repairs','counted_rectangles','pre_mutation_rejections','transient_descriptor_IRQ_cases']}
  elif name.endswith('width-edit-checks.json'):
   assert(report['cases'],report['character_cases'],report['narrow_return_cases'],report['character_refusals'],report['foreign_DS_UART_cases'])==(160,528,2,12,4)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_width_edit_live.py')
   edits[name]={key:report[key]for key in ['binary_sha256','cases','character_cases','narrow_return_cases','character_refusals','foreign_DS_UART_cases']}
  elif name.endswith('character-edit-live-checks.json'):
   assert len(report['cases'])==10 and all(case['passed']for case in report['cases']);ordinary=report
  elif name.endswith('reset-live-checks.json'):
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
   assert all(report['checks'].values())and report['transaction_status']==0 and report['character_edits_fixture']and report['field_edits_fixture']and report['scroll_fields_fixture']
   assert report['content_rows']==(25 if report['hidden_status_fixture']else 24)
   assert report['binary_sha256']==proof['products'][FULL if name.split('/')[1].endswith('special')else BASE]
   assert report['checker_sha256']==sha(ROOT/'standalone/test_reset_live_dos.py')
   dos[name]={key:report[key]for key in ['binary_sha256','content_rows','hidden_status_fixture','checks']}
  elif '/nested/'in name:
   assert all(report['checks'].values())
   assert report['products']['TERMINAL.EXE']==proof['products'][FULL]
   assert report['products']['ASPECT.EXE']==proof['child_products']['aspect-register-parent-custom-irq']
   assert report['products']['ASPCOMP.EXE']==proof['child_products']['aspect-compiler-dos']
   if report['case']=='explicit':assert report['log_collisions']==32
   nested[report['case']]={key:report[key]for key in ['products','checks','port','log_collisions']}
  elif name=='build/csi-relocation/result.json':
   assert len(report['cases'])==3 and all(case['passed']for case in report['cases'])
   assert report['flat_sha256']=='3a1524f4c69e7e9da59fd67babc99c94dfdcff097c337dfd79f198705f4535b5'
   flat=path.parent/'dispatch.bin';assert flat.stat().st_size==2018;bind(flat,report['flat_sha256']);relocation=report
  elif name=='build/attribute-repair/live-checks.json':
   assert report['cases']==925 and report['consumer_cases']>0 and report['prewire_cases']>0 and report['geometry_errors']==17
   assert report['checker_sha256']==sha(ROOT/'standalone/check_attribute_repair_live.py');legacy['repair']=report
  elif name.endswith('line-attributes-live-checks.json'):
   assert report['cases']==516 and report['pre_mutation_rejections']==45 and report['repair_operations']==192
   assert report['checker_sha256']==sha(ROOT/'standalone/check_line_attributes_live.py')
   legacy['lines']=report
  elif name.endswith('line-edit-live-checks.json'):
   assert len(report['cases'])==8 and all(case['passed']for case in report['cases'])
   legacy['policy']=report
  else:raise AssertionError(name)
  for artifact,expected in report.get('artifacts',{}).items():bind(path.parent/artifact if 'allocator/'in name else directory/'source'/artifact,expected)
 assert len(edits)==2 and len(fields)==2 and ordinary is not None and set(legacy)=={'repair','lines','policy'}and relocation is not None
 optimized=directory/'source/build/aspect-compiler-dos/ASPCOMP.EXE'
 assert optimized.stat().st_size==50582
 assert load(optimized.parent/'manifest.json')['optimization']=='size (-os)'
 bind(optimized)
 prior_path=ROOT/'docs/validation/wide-character-edit.json';prior=load(prior_path);bind(prior_path)
 assert prior['child_products']==proof['child_products']
 for name,digest in load(optimized.parent/'manifest.json')['sources'].items():assert prior['sources'][name]==digest,name
 compiler=dict(inherited_receipt=str(prior_path.relative_to(ROOT)),receipt_sha256=sha(prior_path),unchanged_compiler_sha256=sha(optimized),corpus=prior['compiler_memory']['corpus'],stack=prior['compiler_memory']['stack'])
 assert len(models)==2 and len(dos)==4 and len(banks)==3 and set(nested)=={'explicit','fallback','chain','rejected'}
 result=dict(status='bounded full-width scroll metadata and native repair checkpoint verified',accepted_for_deployment=False,source_files=len(sources),sources=sources,
  source_only_products=proof['products'],child_products=proof['child_products'],models=models,DOS_commits=dos,bank_ownership=banks,nested_compiler=nested,compiler_memory=compiler,wide_edits=edits,scroll_fields=fields,legacy_fields=legacy,CSI_relocation=relocation,ordinary_character_edits=ordinary,optimized_compiler_file_bytes=50582,
  artifacts=custody,recorder_sha256=sha(Path(__file__)),original_inputs=[],limitations=[
   'Explicit plain-profile4/6 transaction only; normal peer width requests remain unbound.',
   'Valid row counts1..25 and margins admitted; width resets margins to full content and clamps saved coordinates.',
   'Visible legacy startup25 adopts24 content rows; hidden status allows25. Actual DOS checks cover both startup cases on both parents.',
   'Rollback faults and private-stack UART interrupt timing use the hardware model.',
   'Nested compilation uses ordinary display, not an active132-column application/script renderer.',
   'Partial-width wrapped scrolling, field-active width changes, broader UI/keyboard/child composition and width-changing BBS sessions remain open.',
   'No physical modem verification or card deployment.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('RECORDED bounded scroll checkpoint: two models, four DOS commits, ownership and four nested compiler cases')
if __name__=='__main__':main()
