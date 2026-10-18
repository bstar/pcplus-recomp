#!/usr/bin/env python3
"""Bind direct settings invocation and configuration segmentation to evidence."""
import hashlib,json,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def bound(path,runtime):
 result=read(path);assert result['passed'] and result['binary_sha256']==runtime,path
 for source,digest in result.get('sources',{}).items():assert sha(source)==digest,source
 return result
def main():
 runtime=sha('build/terminal/TERMINAL.EXE');editor=sha('build/setup/PRMEDIT.EXE')
 manifest=read('build/terminal/manifest.json');assert manifest['binary_sha256']==runtime
 for source,digest in manifest['sources'].items():assert sha(source)==digest,source
 linked=bound('build/terminal/setup-live-checks.json',runtime);assert linked['inputs']==32
 dos=read('build/setup-startup/live-checks.json')
 assert dos['passed'] and dos['terminal_sha256']==runtime and dos['editor_sha256']==editor
 assert len(dos['cases'])==10 and all(c['passed'] and all(c['checks'].values()) for c in dos['cases'])
 owner=bound('build/terminal/live-setup-owner-checks.json',runtime);assert owner['inputs']==76
 apply=bound('build/terminal/live-setup-apply-checks.json',runtime);assert apply['inputs']==27
 policy=bound('build/terminal/live-setup-policy-checks.json',runtime);assert policy['inputs']==27
 link=bound('build/terminal/live-setup-link-checks.json',runtime);assert link['inputs']==53
 profile=bound('build/terminal/live-setup-profile-checks.json',runtime);assert profile['inputs']==32
 port=bound('build/terminal/port-handoff-checks.json',runtime);assert port['inputs']==61
 frames=bound('build/terminal/config-far-checks.json',runtime)
 assert frames['configuration_bridge_pairs_verified']==22 and len(frames['rejected_mutations'])==103
 candidate=bound('build/live-configuration/terminal-checks.json',runtime)
 assert candidate['host']=='terminal-far-C' and candidate['inputs']==389 and candidate['maximum_CPU_call_stack_bytes']<8192-3514-16
 directory=bound('build/terminal/directory-live-checks.json',runtime);assert directory['inputs']==311
 context=bound('build/terminal/directory-context-checks.json',runtime);assert context['inputs']==507
 retained=bound('build/far-storage-dos/checks.json',runtime)
 assert all(retained['checks'].values()) and len(bytes.fromhex(retained['sample_hex']))==64
 assert retained['checks']['configuration_far_code_sum_and_full_C_extent_survive_child_allocation_fill']
 regression=read('build/terminal/setup-profile-regression.json')
 assert regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 commands=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert [r['command'] for r in regression['commands']]==commands and all(r['exit_code']==0 for r in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json');assert proof['passed'] and proof['output_count']==60
 for path,digest in [('terminal/TERMINAL.EXE',runtime),('setup/PRMEDIT.EXE',editor)]:assert proof['outputs'][path]['sha256']==digest and proof['outputs'][path]['matches_workspace']
 scripts=['standalone/record_setup_live.py','standalone/check_setup_live.py','standalone/test_setup_live_dos.py','standalone/check_program_actions_live.py','standalone/test_setup_startup_dos.py','standalone/check_live_configuration.py','standalone/check_config_far_live.py','standalone/check_directory_live.py','standalone/check_directory_context.py','standalone/test_far_storage_dos.py','standalone/far_storage_child.asm','standalone/terminal_memory.py','standalone/build_terminal.py']
 scripts+=['standalone/check_live_setup_owner.py','standalone/check_live_setup_apply.py','standalone/live_setup_kernel.py']
 scripts+=['standalone/check_live_setup_policy.py','standalone/check_live_setup_link.py','standalone/setup_watch.asm']
 scripts+=['standalone/check_live_setup_profile.py']
 scripts+=['standalone/check_port_handoff.py']
 artifacts=['build/terminal/setup-profile-regression.json','build/terminal/setup-profile-regression.log','build/terminal/setup-live-checks.json','build/setup-startup/live-checks.json','build/terminal/config-far-checks.json','build/live-configuration/terminal-checks.json','build/terminal/directory-live-checks.json','build/terminal/directory-context-checks.json','build/far-storage-dos/checks.json','build/terminal/live-setup-owner-checks.json','build/terminal/live-setup-apply-checks.json','build/terminal/live-setup-policy-checks.json','build/terminal/live-setup-link-checks.json','build/terminal/live-setup-profile-checks.json']
 artifacts+=['build/terminal/port-handoff-checks.json']
 uart_samples={}
 for case in dos['cases']:
  name=case['case'];assert Path(name).name==name
  folder='build/setup-startup/'+name
  sample=struct.unpack('<6H',(ROOT/folder/'WATCH.BIN').read_bytes())
  assert sample[0]==0x5355 and sample[4]>0
  assert sample[2]==(3 if name.endswith('apply-baud') else 1)
  assert sample[5]==(3 if name.endswith('apply-line') else 1)
  assert (ROOT/folder/'BEFORE.BIN').read_bytes()==(ROOT/folder/'AFTER.BIN').read_bytes()
  uart_samples[name]=dict(active_timer_samples=sample[4],divisor_bitmap=sample[2],last_divisor=sample[3],line_bitmap=sample[5])
  artifacts += [folder+'/'+f for f in ['WATCH.BIN','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','TEST.PRM','serial.bin']]
  if (ROOT/folder/'TEST.KBD').exists():artifacts.append(folder+'/TEST.KBD')
 common=dict(passed=True,binary_sha256=runtime,editor_sha256=editor,memory_layout=manifest['memory_layout'],terminal_regression=regression,source_rebuild=dict(report='docs/validation/application-components-source-build.json',source_snapshot_sha256=proof['source_snapshot_sha256'],output_count=proof['output_count']),source_sha256={p:sha(p) for p in scripts},retained_artifacts={p:sha(p) for p in artifacts})
 setup={**common,'linked':linked,'transaction_owner':owner,'selective_application':apply,'same_port_policy':policy,'same_port_handoff':link,'profile_switching':profile,'port_ownership_primitive':port,'actual_DOS':dos,'DOS_uart_samples':uart_samples,'scope':'AltF10 canonical bound editor/candidate owner with selective settings, confirmed same-port serial handoff and confirmed maintained4/6 profile reset. Strict staged target KBD import, frozen keyboard namespace, clean reset/view/keymap baseline, fresh DA and later RIS are checked. Actual DOS includes accepted/declined profile choices, target F1 mapping and missing-target-block preservation, plus prior serial/color cases. The separate cross-port ownership primitive has modeled linked evidence only and is not connected to the settings UI. COM settings integration and actual DOS multiport, other/full emulations, original PCSETUP shared ABI, complete application and physical modem remain open.'}
 config={**common,'call_frame_validation':frames,'terminal_candidate':candidate,'transaction_owner_inputs':owner['inputs'],'selective_application_inputs':apply['inputs'],'directory_inputs':directory['inputs'],'context_inputs':context['inputs'],'DOS_retention':retained,'scope':'Small-model C directory/candidate/setup-owner functions in a separately retained CS with explicit near-cdecl entries and register/cdecl resident callbacks. Independent actual-terminal CPU behavior, damaged MZ/frame rejection and real DOS allocation retention. General callbacks, dynamic overlays, full transport/profile handoff and complete application remain open.'}
 for name,value in [('setup-live.json',setup),('configuration-far-code.json',config)]:
  (ROOT/'docs/validation'/name).write_text(json.dumps(value,indent=2)+'\n')
 port_report={**port,'memory_layout':manifest['memory_layout'],
  'terminal_regression':dict(commands=len(commands),passed=True,report='docs/validation/setup-live.json'),
  'source_rebuild':common['source_rebuild'],
  'settings_UI_connected':False,'actual_DOS_multiport_verified':False,'physical_UART_verified':False}
 (ROOT/'docs/validation/port-handoff.json').write_text(json.dumps(port_report,indent=2)+'\n')
 print('Recorded direct setup and configuration CS:',len(commands),'regression commands;',candidate['inputs'],'terminal candidate inputs')
if __name__=='__main__':main()
