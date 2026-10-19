#!/usr/bin/env python3
"""Freeze original compiler directory grammar with independent synthetic metadata."""
import json
from pathlib import Path
from aspect_directory_probe import ROOT, COMPILER, corpus, sha
REPORT='analysis/aspect-directory/compiler-03/report.json'
REPORT_SHA='1295f4e13b2cb4a817c60fa45c4f1e0084bd8362595c8cb09f56c473661163ce'
def main():
 raw=(ROOT/REPORT).read_bytes();assert sha(raw)==REPORT_SHA
 report=json.loads(raw);assert report['compiler_sha256']==COMPILER
 assert report['harness_sha256']==sha((ROOT/'standalone/aspect_directory_probe.py').read_bytes())
 authored=corpus();vectors=[];compiler_only=[];rejected=[]
 for case in report['cases']:
  assert case['source']==authored[case['name']]['source']
  assert sha(case['source'].encode('cp437'))==case['source_sha256']
  if not case['success']:
   rejected.append({key:case[key] for key in ['name','source','source_sha256','errors']});continue
  assert sha(bytes.fromhex(case['hex']))==case['asx_sha256']
  prediction=authored[case['name']];assert prediction['expected'] is not None
  v={key:case[key] for key in ['name','source','source_sha256','hex','asx_sha256']}
  v.update(source_encoding='cp437',directory=prediction['directory'],expected=prediction['expected'])
  if case['name']=='DIRTX':v['serial']=dict(enabled=True,input_hex='',send_after_tx_hex='',case_sensitive=False)
  if prediction['compiler_only']:
   v.update(dos_excluded=True,dos_excluded_reason='BAUD long0 original getter indexes global DWORD baud table3270 using record.word46; native service/table not bound by this directory snapshot phase.')
   compiler_only.append(v)
  else:vectors.append(v)
 assert len(vectors)==18 and len(compiler_only)==1 and len(rejected)==26
 out=dict(compiler_sha256=COMPILER,private_report=REPORT,private_report_sha256=sha(raw),probe_sha256=report['harness_sha256'],freezer_sha256=sha(Path(__file__).read_bytes()),vectors=vectors,compiler_only=compiler_only,rejected=rejected,
  expectation_model='Hand-derived before composed VM execution from synthetic114B record and selected entry7. String slots0..7 point to record offsets61,95,86,0,105,25,75,52. Importantly KBDFILE1 uses95 and METAKEY2 uses86, despite potential editor-label assumptions. Entry3 reads selected entry independently of record bytes. Password is explicit script operand, not automatic transmission. No directory username builtin inferred. BAUD emits long0 but remains compile-only pending table binding.',
  native_evidence=['analysis/aspect-directory/original-getters-01.json:24 original getter executions, empty/max/CP437 synthetic fields','Original overlay16 D9B5..D9B9 selected entry;DAA2..DAC2 eight string getter bodies; compiler03 exact6E/6F/70 typed selectors'],
  prior_report=dict(path='analysis/aspect-directory/compiler-01/report.json',sha256='eca5b888c68103f4b9c9929634a79e858a5d1a57bce9724c1333fe535a6f07dd',attempts=17,accepted=13),
  scope='45 original compiler attempts19 accepted26 rejected;18 authored metadata runtime vectors1 compiler-only. Normal compiler/tests use frozen authored data and source only. No private directory/configuration, automatic credential transmission, username alias, or full application claim.')
 target=ROOT/'standalone/fixtures/aspect_directory_vectors.json';target.write_text(json.dumps(out,indent=2)+'\n');print(target.relative_to(ROOT),sha(target.read_bytes()))
if __name__=='__main__':main()
