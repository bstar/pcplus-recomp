#!/usr/bin/env python3
"""Seal recovered SUB behavior, peer refusals and real DOS CSI interruption."""
import argparse,hashlib,json
from pathlib import Path
from prove_substitute_source import ROOT,BASE,FULL

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 directory=a.proof.resolve();assert directory.is_relative_to(ROOT/'build')
 proof=load(directory/'result.json');assert proof['passed']and proof['nested_compiler_verified']and not proof['original_inputs']
 sources=proof['sources'];custody={};models={};dos={};nested={};banks={};compiler={};edits={};ordinary=None;fields={};legacy={};relocation=None;reset_fields={};shared={};viewers={};wide_dos={};aspect_dos={};aspect_owners={};render_policy=None;protected_dos={};protected_models={};clear_models={};alternate_dos={};alternate_models={};peer_models={};peer_dos={};substitute_models={};failure_dos={}
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
  if name.startswith('build/FAIL-DOS-'):
   assert all(report['checks'].values())and report['binary_sha256']==proof['products'][FULL]
   assert report['runner_sha256']==proof['child_products']['aspect-register-parent-custom-irq']
   for source,digest in report['test_sources'].items():assert sources[source]==digest,source
   refused=report['case']in('native','preflight');fatal=report['ordinary']and refused
   assert report['state'][:5]==[0x5756,1,0,1,2 if fatal else 0]
   assert report['final_state']==([0x2a6e,80,1,0,0,0,0]if fatal else[0,132,0,0,0,0,0])
   if report['ordinary']:
    assert report['compiler_observation']==[0]*6 and report['child_state']==[65535]*10
    assert report['attached_ticks']==report['bridge_ticks']==report['overlay_ticks']==0
   else:
    assert report['attached_ticks']>0 and(report['overlay_ticks']>0)==report['window']
    assert report['child_state'][0]==(3 if refused else 0)and report['child_state'][4:9]==[0]*5
    assert report['child_state'][9]==(0x2a6e if report['case']=='native'else 0)
    if refused:assert report['child_state'][1:4]==[80,25,2000]
   if report['source_compilation']:assert report['compiler_sha256']==proof['child_products']['aspect-compiler-dos']and report['checks']['exact_DOS_ASX']
   failure_dos[name]=report
  elif name.startswith(('build/ASPECT-DOS-','build/PROTECTED-DOS-','build/ALT-DOS-','build/PEER-DOS-')):
   assert all(report['checks'].values())and report['state'][1:5]==[1,0,1,0]
   assert report['binary_sha256']==proof['products'][FULL]
   assert report['runner_sha256']==proof['child_products']['aspect-register-parent-custom-irq']
   assert report['checker_sha256']==sha(ROOT/'standalone/test_aspect_wide_dos.py')
   assert report['observer_sha256']==sha(ROOT/'standalone/aspect_wide_watch.asm')
   assert report['content_rows']==(25 if report['hidden_status']else 24)
   if report['ordinary']:
    assert report['peer_width']and not report['window']and not report['source_compilation']
    assert report['attached_ticks']==report['bridge_ticks']==report['overlay_ticks']==0
    assert report['compiler_observation']==[0]*6 and report['checks']['ordinary_receive_owner']
   else:assert report['attached_ticks']>0
   assert report['checks']['compiler_exit_observed']
   assert (report['overlay_ticks']>0)==report['window']
   if report['source_compilation']:
    assert report['compiler_sha256']==proof['child_products']['aspect-compiler-dos']
    assert report['checks']['exact_DOS_compiled_ASX']and not report['full_plane_snapshot']
    assert not any(k in report['checks']for k in ['exact_logical_screen','exact_flags','exact_values'])
   else:
    assert report['full_plane_snapshot']and all(report['checks'][k]for k in ['exact_logical_screen','exact_flags','exact_values'])
   target=peer_dos if name.startswith('build/PEER-DOS-')else alternate_dos if name.startswith('build/ALT-DOS-')else protected_dos if name.startswith('build/PROTECTED-DOS-')else aspect_dos
   assert report['unimplemented_service']==0
   if target is peer_dos:assert report['peer_width']and report['checks']['peer_narrow_CPR']
   else:assert not report['peer_width']and not report['ordinary']and report['profile']==6
   if target is alternate_dos:assert report['alternate_output']and report['checks']['alternate_glyph_query']
   if target is protected_dos:assert report['protected_erase']and report['erase_case']=='all'and report['checks']['immediate_banner_parsed']
   target[name]={k:report[k]for k in ['profile','peer_width','ordinary','compiler_observation','alternate_output','output_map','output_mask','protected_erase','erase_case','field_color','unimplemented_service','checks','state','attached_ticks','bridge_ticks','overlay_ticks','binary_sha256','runner_sha256','compiler_sha256','source_compilation','full_plane_snapshot','window','hidden_status','content_rows','checker_sha256','observer_sha256','scope']}
  elif name.endswith('substitute-checks.json'):
   assert(report['cases'],report['signed_profile_cases'],report['foreground_UART_IRQ_cases'])==(768,5,4)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_substitute_live.py')
   assert report['dispatcher_cases']==4
   substitute_models[name]=report
  elif name.endswith('peer-width-checks.json'):
   assert(report['parser_commits'],report['ownership_cases'],report['admitted_states'],report['additional_refusals'],report['private_stack_IRQ_cases'],report['ASPECT_rollbacks'])==(64,768,1,8,4,2)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_peer_width_live.py')
   peer_models[name]=report
  elif name.endswith('alternate-output-checks.json'):
   assert(report['cell_cases'],report['renderer_streams'],report['foreign_DS_IRQ_cases'],report['pre_mutation_refusals'],report['RIS_cases'],report['active_width_commits'])==(12288,96,6,9,3,12)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_alternate_output_live.py')
   alternate_models[name]=report
  elif name.endswith('protected-erase-checks.json'):
   assert(report['cases'],report['parser_cases'],report['pre_mutation_rejections'],report['real_UART_IRQ_cases'])==(288,72,8,4)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_protected_erase_live.py')
   protected_models[name]=report
  elif name.endswith('wide-clear-checks.json'):
   assert(report['cases'],report['pre_mutation_rejections'])==(896,5)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_wide_clear_live.py')
   clear_models[name]=report
  elif name.endswith('aspect-viewport-ownership-checks.json'):
   assert(report['cases'],report['accepted'])==(768,1)
   assert report['checker_sha256']==sha(ROOT/'standalone/check_aspect_viewport_ownership.py')
   aspect_owners[name]=report
  elif name=='build/aspect-renderer-policy/checks.json':
   assert report['DOS_summary']=='checks=58978 failures=0'
   assert report['cpu']['count']==56 and report['cpu']['no_nonstack_writes']
   assert report['checker_sha256']==sha(ROOT/'standalone/check_aspect_renderer_policy.py')
   render_policy=report
  elif name.endswith('scroll-field-checks.json'):
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
   assert(report['owner_refusals'],report['restore_cycles'],report['reclaimed_bytes'])==(12,3,8000)
   assert(report['editor_restore_cycles'],report['viewer_restore_cycles'])==(2,1)
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
   assert(layout['substitute_native_bytes_verified'],layout['substitute_native_dependencies_verified'],layout['substitute_state_words_verified'])==(53,4,4)
   assert layout['peer_width_mode_bridge_verified']
   assert layout['native_reset_transaction_bridge_verified']and layout['native_reset_backup_bytes']==4000
   assert layout['program_browser_screen_overlay']and layout['far_ui_storage_bytes']==12000 and layout['editor_viewer_screen_overlay']
   assert layout['native_reset_projection_fields_verified']==37
   assert layout['aspect_command_preflight_verified']and layout['aspect_viewport_lease_words_verified']==3
   assert layout['protected_erase_far_bridge_verified']and layout['protected_erase_native_dependencies_verified']==4
   assert layout['wide_clear_rectangle_route_verified']and layout['erase_after_projection_initially_idle']
   assert layout['alternate_output_far_bridge_verified']and layout['alternate_output_native_dependencies_verified']==4 and layout['source_owned_output_table_bytes']==256 and layout['native_reset_field_repair_verified']
   assert(layout['native_reset_image_offset'],layout['native_reset_private_stack_bytes'],layout['native_reset_shadow_bytes'])==(0,4096,6600)
   assert layout['native_reset_workspace_end']-layout['native_reset_shadow_end']==24
   assert not report['peer_width_still_unbound']and report['peer_width_parser_roundtrip']and report['real_UART_ISR_in_private_context']and report['RIS_baseline_preserved']
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
 assert len(aspect_dos)==8 and len(aspect_owners)==2 and render_policy is not None
 assert sum(r['source_compilation']for r in aspect_dos.values())==4
 assert len(protected_dos)==16 and len(protected_models)==2 and len(clear_models)==2
 assert sum(r['field_color']for r in protected_dos.values())==8
 assert {(r['hidden_status'],r['window'],r['source_compilation'],r['field_color'])for r in protected_dos.values()}=={(h,w,s,c)for h in (False,True)for w in (False,True)for s in (False,True)for c in (False,True)}
 assert len(alternate_dos)==18 and len(alternate_models)==2
 primary=[r for r in alternate_dos.values()if r['output_mask']==255]
 assert {(r['hidden_status'],r['window'],r['source_compilation'],r['output_map'])for r in primary}=={(h,w,s,m)for h in (False,True)for w in (False,True)for s in (False,True)for m in (False,True)}
 assert sum(r['output_mask']==127 for r in alternate_dos.values())==2
 assert len(peer_models)==2 and len(peer_dos)==46
 primary=[r for r in peer_dos.values()if r['output_mask']==255]
 children=[r for r in primary if not r['ordinary']];ordinary_peers=[r for r in primary if r['ordinary']]
 assert len(children)==32 and len(ordinary_peers)==8
 assert {(r['profile'],r['hidden_status'],r['window'],r['source_compilation'],r['alternate_output'])for r in children}=={(p,h,w,s,m)for p in (4,6)for h in (False,True)for w in (False,True)for s in (False,True)for m in (False,True)}
 assert {(r['profile'],r['hidden_status'],r['alternate_output'])for r in ordinary_peers}=={(p,h,m)for p in (4,6)for h in (False,True)for m in (False,True)}
 masks=[r for r in peer_dos.values()if r['output_mask']==127]
 assert len(masks)==6 and all(r['alternate_output']and r['output_map']and r['hidden_status']for r in masks)
 assert {(r['profile'],r['ordinary'],r['source_compilation'])for r in masks}=={(p,o,s)for p in (4,6)for o,s in ((True,False),(False,False),(False,True))}
 assert len(substitute_models)==2 and len(failure_dos)==76
 wanted={(p,h,c,False,w,s)for p in(4,6)for h in(False,True)for c in('native','preflight','can','sub')for w in(False,True)for s in(False,True)}
 wanted|={(p,h,c,True,False,False)for p in(4,6)for h in(False,True)for c in('native','can','sub')}
 assert {(r['profile'],r['hidden_status'],r['case'],r['ordinary'],r['window'],r['source_compilation'])for r in failure_dos.values()}==wanted
 result=dict(status='recovered SUB and DOS peer refusal/interruption checkpoint verified',accepted_for_deployment=False,source_files=len(sources),sources=sources,
  substitute_models=substitute_models,DOS_peer_failure=failure_dos,peer_width_models=peer_models,DOS_peer_width=peer_dos,source_only_products=proof['products'],child_products=proof['child_products'],models=models,alternate_models=alternate_models,DOS_alternate_output=alternate_dos,protected_models=protected_models,wide_clear_models=clear_models,DOS_protected_erase=protected_dos,DOS_ASPECT=aspect_dos,ASPECT_ownership=aspect_owners,ASPECT_policy=render_policy,DOS_commits=dos,bank_ownership=banks,nested_compiler=nested,compiler_memory=compiler,wide_edits=edits,scroll_fields=fields,active_width_fields=reset_fields,shared_screen=shared,wide_viewers=viewers,DOS_wide_viewers=wide_dos,legacy_fields=legacy,CSI_relocation=relocation,ordinary_character_edits=ordinary,optimized_compiler_file_bytes=50582,
  artifacts=custody,recorder_sha256=sha(Path(__file__)),original_inputs=[],limitations=[
   'Peer mode3 width requests are bound in the experimental transaction parent only, with supported profile4/6 and boolean wrapped/checking/protection modes.',
   'Valid row counts1..25 and margins admitted; width resets margins to full content and clamps saved coordinates.',
   'Visible legacy startup25 adopts24 content rows; hidden status allows25. Actual DOS checks cover both startup cases on both parents.',
   'Rollback faults and private-stack UART interrupt timing use the hardware model.',
   'Five ordinary-display nested compiler cases plus four wide source cases; the latter use a compact observer, while four precompiled cases capture complete planes.',
   'Physical80-column display and local UI remain; logical132 columns use overlapping panes. Broader UI/keyboard/child composition, unsupported modes, partial-width scrolling and active-ASPECT/BBS width sessions remain open.',
   'SUB profile>=20 still calls an unresolved overlay provider; the admitted application profiles4/6 use the recovered return/clear/up/down behavior.',
   'DOS rejection cases use a declared startup cursor-backend refusal or mixed-list preflight. They do not force native-body/output faults. Interrupted input covers incoming CAN/SUB followed by ESC resynchronization, not independent CAN/SUB cancellation, arbitrary DOS/OS cancellation or carrier loss.',
   'The ordinary fatal refusal exits2 and restores sampled UART/interrupt hardware; a discarded parser-frame counter in the terminating process is not a live owner.',
   'No physical modem verification or card deployment.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('RECORDED SUB:53 exact native bytes,76 refusal/interruption DOS cases,177 total workflows')
if __name__=='__main__':main()
