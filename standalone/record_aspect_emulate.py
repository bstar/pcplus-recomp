#!/usr/bin/env python3
"""Bind EMULATE native recovery and compiler fidelity; runtime integration remains open."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={}
 def load(name):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed'],name;receipts[name]=sha(path)
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n;sources[n]=h
  return r
 test=load('build/emulate-compiler-20261107/result.json');cold=load('build/emulate-compiler-cold-20261107/result.json')
 full=load('build/aspect-compiler-dos/checks.json');stack=load('build/emulate-compiler-stack-20261107/stack-checks.json')
 native=load('build/emulate-native-final-20261107/result.json');original=load('build/emulate-native-original-final-20261107/result.json')
 binary=sha(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE')
 assert binary==test['binary_sha256']==cold['binary_sha256']==full['binary_sha256']==stack['compiler_sha256']
 assert test['original_cases']==test['presentation_cases']==98 and len(test['cases'])==196
 assert test['accepted']==72 and test['rejected']==124
 for n,h in test['captures'].items():assert sha(ROOT/'build/emulate-compiler-20261107'/n)==h,n
 assert cold['source_files']==25 and cold['cases']==196
 repeated=ROOT/'build/emulate-compiler-cold-20261107/source/build/tests/result.json'
 assert sha(repeated)==cold['test_result_sha256'] and json.loads(repeated.read_text())['cases']==test['cases']
 assert full['case_count']==2323 and full['API_summary']=='API 1693 checks 0 failures'
 assert sha(ROOT/'build/aspect-compiler-dos/manifest.json')==full['manifest_sha256']
 assert sha(ROOT/'build/aspect-compiler-dos/cases.json')==full['case_manifest_sha256']
 for n,h in {**full['fixture_sources'],**full['reused_sources']}.items():assert sha(ROOT/n)==h,n;sources[n]=h
 assert stack['corpus_cases']==2341 and stack['checked_CLI_cases']==18
 assert stack['candidate_CLI_stack_bytes']==stack['checked_CLI_stack_bytes']==24576 and stack['checked_API_stack_bytes']==16384
 for n,h in [('standalone/check_aspect_compiler_dos.py',full['checker_sha256']),('src/aspect/compiler.py',full['host_compiler_sha256']),('standalone/check_aspect_compiler_stack.py',stack['checker_sha256'])]:assert sha(ROOT/n)==h,n;sources[n]=h
 assert stack['reused_corpus_checker_sha256']==full['checker_sha256']
 assert native['cases']==original['cases']==768 and native['native_bytes']==15
 assert not native['original_inputs'] and original['optional_original'] and len(original['original_inputs'])==1
 assert native['binary_sha256']==original['binary_sha256']=='e6d7360b2eaabb705a1e28786e80cd5d3c4e5729e5eb7e27e1387087e30536d2'
 for n in ('standalone/probe_aspect_emulate_compiler.py','standalone/freeze_aspect_emulate_compiler.py','standalone/record_aspect_emulate.py'):sources[n]=sha(ROOT/n)
 fixture=json.loads((ROOT/'standalone/fixtures/aspect_emulate_compiler_vectors.json').read_text())
 assert fixture['probe_sha256']==sources['standalone/probe_aspect_emulate_compiler.py'] and fixture['freezer_sha256']==sources['standalone/freeze_aspect_emulate_compiler.py']
 result=dict(passed=True,sources=sources,receipts=receipts,compiler_sha256=binary,native_sha256=native['binary_sha256'],
  summary=dict(original_grammar_cases=98,host_and_DOS_cases=196,full_DOS_corpus=2323,API_checks=1693,checked_stack_cases=2341,cold_source_files=25,native_cases=768,native_bytes=15),
  original_inputs=[],installed_changed=False,runtime_opcode_integrated=False,
  limitations=['Compiler emits all33 original named selectors; this does not implement33 terminal emulations. Numeric/variable selectors reject.',
   'Native byte-reader and full-reset callbacks are models. Exact15-byte owner writes selector before reset(1); reset-error stop does not prove recovery. No parent/renderer/key-profile integration or DOS command execution.',
   'Cold export repeats196 compiler cases and exact executable, not full2323/2341 suites or native replay. Optional native comparison reads original only outside normal builds.',
   'Installed parent689/ASPECTb4f0/compilerc261 package remains unchanged. New compilerac58 is not selected or deployed. Physical acceptance and full parity remain open.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS EMULATE recovery/compiler checkpoint',result['summary'])
if __name__=='__main__':main()
