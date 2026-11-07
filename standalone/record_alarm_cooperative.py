#!/usr/bin/env python3
"""Bind cooperative native-alert ownership tests and cold source reproduction."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={}
 def load(name):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed'],name;receipts[name]=sha(path)
  for n,h in r['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
  return r
 dos=load('build/alarm-cooperative-dos-final-20261106/result.json')
 cold=load('build/alarm-cooperative-cold-source-20261106/result.json')
 native=load('docs/validation/aspect-alarm-native.json')
 assert dos['cases']==cold['cases']==94 and dos['checks']==cold['checks']==1701 and cold['source_files']==8
 assert native['cases']==348 and native['native_bytes']==120
 assert cold['binary_sha256']==sha(ROOT/'build/alarm-cooperative-dos-final-20261106/ALARM.EXE')
 for n,h in dos['artifacts'].items():assert sha(ROOT/'build/alarm-cooperative-dos-final-20261106'/n)==h,n
 oracle=ROOT/'analysis/aspect-compiler/alarm-grammar-full-20261106/fixture.json';grammar=json.loads(oracle.read_text())
 assert len(grammar['cases'])==39 and sum(c['success'] for c in grammar['cases'])==17
 assert sha(ROOT/'standalone/probe_aspect_alarm_compiler.py')==grammar['probe_sha256']
 sources['standalone/probe_aspect_alarm_compiler.py']=grammar['probe_sha256']
 sources['standalone/record_alarm_cooperative.py']=sha(Path(__file__))
 report=dict(passed=True,binary_sha256=cold['binary_sha256'],sources=sources,receipts=receipts,
  summary=dict(DOS_cases=94,DOS_checks=1701,cold_source_files=8,native_baseline_cases=348,native_bytes=120),
  original_grammar=dict(cases=39,accepted=17,rejected=22,fixture_sha256=sha(oracle),compiler_sha256=grammar['compiler_sha256'],probe_sha256=grammar['probe_sha256']),
  limitations=['Actual recovered native alert and C/RET2/RET4 bridge execute under DOS8086, but platform clock/keyboard/service/speaker callbacks are modeled.',
   'No actual UART receive, PIT/acoustic timing, VM opcode binding, parent PRM policy or physical machine acceptance.',
   'Tone duration15 uses a maintained3-BIOS-tick request. Keys can end an active tone early; this is a cooperative cancellation adaptation.',
   'Original grammar is independently captured; maintained host/DOS compiler emission remains unimplemented at this checkpoint.',
   'Callback context/ownership/lifetime contracts remain the platform adapter responsibility. Failed cleanup retains borrowed ops/cookie until explicit successful recovery.',
   'No selected package, installed files, machine configuration or running BBS/bridge changes.'],
  scope=__doc__+' Exact native93-byte shared alert retained, synchronous services replaced by bounded foreground callbacks. Error termination does not invent or consume a key. Reentrant run/recovery rejected; owned sound cleanup failures remain quarantined for retry. Full application integration and parity stay open.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS cooperative native alarm and cold DOS source receipt')
if __name__=='__main__':main()
