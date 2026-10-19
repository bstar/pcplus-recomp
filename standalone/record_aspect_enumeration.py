#!/usr/bin/env python3
"""Bind native file enumeration to compiler, real DOS, parent and ENiGMA evidence."""
import hashlib,json
from pathlib import Path
from build_aspect_enumeration import ROOT,sha

def read(path):return json.loads((ROOT/path).read_text())
def main():
 paths=dict(inventory='build/aspect-compiler-unit/checks.json',expressions='build/aspect-compiler-expression/checks.json',native='build/aspect-enumeration/checks.json',original='build/aspect-enumeration/native-checks.json',host='build/aspect-enumeration/compiler-checks.json',compiler='build/aspect-compiler-dos/checks.json',runtime='build/aspect-runtime/checks.json',VM='build/aspect-enumeration-dos/integrated-02/checks.json',info='build/aspect-file-info-dos/enumeration-regression-01/checks.json',streams='build/aspect-script-files-dos/enumeration-regression-01/checks.json',parent='build/aspect-enumeration-parent-dos/integrated-01/checks.json',ENiGMA='build/bbs-lab/results/enigma/owned-enumeration-login-01/search-checks.json')
 reports={name:read(path) for name,path in paths.items()};assert all(r['passed'] for r in reports.values())
 for name,folder,binary,checker in [('inventory','aspect-compiler-unit','ASPINV.EXE','check_aspect_compiler_unit.py'),('expressions','aspect-compiler-expression','ASPEXP.EXE','check_aspect_compiler_expression.py')]:
  r=reports[name];assert r['binary_sha256']==sha(ROOT/'build'/folder/binary)
  assert r['checker_sha256']==sha(ROOT/'standalone'/checker)
  for path,digest in read('build/'+folder+'/manifest.json')['sources'].items():assert sha(ROOT/path)==digest,path
 assert reports['inventory']['case_count']==1611 and reports['expressions']['case_count']==3494
 manifest_path='build/aspect-enumeration/manifest.json';manifest=read(manifest_path)
 assert manifest['native_bytes']==675
 for path,digest in manifest['sources'].items():assert sha(ROOT/path)==digest,path
 for name in ('native','original'):
  r=reports[name];assert r['cases']==885 and r['original_comparisons']==(885 if name=='original' else 0)
  assert r['manifest_sha256']==sha(ROOT/manifest_path) and r['checker_sha256']==sha(ROOT/'standalone/check_aspect_enumeration.py')
 fixture_path='standalone/fixtures/aspect_enumeration_compiler_vectors.json';host=reports['host'];compiler=reports['compiler']
 assert (host['accepted'],host['rejected'])==(17,29)
 assert host['fixture_sha256']==compiler['fixture_sources'][fixture_path]==sha(ROOT/fixture_path)
 assert host['compiler_sha256']==compiler['host_compiler_sha256']==sha(ROOT/'src/aspect/compiler.py')
 assert compiler['case_count']==1610 and compiler['accepted']==899 and compiler['rejected']==711
 case_path='build/aspect-compiler-dos/cases.json';assert compiler['case_manifest_sha256']==sha(ROOT/case_path)
 cases={c['source_sha256']:c for c in read(case_path)}
 for case in read(fixture_path)['cases']:
  actual=cases[case['source_sha256']];assert actual['accepted']==case['success']
  if case['success']:assert actual['asx_sha256']==case['asx_sha256']
 terminal=sha(ROOT/'build/terminal/TERMINAL.EXE');runner=sha(ROOT/'build/aspect-runner/ASPECT.EXE');compiler_binary=sha(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE')
 assert compiler['binary_sha256']==compiler_binary
 runtime=reports['runtime'];assert runtime['supported_slot_count']==94 and runtime['unsupported_slot_cases']==121
 assert runtime['binary_sha256']==sha(ROOT/'build/aspect-runtime/EXECUTE.EXE')
 for name,counts,checker in [('VM',(310,22377),'test_aspect_enumeration_dos.py'),('info',(155,1103),'test_aspect_file_info_dos.py'),('streams',(341,4727),'test_aspect_script_files_dos.py')]:
  r=reports[name];assert (r['cases'],r['assertions'])==counts and r['same_process_rounds']==31
  assert r['runner_sha256']==runner and r['compiler_sha256']==compiler_binary
  assert r['checker_sha256']==sha(ROOT/'standalone'/checker)
  folder=ROOT/Path(paths[name]).parent;assert r['harness_sha256']==sha(folder/'harness.c') and r['result_sha256']==sha(folder/'drive/RESULT.TXT')
 core={}
 for module in ('runtime','script_file_runtime','file_info_runtime','enumeration_runtime','file_io','script_path','serial_runtime','receive_runtime','directory_runtime','when_runtime','set_runtime','find_runtime'):
  digest=sha(ROOT/'build/aspect-runtime'/(module+'.o'))
  for name in ('VM','info','streams'):assert digest==sha(ROOT/Path(paths[name]).parent/(module+'.o')),module
  core[module]=digest
 parent=reports['parent'];assert parent['terminal_sha256']==terminal and parent['runner_sha256']==runner
 assert parent['checker_sha256']==sha(ROOT/'standalone/test_aspect_enumeration_parent_dos.py')
 assert len(parent['cases'])==1 and all(parent['cases'][0]['checks'].values())
 enigma=reports['ENiGMA'];assert len(enigma['checks'])==19 and all(enigma['checks'].values())
 assert enigma['terminal_sha256']==terminal and enigma['runner_sha256']==sha(ROOT/'lab/bbs/enigma_search_dos.py')
 assert enigma['script_login']['runner_sha256']==runner and enigma['script_login']['compiler_sha256']==compiler_binary
 enigma_dir=ROOT/Path(paths['ENiGMA']).parent/'program'
 assert (enigma_dir/'FIND.LOG').read_bytes()==b'FILECHK.BIN|FILECHK|BIN|5'
 assert enigma['script_login']['enumeration_trace_sha256']==sha(enigma_dir/'FIND.LOG')
 assert (enigma_dir/'LOGIN.LOG').read_bytes()==b'STARTAUTHREADY'
 package=read('build/dos-package/manifest.json')
 for name,digest in [('TERMINAL.EXE',terminal),('ASPECT.EXE',runner),('ASPCOMP.EXE',compiler_binary)]:assert package['files'][name]==digest==sha(ROOT/'build/dos-package'/name)
 proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
 assert proof['passed'] and proof['output_count']==234
 for name in ('terminal/TERMINAL.EXE','aspect-runner/ASPECT.EXE','aspect-compiler-dos/ASPCOMP.EXE','aspect-runtime/EXECUTE.EXE'):
  assert proof['outputs'][name]['sha256']==sha(ROOT/'build'/name)
 bundles=['analysis/aspect-enumeration/rea-overlay18-01.json','analysis/aspect-enumeration/rea-overlay16-01.json']
 report=dict(passed=True,terminal_sha256=terminal,runner_sha256=runner,compiler_sha256=compiler_binary,native_bytes=675,supported_opcodes=94,unsupported_opcodes=121,
  evidence={name:dict(path=path,sha256=sha(ROOT/path)) for name,path in paths.items()},reports=reports,core_objects_identical=core,
  REA=[dict(bundle_sha256=sha(ROOT/path),evidence_ids=[r['evidence_id'] for r in read(path)['records']]) for path in bundles],
  source_build_proof=dict(path=proof_path,sha256=sha(ROOT/proof_path),outputs=234),package_manifest_sha256=sha(ROOT/'build/dos-package/manifest.json'),recorder_sha256=sha(Path(__file__)),
  maintained_policies=['Own81-byte pattern,43-byte DTA; preserve caller DTA on every first/next.','Next before a first returns no match without adopting another caller context.','Four-byte no-dot volume admission avoids original DS0000 memmove; exact675-byte baseline remains unchanged.'],
  retained_failures=['First attribute oracle incorrectly expected V/mode0 to set directory bit; expectation corrected without native code changes.','Initial links exposed missing DOS prototype and C symbol aliases; no failed DOS binary executed.','First fresh proof matched232/234 outputs; stale workspace ASPINV/ASPEXP diagnostics were rebuilt and checked before a separate fresh proof.'],
  live_server_modified=False,physical_modem_validated=False,whole_application_gates_closed=[],remaining=['Broader original CRT/formatting equivalence and other file metadata commands.','121 remaining ASPECT opcode slots,recorder and complete F01-F16 requirements.','Approved live ENiGMA decoder installation,actual catalog and physical modem validation.'])
 target=ROOT/'docs/validation/aspect-enumeration.json';target.write_text(json.dumps(report,indent=2)+'\n')
 print('Recorded enumeration:94 slots,310 DOS VM runs,19 ENiGMA checks; all gates open')
if __name__=='__main__':main()
