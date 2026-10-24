#!/usr/bin/env python3
"""Seal wide UI frames, live-only pane admission and DOS parser/menu workflows."""
import argparse,hashlib,json
from pathlib import Path
from prove_wide_viewer_source import ROOT,BASE,FULL

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 directory=a.proof.resolve();assert directory.is_relative_to(ROOT/'build')
 proof=load(directory/'result.json');assert proof['passed']and proof['nested_compiler_verified']and not proof['original_inputs']
 sources=proof['sources'];custody={};models={};dos={};nested={};banks={};compiler={};edits={};ordinary=None;fields={};legacy={};relocation=None;reset_fields={};shared={};viewers={};wide_dos={}
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
  elif name.endswith('wide-viewer-checks.json'):
   assert(report['open_close_cases'],report['live_stream_cases'],report['overlay_copy_and_width_refusals'],report['typed_overlay_copy_refusals'],report['deferred_menu_cases'],report['invalid_lifecycle_refusals'])==(144,396,288,6,16,5)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_wide_redisplay_live.py')
   viewers[name]={key:report[key]for key in ['binary_sha256','open_close_cases','live_stream_cases','overlay_copy_and_width_refusals','typed_overlay_copy_refusals','deferred_menu_cases','invalid_lifecycle_refusals','checker_sha256','scope']}
  elif name.startswith('build/WIDE-DOS-'):
   assert all(report['checks'].values())and report['state'][1:5]==[1,0,1,0]
   assert report['content_rows']==(25 if report['hidden_status']else 24)
   assert report['binary_sha256']==proof['products'][FULL if name.split('/')[1].endswith('special')else BASE]
   assert report['checker_sha256']==sha(ROOT/'standalone/test_wide_viewer_dos.py')
   assert report['observer_sha256']==sha(ROOT/'standalone/wide_viewer_watch.asm')
   wide_dos[name]={key:report[key]for key in ['checks','state','frame_count','viewer_ticks','binary_sha256','hidden_status','content_rows','checker_sha256','observer_sha256','scope']}
  elif name.endswith('shared-screen-checks.json'):
   assert(report['owner_refusals'],report['restore_cycles'],report['reclaimed_bytes'])==(4,3,4000)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_shared_screen_live.py')
   shared[name]=report
  elif name.endswith('reset-field-checks.json'):
   assert(report['cases'],report['native_repaint_cases'],report['post_width_field_edits'],report['private_repair_IRQ_cases'],report['native_fault_rollbacks'])==(420,240,240,2,8)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_reset_fields_live.py')
   reset_fields[name]={key:report[key]for key in ['binary_sha256','cases','native_repaint_cases','post_width_field_edits','private_repair_IRQ_cases','native_fault_rollbacks']}
  elif name.endswith('width-edit-checks.json'):
   assert(report['cases'],report['character_cases'],report['narrow_return_cases'],report['character_refusals'],report['foreign_DS_UART_cases'])==(160,528,2,12,4)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_width_edit_live.py')
   edits[name]={key:report[key]for key in ['binary_sha256','cases','character_cases','narrow_return_cases','character_refusals','foreign_DS_UART_cases']}
  elif name.endswith('character-edit-live-checks.json'):
   assert len(report['cases'])==10 and all(case['passed']for case in report['cases']);ordinary=report
  elif name.endswith('reset-live-checks.json'):
   assert(report['successes'],report['general_row_commits'],report['native_fault_rollbacks'],report['refusals'])==(25,112,20,63)
   layout=report['memory_layout']
   assert layout['viewer_live_plane_admission_verified']
   assert layout['native_reset_transaction_bridge_verified']and layout['native_reset_backup_bytes']==4000
   assert layout['program_browser_screen_overlay']and layout['far_ui_storage_bytes']==16000
   assert layout['native_reset_projection_fields_verified']==35 and layout['native_reset_field_repair_verified']
   assert(layout['native_reset_image_offset'],layout['native_reset_private_stack_bytes'],layout['native_reset_shadow_bytes'])==(0,4096,6600)
   assert layout['native_reset_workspace_end']-layout['native_reset_shadow_end']==24
   assert report['peer_width_still_unbound']and report['real_UART_ISR_in_private_context']and report['RIS_baseline_preserved']
   assert report['checker_sha256']==sha(ROOT/'standalone/check_reset_live.py')
   models[name]={key:report[key]for key in ['binary_sha256','successes','general_row_commits','native_fault_rollbacks','refusals','memory_layout']}
  elif name.endswith('native-bank-parent-checks.json'):
   assert len(report['malformed_layout_refusals'])==4
   banks[name]={key:report[key]for key in ['binary_sha256','malformed_layout_refusals','actual_PROGRAM_retention_verified','workspace_owner_refusals']}
  elif '/DOS-'in name:
   assert all(report['checks'].values())and report['transaction_status']==0 and report['character_edits_fixture']and report['field_edits_fixture']and report['scroll_fields_fixture']and report['active_width_fields_fixture']
   assert report['content_rows']==(25 if report['hidden_status_fixture']else 24)
   assert report['binary_sha256']==proof['products'][FULL if name.split('/')[1].endswith('special')else BASE]
   assert report['checker_sha256']==sha(ROOT/'standalone/test_reset_live_dos.py')
   dos[name]={key:report[key]for key in ['binary_sha256','content_rows','hidden_status_fixture','checks']}
  elif '/nested/'in name:
   assert all(report['checks'].values())
   assert report['products']['TERMINAL.EXE']==proof['products'][FULL]
   assert report['products']['ASPECT.EXE']==proof['child_products']['aspect-register-parent-custom-irq']
   assert report['products']['ASPCOMP.EXE']==proof['child_products']['aspect-compiler-dos']
   if report['case']in('explicit','chooser-explicit'):assert report['log_collisions']==32
   if report['case']=='rejected':
    screen=directory/'source/build/connection-dos'/report['connection']['case']/'SCREEN.BIN'
    bind(screen);raw=screen.read_bytes();assert len(raw)==4000
    text=b'\n'.join(raw[row*160:(row+1)*160:2]for row in range(25))
    assert b'compile error 2 (lexer0 output0)'in text and b'out of memory'not in text
   nested[report['case']]={key:report[key]for key in ['products','checks','port','log_collisions']}
  elif name.endswith('redisplay-checks.json'):
   assert report['inputs']==39 and len(report['cases'])==7 and all(case['passed']for case in report['cases']);legacy['viewer']=report
  elif name.endswith('command-menu-checks.json'):
   assert report['inputs']==153 and len(report['cases'])==5 and all(case['passed']for case in report['cases']);legacy['menu']=report
  elif name.endswith('menu-pending-checks.json'):
   assert report['inputs']==36 and len(report['cases'])==7 and all(case['passed']for case in report['cases']);legacy['pending']=report
  elif name.endswith('viewport-live-checks.json'):
   assert(report['cursor_transitions'],report['parser_output_erase_cases'],report['pre_copy_rejections'])==(80,60,186);legacy['viewport']=report
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
 assert len(wide_dos)==4 and len(viewers)==2 and len(shared)==2 and len(reset_fields)==2 and len(edits)==2 and len(fields)==2 and ordinary is not None and set(legacy)=={'repair','lines','policy','viewer','menu','pending','viewport'}and relocation is not None
 optimized=directory/'source/build/aspect-compiler-dos/ASPCOMP.EXE'
 assert optimized.stat().st_size==50582
 assert load(optimized.parent/'manifest.json')['optimization']=='size (-os)'
 bind(optimized)
 prior_path=ROOT/'docs/validation/wide-character-edit.json';prior=load(prior_path);bind(prior_path)
 assert prior['child_products']==proof['child_products']
 for name,digest in load(optimized.parent/'manifest.json')['sources'].items():assert prior['sources'][name]==digest,name
 compiler=dict(inherited_receipt=str(prior_path.relative_to(ROOT)),receipt_sha256=sha(prior_path),unchanged_compiler_sha256=sha(optimized),corpus=prior['compiler_memory']['corpus'],stack=prior['compiler_memory']['stack'])
 assert len(models)==2 and len(dos)==4 and len(banks)==3 and set(nested)=={'explicit','fallback','chain','rejected','chooser-explicit'}
 result=dict(status='wide serviced menu/history/clipboard with live-only pane admission checkpoint verified',accepted_for_deployment=False,source_files=len(sources),sources=sources,
  source_only_products=proof['products'],child_products=proof['child_products'],models=models,DOS_commits=dos,bank_ownership=banks,nested_compiler=nested,compiler_memory=compiler,wide_edits=edits,scroll_fields=fields,active_width_fields=reset_fields,shared_screen=shared,wide_viewers=viewers,DOS_wide_viewers=wide_dos,legacy_fields=legacy,CSI_relocation=relocation,ordinary_character_edits=ordinary,optimized_compiler_file_bytes=50582,
  artifacts=custody,recorder_sha256=sha(Path(__file__)),original_inputs=[],limitations=[
   'Explicit profile4/6 transaction with boolean wrapped/checking/protection modes; peer width requests remain unbound.',
   'Valid row counts1..25 and margins admitted; width resets margins to full content and clamps saved coordinates.',
   'Visible legacy startup25 adopts24 content rows; hidden status allows25. Actual DOS checks cover both startup cases on both parents.',
   'Rollback faults and private-stack UART interrupt timing use the hardware model.',
   'Nested compilation uses ordinary display, not an active132-column application/script renderer.',
   'History/menu/clipboard retain physical80-column local layouts; other UI/keyboard/child composition, unsupported field modes, partial-width scrolling and width-changing BBS sessions remain open.',
   'No physical modem verification or card deployment.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('RECORDED wide serviced UI checkpoint: two models, eight DOS workflows, ownership and five nested compiler cases')
if __name__=='__main__':main()
