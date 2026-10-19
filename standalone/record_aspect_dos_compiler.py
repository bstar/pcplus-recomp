#!/usr/bin/env python3
"""Bind DOS frontend phases, ownership/CRT evidence and original-free builds."""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text())
def main():
 reports={};binaries={}
 for name,leaf,cases in [('lexer','ASPLEX.EXE',1164),('unit','ASPINV.EXE',1174),('expression','ASPEXP.EXE',3459),('dos','ASPCOMP.EXE',1173)]:
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
 lexer=reports['lexer']['report'];unit=reports['unit']['report'];expression=reports['expression']['report'];dos=reports['dos']['report']
 assert lexer['DOS_summary']=='LEXER 1164 cases 2389 checks 0 failures'
 assert (lexer['line_count'],lexer['token_count'],lexer['tokens_bytes'])==(92324,75247,2131983)
 assert unit['DOS_summary']=='UNIT 1174 cases 3346 checks 0 failures'
 assert unit['ownership_summary']=='OWNERSHIP 18 injected failures and200 successful load/dispose cycles'
 assert expression['DOS_summary'].endswith('EXPRESSION 3459 cases 0 failures')
 assert expression['API_summary']=='API 1356 checks 0 failures'
 assert expression['ownership_cycles']==100 and expression['CLI_children']==6
 assert (expression['accepted'],expression['rejected'])==(2530,929)
 for source,digest in expression['reused_sources'].items():assert sha(source)==digest,source
 assert expression['case_manifest_sha256']==sha('build/aspect-compiler-expression/cases.json')
 assert expression['fragments_sha256']==sha('build/aspect-compiler-expression/tests/EXPRS.DAT')
 assert not expression['host_exception_edges']
 assert dos['DOS_summary']=='PROGRAM 1173 cases 0 failures' and dos['API_summary']=='API 1693 checks 0 failures'
 assert (dos['accepted'],dos['rejected'],dos['CLI_children'])==(718,455,11)
 assert dos['ownership_summary']=='OWNERSHIP 26 program and29 inventory failures,100 successful cycles'
 assert dos['fault_CLI_children']==2
 for name,digest in dos['fault_binaries'].items():assert sha('build/aspect-compiler-dos/tests/'+name)==digest
 for source,digest in dos['reused_sources'].items():assert sha(source)==digest,source
 assert dos['case_manifest_sha256']==sha('build/aspect-compiler-dos/cases.json')
 assert dos['runtime_child_sha256']==sha('build/aspect-runner/ASPECT.EXE')
 assert dos['runtime_asx_sha256']==sha('build/aspect-compiler-dos/tests/BUILD.ASX')
 oracle=read('standalone/fixtures/aspect_declaration_edges.json')
 assert oracle['compiler_sha256']=='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
 assert oracle['probe_sha256']==sha('standalone/probe_aspect_declaration_edges.py')
 assert len(oracle['vectors'])==2 and len(oracle['rejected'])==8
 assert sha(oracle['provenance']['report'])==oracle['provenance']['report_sha256']
 for v in oracle['vectors']+oracle['rejected']:assert hashlib.sha256(v['source'].encode('cp437')).hexdigest()==v['source_sha256']
 for v in oracle['vectors']:assert hashlib.sha256(bytes.fromhex(v['hex'])).hexdigest()==v['asx_sha256']
 for source,digest in unit['heap_observer_sources'].items():assert sha(source)==digest,source
 assert unit['reused_corpus_checker_sha256']==sha('standalone/check_aspect_compiler_lexer.py')
 crt=unit['isolated_CRT_probe'];assert crt['source_sha256']==sha('standalone/compiler_crt_heap_probe.c')
 assert crt['binary_sha256']==sha('build/aspect-compiler-unit/tests/CRTHEAP.EXE')
 assert 'independent_during0 independent_after0 used_during1 used_after0' in crt['summary']
 proof=read('docs/validation/application-components-source-build.json')
 assert proof['passed'] and proof['output_count']==153 and all(v['matches_workspace'] for v in proof['outputs'].values())
 for name,digest in binaries.items():assert proof['outputs'][name]['sha256']==digest
 # This chapter adds frontend tools and changes no application product bytes.
 prior=read('docs/validation/aspect-script-label.json')
 assert proof['outputs']['terminal/TERMINAL.EXE']['sha256']==prior['terminal_sha256']==sha('build/terminal/TERMINAL.EXE')
 assert proof['outputs']['aspect-runner/ASPECT.EXE']['sha256']==sha('build/aspect-runner/ASPECT.EXE')
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
  source_proof_sha256=sha('docs/validation/application-components-source-build.json'),reproduced_output_count=153,
  terminal_bytes_unchanged_from_prior_label_checkpoint=True,
  runtime_integration_validation='docs/validation/aspect-source-compile.json',
  CRT_analysis=dict(evidence_id='ev_d1a5f2f22b386770e1316405e3db283a854074f3496c79f5004bb421f01b9b66',
   target_sha256=hashlib.sha256(old).hexdigest(),current_runtime_probe_sha256=crt['binary_sha256'],identical_routine_sha256=hashlib.sha256(original_routine).hexdigest(),function='__HeapWalk',linear_address='0x10a0c',body_bytes=267,
   scope='REA/Ghidra static instructions plus separate owned malloc-only DOS execution. Pinned checker false failure; production allocator unchanged. Independent observer covers block/free-list/used-count structure and rejects six corruptions or capacity failures.'),
  native_declaration_oracle=dict(fixture_sha256=sha('standalone/fixtures/aspect_declaration_edges.json'),compiler_sha256=oracle['compiler_sha256'],probe_sha256=oracle['probe_sha256'],provenance=oracle['provenance'],accepted=2,rejected=8),
  compiler_stages_completed=['streaming lexical frontend','declaration/procedure inventory and owned source ranges','typed expression parsing and exact operand/assignment fragments with short-circuit DWORD patches','integer-only decimal to IEEE754 nearest/even conversion','complete maintained host statement/command grammar and typed procedure calls','validation of unused bodies/initializers and confirmed malformed declaration edges','iterative zero-reference pruning and complete ASX with DWORD patches beyond64KiB','DOS compiler CLI with staged output, replacement rollback and preserved source/existing output on tested failures','actual maintained DOS interpreter execution of DOS-compiled ASX'],
  required_remaining=['original compiler UI and broader lifecycle/physical compatibility beyond the separately tested runtime integration','full native compiler coverage beyond the host subset','recorder and remaining F01-F16 requirements'],
  limitations=['ASPLEX/ASPINV/ASPEXP remain diagnostics; ASPCOMP produces complete ASX only for the maintained host grammar.','Original ASPECT language families beyond the maintained subset remain unsupported.','Additional native malformed grammar edges still require independent evidence.','Physical hardware and modem compatibility are not established by these compiler tests.'],whole_application_gates_closed=[])
 (ROOT/'docs/validation/aspect-dos-compiler.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Bound DOS compiler:',dos['case_count'],'whole programs,',expression['case_count'],'expression fragments; full native language remains pending; source fallback is validated separately')
if __name__=='__main__':main()
