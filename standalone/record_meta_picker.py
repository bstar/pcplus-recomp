#!/usr/bin/env python3
"""Bind native picker traces, serviced DOS replay and isolated source rebuild."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','proof','capture','evidence','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT/'build');v=json.loads(path.read_text());assert v['passed'];receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in v['sources'].items():assert sha(ROOT/n)==h;sources[n]=h
  return v
 core=load(a.build.resolve()/'result.json');cold=load(a.proof.resolve()/'result.json');assert core['original_inputs']==cold['original_inputs']==[] and core['cpu']=='8086'
 assert core['native_cases']==99 and core['native_states']==2431 and 'PASS 28973 checks;' in core['transcript']
 assert sha(a.build.resolve()/'KEYPICK.EXE')==core['binary_sha256']==cold['binary_sha256'] and core['transcript']==cold['transcript'] and cold['source_count']==10 and cold['ancestor_git_unavailable']
 fixture=ROOT/'standalone/fixtures/meta_picker_native.json';native=json.loads(fixture.read_text());assert sha(fixture)==sha(a.capture.resolve()) and native['original_sha256']=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 evidence=a.evidence.resolve();assert evidence.is_relative_to(ROOT/'analysis');records={r['parameters'].get('procedure'):r for r in json.loads(evidence.read_text())['records'] if r['operation']=='analyze_function'};authority={}
 for name,at in [('dispatcher','0x1d0d0'),('redraw','0x1d304'),('selection','0x1d38a'),('scroll','0x1d3e9'),('sort','0x1d446'),('comparison','0x193de')]:
  r=records[at];assert r['subject']['digest']['sha256']=='fff9700d3b5e76b8f0d76c3a9df7051bfa39f87c0891bd593a8f84f19c758b19';authority[name]=dict(evidence_id=r['evidence_id'],address=at,body=r['normalized_result']['procedure']['body'])
 for n in ('standalone/record_meta_picker.py','standalone/prove_meta_picker_source.py','standalone/capture_meta_picker_original.py','docs/META_PICKER.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,component_only=True,installed_changed=False,terminal_changed=False,physical_runtime_verified=False,binary_sha256=core['binary_sha256'],checks=28973,native_cases=99,native_states=2431,state_bytes=20,table_bytes=9009,maintained_entry_capacity=1001,native_maximum_entries=350,maximum_comparisons_per_sort_step=64,isolated_source_files=10,original_inputs=[],native_authorities=authority,analyst_evidence_bundle_sha256=sha(evidence),sources=sources,receipts=receipts,
 limitations=['Original overlay1/shared picker and CRT instructions replay with synthetic enumeration and modeled formatting/window/keyboard/bell boundaries. Static synthetic image never executed; no native DOS/BIOS/VGA/hardware acceptance.', 'Native traces cover distinct stems/counts1..350, mixed case/punctuation/high CP437 bytes. Stable maintained sort is not recovered original code;1001-entry coverage is source-only, not original capacity parity.', 'Actual DOS enumeration/DTA and canonical resource search, modal ownership/restoration, missing-file creation, persistence/adoption/quarantine, parent scheduling/memory/capacity/BBS/physical acceptance remain open. Installed RCE81708 unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS Meta picker receipt:99 cases,2431 states/views,28973 checks,10-file source rebuild')
if __name__=='__main__':main()
