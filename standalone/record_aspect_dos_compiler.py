#!/usr/bin/env python3
"""Bind DOS frontend phases, ownership/CRT evidence and original-free builds."""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def main():
 reports={};binaries={}
 for name,leaf,cases in [('lexer','ASPLEX.EXE',1154),('unit','ASPINV.EXE',1164)]:
  prefix='build/aspect-compiler-'+name+'/';manifest=read(prefix+'manifest.json');checks=read(prefix+'checks.json')
  assert not manifest['original_inputs'] and checks['passed'] and not checks['original_inputs']
  assert checks['binary_sha256']==manifest['binary_sha256']==sha(prefix+leaf)
  assert checks['manifest_sha256']==sha(prefix+'manifest.json')
  assert checks['case_count']==cases and checks['host_compiler_sha256']==sha('src/aspect/compiler.py')
  assert checks['checker_sha256']==sha('standalone/check_aspect_compiler_'+name+'.py')
  for source,digest in manifest['sources'].items():assert sha(source)==digest,source
  for source,digest in checks['fixture_sources'].items():assert sha(source)==digest,source
  binaries['aspect-compiler-'+name+'/'+leaf]=manifest['binary_sha256']
  reports[name]=dict(manifest_sha256=sha(prefix+'manifest.json'),checks_sha256=sha(prefix+'checks.json'),report=checks)
 lexer=reports['lexer']['report'];unit=reports['unit']['report']
 assert lexer['DOS_summary']=='LEXER 1154 cases 2369 checks 0 failures'
 assert (lexer['line_count'],lexer['token_count'],lexer['tokens_bytes'])==(92290,75155,2130319)
 assert unit['DOS_summary']=='UNIT 1164 cases 3326 checks 0 failures'
 assert unit['ownership_summary']=='OWNERSHIP 18 injected failures and200 successful load/dispose cycles'
 for source,digest in unit['heap_observer_sources'].items():assert sha(source)==digest,source
 assert unit['reused_corpus_checker_sha256']==sha('standalone/check_aspect_compiler_lexer.py')
 crt=unit['isolated_CRT_probe'];assert crt['source_sha256']==sha('standalone/compiler_crt_heap_probe.c')
 assert crt['binary_sha256']==sha('build/aspect-compiler-unit/tests/CRTHEAP.EXE')
 assert 'independent_during0 independent_after0 used_during1 used_after0' in crt['summary']
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed'] and proof['output_count']==151 and all(v['matches_workspace'] for v in proof['outputs'].values())
 for name,digest in binaries.items():assert proof['outputs'][name]['sha256']==digest
 # This chapter adds frontend tools and changes no application product bytes.
 prior=read('docs/validation/aspect-script-label.json')
 for path,key in [('terminal/TERMINAL.EXE','terminal_sha256'),('aspect-runner/ASPECT.EXE','runner_sha256')]:
  assert proof['outputs'][path]['sha256']==prior[key]==sha('build/'+path)
 old=(ROOT/'analysis/dos-compiler-heap/CRTHEAP-feef536a.EXE').read_bytes()
 assert hashlib.sha256(old).hexdigest()=='feef536a2ceec25567d164d566c749a5c085d5b5a847542790a0b977939d8235'
 current=(ROOT/'build/aspect-compiler-unit/tests/CRTHEAP.EXE').read_bytes()
 listing=(ROOT/'build/aspect-compiler-unit/tests/CRTHEAP.map').read_text()
 match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})[+* ]+\s+__HeapWalk_\s*$',listing,re.M|re.I);assert match
 old_header=struct.unpack_from('<H',old,8)[0]*16;new_header=struct.unpack_from('<H',current,8)[0]*16
 current_offset=int(match[1],16)*16+int(match[2],16)
 original_routine=old[old_header+0xa0c:old_header+0xa0c+267]
 assert original_routine==current[new_header+current_offset:new_header+current_offset+267]
 result=dict(passed=True,recorder_sha256=sha('standalone/record_aspect_dos_compiler.py'),reports=reports,
  source_proof_sha256=sha('docs/validation/application-components-source-build.json'),reproduced_output_count=151,
  application_bytes_unchanged_from_prior_label_checkpoint=True,
  CRT_analysis=dict(evidence_id='ev_d1a5f2f22b386770e1316405e3db283a854074f3496c79f5004bb421f01b9b66',
   target_sha256=hashlib.sha256(old).hexdigest(),current_runtime_probe_sha256=crt['binary_sha256'],identical_routine_sha256=hashlib.sha256(original_routine).hexdigest(),function='__HeapWalk',linear_address='0x10a0c',body_bytes=267,
   scope='REA/Ghidra static instructions plus separate owned malloc-only DOS execution. Pinned checker false failure; production allocator unchanged. Independent observer covers block/free-list/used-count structure and rejects six corruptions or capacity failures.'),
  compiler_stages_completed=['streaming lexical frontend','declaration/procedure inventory and owned source ranges'],
  required_remaining=['expression and full body/initializer validation','typed operand/command and positional string emission','all statement families and exact procedure pruning','32-bit ASX fixups and exact output parity','DOS compiler CLI and transactional output','runtime ASP/fallback integration preserving UART/file/settings ownership','full native compiler coverage beyond the host subset, recorder and remaining F01-F16 requirements'],
  limitations=['ASPLEX/ASPINV are diagnostics and cannot generate ASX.','Successful inventory is not a valid-program/compiler acceptance claim.','Native grammar for previously unproved malformed declaration edges remains an oracle task.','Physical hardware and modem compatibility are not established by these frontend tests.'],whole_application_gates_closed=[])
 (ROOT/'docs/validation/aspect-dos-compiler.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Bound DOS compiler frontend stages:',lexer['case_count'],'lexical,',unit['case_count'],'inventory; full DOS compiler remains pending')
if __name__=='__main__':main()
