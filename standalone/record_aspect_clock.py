#!/usr/bin/env python3
"""Bind native clock recovery, source compiler/VM, memory funding and BBS gates."""
import argparse,json,struct
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={}
 def load(name,positive=True):
  path=ROOT/name;r=json.loads(path.read_text());assert r.get('passed',True)==positive,name;receipts[name]=sha(path)
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n;sources[n]=h
  return r
 def product(folder,leaf):
  path=ROOT/folder/leaf;m=load(folder+'/manifest.json');assert sha(path)==m['binary_sha256'] and not m['original_inputs'];return sha(path)
 matched=product('build/aspect-clock-compact-final-20261106','ASPECT.EXE');ordinary=product('build/aspect-runner','ASPECT.EXE');compiler=product('build/aspect-compiler-dos','ASPCOMP.EXE')
 native=load('build/aspect-clock-native-final-20261106/result.json');clean=load('build/aspect-clock-source-only-native-20261106/result.json')
 assert native['cases']==native['original_comparisons']==clean['cases']==477 and clean['original_comparisons']==0 and native['new_native_bytes']==171 and native['native_bytes']==274
 for r in (native,clean):
  for u in r['units']:assert sha(ROOT/u['output'])==u['sha256']
 grammar=ROOT/'standalone/fixtures/aspect_clock_compiler_vectors.json';g=json.loads(grammar.read_text());assert len(g['cases'])==161 and sum(c['success'] for c in g['cases'])==27
 assert sha(ROOT/'standalone/probe_aspect_clock_compiler.py')==g['probe_sha256']
 cc=load('build/aspect-compiler-dos/checks.json');assert cc['case_count']==2186 and cc['accepted']==1086 and cc['rejected']==1100 and cc['binary_sha256']==compiler and cc['runtime_child_sha256']==ordinary and cc['host_compiler_sha256']==sha(ROOT/'src/aspect/compiler.py')
 vm=load('build/aspect-runtime/checks.json');assert vm['supported_slot_count']==107 and vm['DOS_summary']=='ASPECT_RUNTIME 1123 cases 26986 checks 0 failures'
 dos=load('build/aspect-clock-dos-compact-accepted-20261106/result.json');assert dos['cases']==372 and dos['checks']==7275 and dos['same_process_rounds']==31
 assert dos['products']['build/aspect-runner/ASPECT.EXE']==ordinary and dos['products']['build/aspect-compiler-dos/ASPCOMP.EXE']==compiler
 for n,h in dos['artifacts'].items():assert sha(ROOT/'build/aspect-clock-dos-compact-accepted-20261106'/n)==h,n
 cold=load('build/aspect-clock-cold-source-20261106/result.json');assert cold['DOS_cases']==372 and cold['DOS_checks']==7275 and cold['source_files']==5339 and not cold['original_inputs']
 assert cold['products']=={'aspect-clock-compact-final-20261106':matched,'aspect-runner':ordinary,'aspect-compiler-dos':compiler}
 for n,h in cold['overlay_sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 parent=load('build/aspect-clock-parent-clock-final-20261106/result.json');negative=load('build/aspect-clock-full-control-final-20261106/result.json',False)
 assert parent['interpreter_sha256']==matched and len(parent['checks'])==26 and all(parent['checks'].values()) and parent['clock_queries'] and parent['nested_child_count']==3
 assert negative['binary_sha256']==parent['binary_sha256'] and negative['clock_queries'] and negative['checks']['actual_parent_clock_queries']
 assert {n for n,v in negative['checks'].items() if not v}=={'all_six_streams','six_files','three_nested_children','exact_viewport_cells'}
 control=product('build/aspect-clock-full-table-control-20261106','ASPECT.EXE');assert control==negative['interpreter_sha256']
 def allocation(path):
  h=struct.unpack_from('<14H',path.read_bytes());return (h[2]-1)*512+(h[1] or 512)-h[4]*16+h[5]*16+256
 baseline=ROOT/'build/chat-echo-label-final-aspect-20261106/ASPECT.EXE';assert sha(baseline)=='cbdee1949f0ac6bba34f56ae9c594a17888ef9b5143ee5dca9cd76498737ccfd'
 minimum=allocation(ROOT/'build/aspect-clock-compact-final-20261106/ASPECT.EXE');assert minimum==131310 and minimum-allocation(baseline)==16
 maptext=(ROOT/'build/aspect-clock-compact-final-20261106/ASPECT.map').read_text();assert '0000:8e73      aspect_set_resolve' in maptext
 for name in ('build/aspect-set/checks.json','build/aspect-fetch-native/checks.json','build/aspect-clock-compact-formats-20261106/checks.json'):load(name)
 sync=load('build/bbs-lab/results/synchronet/aspect-clock-sync-20261106/proxy-integration.json');assert sync['binary_sha256']==parent['binary_sha256'] and sync['interpreter_sha256']==matched and all(sync['checks'].values())
 carrier=load('build/bbs-lab/results/enigma/aspect-clock-carrier-rotating-20261106/carrier-checks.json');audit=load('build/aspect-clock-carrier-audit-20261106/result.json')
 assert carrier['products']['TERMINAL.EXE']['sha256']==parent['binary_sha256'] and carrier['products']['ASPECT.EXE']['sha256']==matched and carrier['products']['ASPCOMP.EXE']['sha256']==compiler and not carrier['errors'] and all(carrier['checks'].values())
 assert audit['exact_retry_bytes']==65539
 journal=load('build/aspect-clock-journal-controls-20261106/result.json');assert journal['case_count']==13
 for n,h in journal['inputs'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 controls=load('build/aspect-clock-journal-copy-controls-20261106/result.json')
 assert len(controls['cases'])==5 and all(c['passed'] and c['rejected']==(c['case']!='unchanged') for c in controls['cases'])
 assert controls['original_capture_sha256']==sha(ROOT/'build/bbs-lab/results/enigma/aspect-clock-carrier-rotating-20261106/carrier-checks.json')
 for n,h in audit['captures'].items():assert sha(ROOT/n)==h,n
 sources['standalone/record_aspect_clock.py']=sha(Path(__file__))
 report=dict(passed=True,products=dict(terminal=parent['binary_sha256'],ASPECT_matched=matched,ASPECT_standalone=ordinary,ASPCOMP=compiler),sources=sources,receipts=receipts,
  summary=dict(new_native_bytes=171,reused_native_bytes=103,native_cases=477,original_CRT_comparisons=477,original_compiler_sources=161,original_compiler_accepted=27,original_compiler_rejected=134,DOS_compiler_cases=2186,DOS_clock_runs=372,DOS_clock_checks=7275,VM_cases=1123,VM_checks=26986,supported_slots=107,unsupported_slots=108,compact_SET_index_bytes=87,compact_SET_pointer_bytes=28,old_SET_table_bytes=512,minimum_module_bytes=minimum,minimum_growth_bytes=16,parent_clock_and_capacity_checks=26,cold_source_files=5339,journal_controls=13,journal_bad_copy_controls=4),
  limitations=['Native source CPU formatting/operand/DOS boundaries are modeled; optional original replay executes original resident CRT but models DOS clock/operand admission. Actual DOS/VM tests are separate.',
   'Full-table control reproduces a parent child/state failure with six streams; not an exhaustive attribution of every native memory/error path.',
   'BBS regressions exercise the new interpreter/compiler in existing login/transfer/editor workflows, not DATE/TIME in a BBS login script. Parent clock queries tested separately over a synthetic modem.',
   'No installed-package selection, physical machine update or Boca/SPA2102/SIP/audio acceptance. Full ASPECT/emulations/protocols/Host and application parity remain open.'],
  scope=__doc__+' Exact native DATE/TIME bodies with existing helpers; compact private formatter and separately maintained bounded shared SET/FETCH resolver fund runtime capacity. No stack/heap-growth/stream/buffer reduction. Source-only products and cold rebuild; parent local clock strings survive nested children, six-stream recovery retained. Physical release stays unchanged.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS native DATE/TIME, compact dispatch and current BBS acceptance')
if __name__=='__main__':main()
