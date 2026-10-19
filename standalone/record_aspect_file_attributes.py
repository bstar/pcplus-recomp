#!/usr/bin/env python3
"""Bind attribute recovery, actual native-control/fixed VM and ENiGMA evidence."""
import json
from pathlib import Path
from build_aspect_file_attributes import ROOT,sha

def read(path):return json.loads((ROOT/path).read_text())
def main():
 paths=dict(native='build/aspect-file-attributes/checks.json',original='build/aspect-file-attributes/native-checks.json',host='build/aspect-file-attributes/compiler-checks.json',compiler='build/aspect-compiler-dos/checks.json',runtime='build/aspect-runtime/checks.json',VM='build/aspect-file-attributes-dos/integrated-01/checks.json',enumeration='build/aspect-enumeration-dos/attributes-regression-01/checks.json',info='build/aspect-file-info-dos/attributes-regression-01/checks.json',streams='build/aspect-script-files-dos/attributes-regression-01/checks.json',parent='build/aspect-file-attributes-parent-dos/integrated-01/checks.json',ENiGMA='build/bbs-lab/results/enigma/owned-attributes-login-01/search-checks.json')
 reports={name:read(path) for name,path in paths.items()};assert all(r['passed'] for r in reports.values())
 manifest_path='build/aspect-file-attributes/manifest.json';manifest=read(manifest_path)
 assert manifest['native_bytes']==100 and manifest['reused_bytes']==203
 for path,digest in manifest['sources'].items():assert sha(ROOT/path)==digest,path
 for name in ('native','original'):
  r=reports[name];assert r['cases']==1081 and r['original_comparisons']==(1081 if name=='original' else 0)
  assert r['manifest_sha256']==sha(ROOT/manifest_path) and r['checker_sha256']==sha(ROOT/'standalone/check_aspect_file_attributes.py')
  assert r['reused_checker_sha256']==sha(ROOT/'standalone/check_aspect_enumeration.py')
 fixture_path='standalone/fixtures/aspect_file_attributes_compiler_vectors.json';host=reports['host'];compiler=reports['compiler']
 assert (host['accepted'],host['rejected'])==(19,35)
 assert host['fixture_sha256']==compiler['fixture_sources'][fixture_path]==sha(ROOT/fixture_path)
 assert host['compiler_sha256']==compiler['host_compiler_sha256']==sha(ROOT/'src/aspect/compiler.py')
 assert compiler['case_count']==1664 and compiler['accepted']==918 and compiler['rejected']==746
 case_path='build/aspect-compiler-dos/cases.json';assert compiler['case_manifest_sha256']==sha(ROOT/case_path)
 cases={c['source_sha256']:c for c in read(case_path)}
 for case in read(fixture_path)['cases']:
  actual=cases[case['source_sha256']];assert actual['accepted']==case['success']
  if case['success']:assert actual['asx_sha256']==case['asx_sha256']
 terminal=sha(ROOT/'build/terminal/TERMINAL.EXE');runner=sha(ROOT/'build/aspect-runner/ASPECT.EXE');compiler_binary=sha(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE')
 assert compiler['binary_sha256']==compiler_binary
 runtime=reports['runtime'];assert runtime['supported_slot_count']==96 and runtime['unsupported_slot_cases']==119
 assert runtime['binary_sha256']==sha(ROOT/'build/aspect-runtime/EXECUTE.EXE')
 for name,counts,checker in [('VM',(279,2403),'test_aspect_file_attributes_dos.py'),('enumeration',(310,22377),'test_aspect_enumeration_dos.py'),('info',(155,1103),'test_aspect_file_info_dos.py'),('streams',(341,4727),'test_aspect_script_files_dos.py')]:
  r=reports[name];assert (r['cases'],r['assertions'])==counts and r['same_process_rounds']==31
  assert r['runner_sha256']==runner and r['compiler_sha256']==compiler_binary and r['checker_sha256']==sha(ROOT/'standalone'/checker)
  folder=ROOT/Path(paths[name]).parent;assert r['harness_sha256']==sha(folder/'harness.c') and r['result_sha256']==sha(folder/'drive/RESULT.TXT')
 vm=reports['VM'];vm_dir=ROOT/Path(paths['VM']).parent
 assert vm['native_control_sha256']==sha(vm_dir/'drive/NATIVE.EXE') and vm['native_control_result_sha256']==sha(vm_dir/'drive/NATIVE.TXT')
 assert vm['native_control_summary']=='NATIVE_CONTROL 10 checks 0 failures global=BEFORE near=RHS/RHS/RHS'
 assert vm['native_object_sha256']==sha(ROOT/'build/aspect-file-attributes/file_attributes.obj')
 assert vm['runtime_object_sha256']==sha(ROOT/'build/aspect-runtime/file_attributes.obj')
 assert vm['native_object_sha256']!=vm['runtime_object_sha256']
 core={}
 for module in ('runtime','script_file_runtime','file_info_runtime','enumeration_runtime','file_io','script_path','serial_runtime','receive_runtime','directory_runtime','when_runtime','set_runtime','find_runtime'):
  digest=sha(ROOT/'build/aspect-runtime'/(module+'.o'))
  for name in ('VM','enumeration','info','streams'):assert digest==sha(ROOT/Path(paths[name]).parent/(module+'.o')),module
  core[module]=digest
 parent=reports['parent'];assert parent['terminal_sha256']==terminal and parent['runner_sha256']==runner
 assert parent['checker_sha256']==sha(ROOT/'standalone/test_aspect_file_attributes_parent_dos.py')
 assert len(parent['cases'])==1 and all(parent['cases'][0]['checks'].values())
 enigma=reports['ENiGMA'];assert len(enigma['checks'])==20 and all(enigma['checks'].values())
 assert enigma['terminal_sha256']==terminal and enigma['runner_sha256']==sha(ROOT/'lab/bbs/enigma_search_dos.py')
 assert enigma['script_login']['runner_sha256']==runner and enigma['script_login']['compiler_sha256']==compiler_binary
 enigma_dir=ROOT/Path(paths['ENiGMA']).parent/'program'
 assert (enigma_dir/'ATTR.LOG').read_bytes()==b'RHS|' and (enigma_dir/'FIND.LOG').read_bytes()==b'FILECHK.BIN|FILECHK|BIN|5'
 assert enigma['script_login']['attribute_trace_sha256']==sha(enigma_dir/'ATTR.LOG')
 assert (enigma_dir/'LOGIN.LOG').read_bytes()==b'STARTAUTHREADY'
 package=read('build/dos-package/manifest.json')
 for name,digest in [('TERMINAL.EXE',terminal),('ASPECT.EXE',runner),('ASPCOMP.EXE',compiler_binary)]:assert package['files'][name]==digest==sha(ROOT/'build/dos-package'/name)
 proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
 assert proof['passed'] and proof['output_count']==241
 for name in ('terminal/TERMINAL.EXE','aspect-runner/ASPECT.EXE','aspect-compiler-dos/ASPCOMP.EXE','aspect-runtime/EXECUTE.EXE'):
  assert proof['outputs'][name]['sha256']==sha(ROOT/'build'/name)
 bundle='analysis/aspect-file-attributes/rea-01.json'
 report=dict(passed=True,terminal_sha256=terminal,runner_sha256=runner,compiler_sha256=compiler_binary,native_bytes=100,reused_native_bytes=203,supported_opcodes=96,unsupported_opcodes=119,
  evidence={name:dict(path=path,sha256=sha(ROOT/path)) for name,path in paths.items()},reports=reports,core_objects_identical=core,
  REA=dict(bundle_sha256=sha(ROOT/bundle),evidence_ids=[r['evidence_id'] for r in read(bundle)['records']]),
  source_build_proof=dict(path=proof_path,sha256=sha(ROOT/proof_path),outputs=241),package_manifest_sha256=sha(ROOT/'build/dos-package/manifest.json'),recorder_sha256=sha(Path(__file__)),
  maintained_policy='GETFATTR selects a destination and flushes far writeback; unmodified native wrapper retains lost-global behavior in flat recovery and actual DOS control.',
  retained_fixture_failure='Raw attribute helpers use cdecl RET: first primitive fixture incorrectly expected callee argument disposal; expectation corrected without native changes.',
  live_server_modified=False,physical_modem_validated=False,whole_application_gates_closed=[],remaining=['Original interactive returning-warning policy and broader native CRT/application equivalence.','119 remaining ASPECT opcode slots,including date/time commands,recorder and complete F01-F16 requirements.','Approved live ENiGMA decoder installation,actual catalog and physical modem validation.'])
 target=ROOT/'docs/validation/aspect-file-attributes.json';target.write_text(json.dumps(report,indent=2)+'\n')
 print('Recorded attributes:96 slots,279 VM runs,native far-writeback control,20 ENiGMA checks; all gates open')
if __name__=='__main__':main()
