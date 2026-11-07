#!/usr/bin/env python3
"""Bind ALARM host/DOS emission, full compiler regression and cold reproduction."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('test','cold','stack','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path):
  report=json.loads(path.read_text());assert report['passed'],str(path);receipts[str(path.relative_to(ROOT))]=sha(path)
  for name,digest in report.get('sources',{}).items():
   assert sha(ROOT/name)==digest,name
   if name in sources:assert sources[name]==digest,name
   sources[name]=digest
  return report
 test=a.test.resolve();cold=a.cold.resolve();stack=a.stack.resolve()
 t=load(test/'result.json');c=load(cold/'result.json');s=load(stack/'stack-checks.json')
 folder=ROOT/'build/aspect-compiler-dos';reg=load(folder/'checks.json');manifest=json.loads((folder/'manifest.json').read_text())
 assert sha(folder/'manifest.json')==reg['manifest_sha256']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest and sources[name]==digest,name
 binary=sha(folder/'ASPCOMP.EXE');assert binary==t['binary_sha256']==c['binary_sha256']==reg['binary_sha256']==s['compiler_sha256']
 assert reg['host_compiler_sha256']==sha(ROOT/'src/aspect/compiler.py')
 for name,digest in reg['fixture_sources'].items():assert sha(ROOT/name)==digest,name;sources[name]=digest
 for name,digest in reg['reused_sources'].items():assert sha(ROOT/name)==digest,name;sources[name]=digest
 for name,key in [('standalone/check_aspect_compiler_dos.py','checker_sha256')]:assert sha(ROOT/name)==reg[key];sources[name]=reg[key]
 assert sha(ROOT/'standalone/check_aspect_compiler_stack.py')==s['checker_sha256'];sources['standalone/check_aspect_compiler_stack.py']=s['checker_sha256']
 assert s['reused_corpus_checker_sha256']==reg['checker_sha256']
 assert reg['case_count']==2225 and reg['API_summary']=='API 1693 checks 0 failures'
 assert s['corpus_cases']==2243 and s['checked_CLI_cases']==18
 assert s['candidate_CLI_stack_bytes']==s['checked_CLI_stack_bytes']==24576 and s['checked_API_stack_bytes']==16384
 assert t['original_cases']==39 and t['presentation_cases']==39 and t['DOS_children']==78 and len(t['cases'])==78
 assert sum(r['accepted'] for r in t['cases'])==t['accepted']==34
 assert t['rejected']==44 and c['cases']==78 and c['source_files']==len(c['sources'])==24
 for name,digest in t['captures'].items():assert sha(test/name)==digest,name
 assert sha(cold/'source/build/tests/result.json')==c['test_result_sha256']
 repeated=json.loads((cold/'source/build/tests/result.json').read_text());assert repeated['passed'] and repeated['cases']==t['cases']
 assert sha(folder/'cases.json')==reg['case_manifest_sha256']
 records=json.loads((folder/'cases.json').read_text())
 for row in t['cases']:
  found=[r for r in records if r['source_sha256']==row['source_sha256']]
  if row['variant']=='original':
   assert len(found)==1 and found[0]['accepted']==row['accepted']
   if row['accepted']:assert found[0]['asx_sha256']==row['output_sha256']
 sources['standalone/record_aspect_alarm_compiler.py']=sha(Path(__file__))
 report=dict(passed=True,sources=sources,receipts=receipts,binary_sha256=binary,
  summary=dict(original_grammar_cases=39,host_and_DOS_cases=78,accepted=34,rejected=44,full_DOS_corpus=2225,API_checks=1693,checked_stack_cases=2243,cold_source_files=24,cold_repeated_cases=78),original_inputs=[],
  limitations=['Compiler grammar/emission only: ALARM opcode still lacks maintained VM, parent policy and WHEN/renderer integration.',
   'Negative signed operands compile as in original; runtime0..32767 bounds remain a separate integration requirement. FOREVER is an ordinary integer builtin, not a WAITFOR timeout marker.',
   'Cold proof repeats78 ALARM cases, not the complete2225-case corpus or2243-case stack suite. Pinned Nix environment supplied by caller.',
   'No installed package, physical acceptance, private state, BBS or bridge changes.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS ALARM compiler checkpoint',report['summary'])
if __name__=='__main__':main()
