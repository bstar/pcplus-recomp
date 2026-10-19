#!/usr/bin/env python3
"""Record line-controller placement against frozen prior/current DOS evidence."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def main():
 current=sha('build/terminal/TERMINAL.EXE');manifest=read('build/terminal/manifest.json')
 assert manifest['binary_sha256']==current
 for p,h in manifest['sources'].items():assert sha(p)==h,p
 baseline=read('build/line-controller-baseline/manifest.json');old=sha('build/line-controller-baseline/TERMINAL.EXE')
 assert baseline['binary_sha256']==old=='d418fca35f3ed3e4adbe7f87eb236f10660ddcc813cb73acfbe5abeac05627cd'
 prior=json.loads(subprocess.check_output(['git','show','7477a19:docs/validation/terminal-source-build.json'],cwd=ROOT))
 assert prior['passed'] and prior['manifest']==baseline and not prior['original_executable_present']
 paths=dict(paired='build/terminal/line-controller-far-checks.json',callbacks='build/terminal/line-callback-live-checks.json',layout='build/terminal/line-controller-layout-checks.json',
  policy='build/terminal/line-edit-live-checks.json',attributes='build/terminal/line-attributes-live-checks.json',ABI='build/terminal/config-far-checks.json',
  DOS='build/line-attributes-dos/controller-far-01/checks.json',ASPECT='build/aspect-renderer-dos/controller-far-02/checks.json',
  keys='build/aspect-keys-dos/controller-far-keys-01/checks.json',ENiGMA='build/bbs-lab/results/enigma/controller-far-search-01/search-checks.json')
 data={k:read(p) for k,p in paths.items()};reports={}
 for k,d in data.items():
  assert d['passed'],k
  assert d.get('binary_sha256',d.get('terminal_sha256'))==current,k
  reports[k]=dict(path=paths[k],sha256=sha(paths[k]))
 pair=data['paired'];assert pair['baseline_sha256']==old and (pair['line_cases'],pair['wait_cases'],pair['callback_cases'])==(192,96,24)
 assert pair['checker_sha256']==sha('standalone/check_line_controller_far.py')
 assert pair['baseline_map_sha256']==sha('build/line-controller-baseline/terminal.map')
 for p,h in pair['sources'].items():assert sha(p)==h,p
 cb=data['callbacks'];assert cb['cases']==24 and cb['checker_sha256']==sha('standalone/check_line_callbacks_live.py') and cb['mechanics_sha256']==pair['checker_sha256'] and not cb['original_inputs']
 layout=data['layout'];assert len(layout['rejected_mutations'])==45 and layout['far_relocations']==19 and layout['checker_sha256']==sha('standalone/check_line_controller_layout.py')
 assert len(data['policy']['cases'])==8 and all(c['passed'] for c in data['policy']['cases'])
 assert (data['attributes']['cases'],data['attributes']['pre_mutation_rejections'])==(512,45)
 assert data['attributes']['checker_sha256']==sha('standalone/check_line_attributes_live.py')
 dos=data['DOS'];assert all(dos['checks'].values())
 for p,h in dos['inputs'].items():assert sha(p)==h,p
 assert dos['capture_sha256']==sha('build/line-attributes-dos/controller-far-01/product/LINEATTR.BIN')
 expected={'original-control-N-wait','native-edits-origin-scroll'}
 aspect=data['ASPECT'];assert {c['case'] for c in aspect['cases']}==expected
 assert all(c['passed'] and all(c['checks'].values()) for c in aspect['cases'])
 assert aspect['checker_sha256']==sha('standalone/test_aspect_renderer_dos.py')
 wait=next(c for c in aspect['cases'] if c['case']=='original-control-N-wait');assert '/A:ORIGINAL' in wait['command']
 old_wait_path='build/aspect-renderer-dos/line-controller-baseline-01/checks.json';old_wait=read(old_wait_path)
 assert old_wait['passed'] and old_wait['terminal_sha256']==old and len(old_wait['cases'])==1
 assert old_wait['cases'][0]['case']=='original-control-N-wait' and '/A:ORIGINAL' in old_wait['cases'][0]['command']
 keys=data['keys'];assert len(keys['cases'])==1 and keys['cases'][0]['case']=='script-keys-6-halfcell' and keys['checker_sha256']==sha('standalone/test_aspect_keys_dos.py')
 assert keys['reused_renderer_checker_sha256']==sha('standalone/test_aspect_renderer_dos.py') and all(keys['cases'][0]['checks'].values())
 enigma=data['ENiGMA'];assert all(enigma['checks'].values()) and enigma['runner_sha256']==sha('lab/bbs/enigma_search_dos.py')
 live=ROOT.parent/'black-flag-bbs'
 for p,h in enigma['source_modules'].items():assert hashlib.sha256((live/p).read_bytes()).hexdigest()==h,p
 live_client=hashlib.sha256((live/'core/client.js').read_bytes()).hexdigest();assert live_client=='d66207f46af13ae4acb0ac430b1d0f2572a03722c79f4bcb7125dcd01e98e788'
 proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
 assert proof['passed'] and proof['output_count']==178 and proof['outputs']['terminal/TERMINAL.EXE']['sha256']==current
 assert {'standalone/check_line_callbacks_live.py','standalone/check_line_controller_layout.py'}<=set(proof['build_scripts'])
 assert read('build/dos-package/manifest.json')['files']['TERMINAL.EXE']==current
 before=baseline['memory_layout'];after=manifest['memory_layout']
 assert before['resident_code_bytes']-after['resident_code_bytes']==280 and after['resident_code_spare_bytes']==290
 assert before['near_bytes']==after['near_bytes']==64832
 assert (after['line_controller_entry_pairs_verified'],after['line_controller_register_callbacks_verified'],after['line_controller_code_bytes'])==(4,3,335)
 assert after['aspect_controller_read_references_verified']==1
 result=dict(passed=True,terminal_sha256=current,reports=reports,
  baseline=dict(commit='7477a19',terminal_sha256=old,map_sha256=sha('build/line-controller-baseline/terminal.map'),manifest_sha256=sha('build/line-controller-baseline/manifest.json'),source_only_proof_from_git=True,
   actual_ASPECT_wait=dict(path=old_wait_path,sha256=sha(old_wait_path))),
  resident_layout=dict(before_bytes=before['resident_code_bytes'],after_bytes=after['resident_code_bytes'],freed_bytes=280,before_available=before['resident_code_spare_bytes'],after_available=290,far_controller_bytes=335,data_stack_bytes=64832,loaded_module_before=before['loaded_module_bytes'],loaded_module_after=after['loaded_module_bytes'],allocated_module_before=before['minimum_allocated_module_bytes'],allocated_module_after=after['minimum_allocated_module_bytes']),
  paired=dict(lines=192,waits=96,callbacks=24),current_source_only_callbacks=24,damaged_layouts_rejected=45,
  actual_DOS=dict(checks=dos['checks'],state=dos['state'],capture_sha256=dos['capture_sha256']),
  ASPECT=dict(cases=[c['case'] for c in aspect['cases']],ORIGINAL_wait_policy_verified=True,half_duplex_cell_keys_passed=True),
  ENiGMA=dict(checks=enigma['checks'],source_modules=enigma['source_modules'],live_client_sha256=live_client,live_server_modified=False),
  source_build=dict(path=proof_path,sha256=sha(proof_path),outputs=proof['output_count'],previous_build_outputs_present=proof['previous_build_outputs_present']),
  memory_layout=after,sources={p:sha(p) for p in ('src/terminal/line_edit.asm','src/terminal/line_controller.asm','src/terminal/attribute_boundary.asm','standalone/terminal_memory.py','standalone/test_aspect_renderer_dos.py','standalone/check_line_controller_far.py','standalone/check_line_callbacks_live.py','standalone/check_line_controller_layout.py')},
  recorder_sha256=sha(Path(__file__).relative_to(ROOT)),whole_application_gates_closed=[],
  scope='Source-owned line controller placement with unchanged public near interfaces and typed register-only callbacks.280 resident bytes recovered. Independent current-only callback/layout tests, frozen-source-built paired state behavior, real DOS plane fixture, actual ASPECT native edits/ORIGINAL wait/representative cell keys, owned-source ENiGMA navigation and178-output fresh rebuild. No original executable in ordinary builds.',
  limitations=['Code remains loaded in the far segment; loaded and minimum allocated module sizes each grow48 bytes.',
   'The paired characterization explicitly reads the prior maintained binary; ordinary builds and current-only source-proof checks do not.',
   'Protected-plane DOS coverage uses the documented test-only state fixture. Normal BBS/ASPECT coverage uses supported defaults.',
   'Live server installation, physical timing/modem validation and complete application gates remain open.'])
 (ROOT/'docs/validation/line-controller-far.json').write_text(json.dumps(result,indent=2)+'\n');print('Recorded far line controller:280 resident bytes, paired behavior, typed ABI, DOS/ASPECT/ENiGMA and source-only proof')
if __name__=='__main__':main()
