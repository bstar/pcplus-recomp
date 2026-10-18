#!/usr/bin/env python3
"""Bind direct settings invocation and configuration segmentation to evidence."""
import hashlib,json,subprocess
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
 assert len(dos['cases'])==3 and all(c['passed'] and all(c['checks'].values()) for c in dos['cases'])
 owner=bound('build/terminal/live-setup-owner-checks.json',runtime);assert owner['inputs']==76
 apply=bound('build/terminal/live-setup-apply-checks.json',runtime);assert apply['inputs']==27
 frames=bound('build/terminal/config-far-checks.json',runtime)
 assert frames['configuration_bridge_pairs_verified']==20 and len(frames['rejected_mutations'])==89
 candidate=bound('build/live-configuration/terminal-checks.json',runtime)
 assert candidate['host']=='terminal-far-C' and candidate['inputs']==389 and candidate['maximum_CPU_call_stack_bytes']<8192-3514-16
 directory=bound('build/terminal/directory-live-checks.json',runtime);assert directory['inputs']==311
 context=bound('build/terminal/directory-context-checks.json',runtime);assert context['inputs']==507
 retained=bound('build/far-storage-dos/checks.json',runtime)
 assert all(retained['checks'].values()) and len(bytes.fromhex(retained['sample_hex']))==64
 assert retained['checks']['configuration_far_code_sum_and_full_C_extent_survive_child_allocation_fill']
 regression=read('build/terminal/setup-apply-regression.json')
 assert regression['passed'] and regression['complete'] and regression['binary_sha256']==runtime
 commands=subprocess.check_output(['make','-n','test-terminal'],cwd=ROOT,text=True).splitlines()
 assert [r['command'] for r in regression['commands']]==commands and all(r['exit_code']==0 for r in regression['commands'])
 proof=read('docs/validation/application-components-source-build.json');assert proof['passed'] and proof['output_count']==60
 for path,digest in [('terminal/TERMINAL.EXE',runtime),('setup/PRMEDIT.EXE',editor)]:assert proof['outputs'][path]['sha256']==digest and proof['outputs'][path]['matches_workspace']
 scripts=['standalone/record_setup_live.py','standalone/check_setup_live.py','standalone/test_setup_live_dos.py','standalone/check_program_actions_live.py','standalone/test_setup_startup_dos.py','standalone/check_live_configuration.py','standalone/check_config_far_live.py','standalone/check_directory_live.py','standalone/check_directory_context.py','standalone/test_far_storage_dos.py','standalone/far_storage_child.asm','standalone/terminal_memory.py','standalone/build_terminal.py']
 scripts+=['standalone/check_live_setup_owner.py','standalone/check_live_setup_apply.py','standalone/live_setup_kernel.py']
 artifacts=['build/terminal/setup-apply-regression.json','build/terminal/setup-apply-regression.log','build/terminal/setup-live-checks.json','build/setup-startup/live-checks.json','build/terminal/config-far-checks.json','build/live-configuration/terminal-checks.json','build/terminal/directory-live-checks.json','build/terminal/directory-context-checks.json','build/far-storage-dos/checks.json','build/terminal/live-setup-owner-checks.json','build/terminal/live-setup-apply-checks.json']
 common=dict(passed=True,binary_sha256=runtime,editor_sha256=editor,memory_layout=manifest['memory_layout'],terminal_regression=regression,source_rebuild=dict(report='docs/validation/application-components-source-build.json',source_snapshot_sha256=proof['source_snapshot_sha256'],output_count=proof['output_count']),source_sha256={p:sha(p) for p in scripts},retained_artifacts={p:sha(p) for p in artifacts})
 setup={**common,'linked':linked,'transaction_owner':owner,'selective_application':apply,'actual_DOS':dos,'scope':'AltF10 production editor with canonical startup identity, retained directory selection, current effective transport/autobaud snapshot and native expansion validation before selective display/mapping/modem/BREAK application. Actual DOS post-child remote text attributes and fresh cursor reply prove a live color save; baud save remains deferred with independent UART/vector samples. Link/profile ownership changes, original PCSETUP shared ABI, complete settings/application and physical modem remain open.'}
 config={**common,'call_frame_validation':frames,'terminal_candidate':candidate,'transaction_owner_inputs':owner['inputs'],'selective_application_inputs':apply['inputs'],'directory_inputs':directory['inputs'],'context_inputs':context['inputs'],'DOS_retention':retained,'scope':'Small-model C directory/candidate/setup-owner functions in a separately retained CS with explicit near-cdecl entries and register/cdecl resident callbacks. Independent actual-terminal CPU behavior, damaged MZ/frame rejection and real DOS allocation retention. General callbacks, dynamic overlays, full transport/profile handoff and complete application remain open.'}
 for name,value in [('setup-live.json',setup),('configuration-far-code.json',config)]:
  (ROOT/'docs/validation'/name).write_text(json.dumps(value,indent=2)+'\n')
 print('Recorded direct setup and configuration CS:',len(commands),'regression commands;',candidate['inputs'],'terminal candidate inputs')
if __name__=='__main__':main()
