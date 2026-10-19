#!/usr/bin/env python3
"""Bind native recovery, DOS compiler/VM/parent and owned ENiGMA results."""
import hashlib,json
from pathlib import Path
from build_aspect_file_info import ROOT,sha

def read(path):return json.loads((ROOT/path).read_text())
def main():
 paths=dict(native='build/aspect-file-info/checks.json',original='build/aspect-file-info/native-checks.json',host='build/aspect-file-info/compiler-checks.json',compiler='build/aspect-compiler-dos/checks.json',runtime='build/aspect-runtime/checks.json',VM='build/aspect-file-info-dos/integrated-03/checks.json',streams='build/aspect-script-files-dos/file-info-regression-01/checks.json',parent='build/aspect-file-info-parent-dos/integrated-01/checks.json',ENiGMA='build/bbs-lab/results/enigma/owned-file-info-login-01/search-checks.json')
 reports={name:read(path) for name,path in paths.items()};assert all(r['passed'] for r in reports.values())
 native_manifest=read('build/aspect-file-info/manifest.json');assert native_manifest['native_bytes']==177
 for path,digest in native_manifest['sources'].items():assert sha(ROOT/path)==digest,path
 for name in ('native','original'):
  report=reports[name];assert report['cases']==322 and report['original_comparisons']==(322 if name=='original' else 0)
  assert report['manifest_sha256']==sha(ROOT/'build/aspect-file-info/manifest.json')
  assert report['checker_sha256']==sha(ROOT/'standalone/check_aspect_file_info.py')
 fixture_path='standalone/fixtures/aspect_file_info_compiler_vectors.json'
 host=reports['host'];compiler=reports['compiler'];assert (host['accepted'],host['rejected'])==(17,67)
 assert host['fixture_sha256']==sha(ROOT/fixture_path)==compiler['fixture_sources'][fixture_path]
 assert host['compiler_sha256']==compiler['host_compiler_sha256']==sha(ROOT/'src/aspect/compiler.py')
 assert compiler['case_count']==1564
 dos_cases={c['source_sha256']:c for c in read('build/aspect-compiler-dos/cases.json')}
 assert compiler['case_manifest_sha256']==sha(ROOT/'build/aspect-compiler-dos/cases.json')
 for case in read(fixture_path)['cases']:
  actual=dos_cases[case['source_sha256']];assert actual['accepted']==case['success']
  if case['success']:assert actual['asx_sha256']==case['asx_sha256']
 terminal=sha(ROOT/'build/terminal/TERMINAL.EXE');runner=sha(ROOT/'build/aspect-runner/ASPECT.EXE');compiler_binary=sha(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE')
 assert compiler['binary_sha256']==compiler_binary
 runtime=reports['runtime'];assert runtime['supported_slot_count']==92 and runtime['unsupported_slot_cases']==123
 assert runtime['binary_sha256']==sha(ROOT/'build/aspect-runtime/EXECUTE.EXE')
 vm=reports['VM'];streams=reports['streams']
 assert (vm['cases'],vm['assertions'],vm['same_process_rounds'])==(155,1103,31)
 assert streams['cases']==341 and streams['assertions']==4727
 for name,path in [('VM','standalone/test_aspect_file_info_dos.py'),('streams','standalone/test_aspect_script_files_dos.py')]:
  report=reports[name];assert report['runner_sha256']==runner and report['compiler_sha256']==compiler_binary
  assert report['checker_sha256']==sha(ROOT/path)
  folder=ROOT/Path(paths[name]).parent
  assert report['harness_sha256']==sha(folder/'harness.c') and report['result_sha256']==sha(folder/'drive/RESULT.TXT')
 core={}
 for module in ('runtime','script_file_runtime','file_info_runtime','file_io','script_path','serial_runtime','receive_runtime','directory_runtime','when_runtime','set_runtime','find_runtime'):
  digest=sha(ROOT/'build/aspect-runtime'/(module+'.o'))
  for name in ('VM','streams'):assert sha(ROOT/Path(paths[name]).parent/(module+'.o'))==digest,module
  core[module]=digest
 parent=reports['parent'];assert parent['terminal_sha256']==terminal and parent['runner_sha256']==runner
 assert parent['checker_sha256']==sha(ROOT/'standalone/test_aspect_file_info_parent_dos.py')
 assert len(parent['cases'])==1 and all(parent['cases'][0]['checks'].values())
 enigma=reports['ENiGMA'];assert len(enigma['checks'])==18 and all(enigma['checks'].values())
 assert enigma['terminal_sha256']==terminal and enigma['runner_sha256']==sha(ROOT/'lab/bbs/enigma_search_dos.py')
 assert enigma['script_login']['runner_sha256']==runner and enigma['script_login']['compiler_sha256']==compiler_binary
 enigma_dir=ROOT/Path(paths['ENiGMA']).parent/'program'
 assert (enigma_dir/'FILECHK.BIN').read_bytes()==b'proof' and not (enigma_dir/'FILECHK.TMP').exists()
 assert enigma['script_login']['file_info_probe_sha256']==sha(enigma_dir/'FILECHK.BIN')
 assert (enigma_dir/'LOGIN.LOG').read_bytes()==b'STARTAUTHREADY'
 package=read('build/dos-package/manifest.json')
 for name,digest in [('TERMINAL.EXE',terminal),('ASPECT.EXE',runner),('ASPCOMP.EXE',compiler_binary)]:assert package['files'][name]==digest==sha(ROOT/'build/dos-package'/name)
 proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
 assert proof['passed'] and proof['output_count']==225
 for name in ('terminal/TERMINAL.EXE','aspect-runner/ASPECT.EXE','aspect-compiler-dos/ASPCOMP.EXE','aspect-runtime/EXECUTE.EXE'):
  assert proof['outputs'][name]['sha256']==sha(ROOT/'build'/name)
 report=dict(passed=True,terminal_sha256=terminal,runner_sha256=runner,compiler_sha256=compiler_binary,native_bytes=177,supported_opcodes=92,unsupported_opcodes=123,
  evidence={name:dict(path=path,sha256=sha(ROOT/path)) for name,path in paths.items()},reports=reports,core_objects_identical=core,
  REA=dict(evidence_bundle_sha256=sha(ROOT/'analysis/aspect-file-info/rea-complete-01.json'),commands=['ev_47ddaa8047cc400cf54b4dd98ec9772accaa9b498d5935b23904c52f040ca45f','ev_db1d9e4972936b9181a43e76d1f6249f772efdb730df0f0df95e6c946f26145a','ev_de53ca1817b5c922295c722841810b7aa1348b4e82bbf7307a965093a8ffb1a0']),
  source_build_proof=dict(path=proof_path,sha256=sha(ROOT/proof_path),outputs=225),package_manifest_sha256=sha(ROOT/'build/dos-package/manifest.json'),recorder_sha256=sha(Path(__file__)),
  retained_failures=['First DOS fixture used unsupported global initializer; corrected fixture only.','Second DOS run found missing DGROUP relocation for local rb strings:155 assertions failed. Production assembly fixed; third run passes without changing flat native bytes.'],
  live_server_modified=False,physical_modem_validated=False,whole_application_gates_closed=[],remaining=['Original returning-warning/unchecked runtime policy and broader CRT equivalence.','123 remaining ASPECT opcode slots, recorder and full F01-F16 requirements.','Approved live ENiGMA decoder installation, actual catalog and physical modem validation.'])
 target=ROOT/'docs/validation/aspect-file-info.json';target.write_text(json.dumps(report,indent=2)+'\n')
 print('Recorded ASPECT filesystem queries/rename:92 slots,155 VM runs,18 ENiGMA checks; all gates open')
if __name__=='__main__':main()
