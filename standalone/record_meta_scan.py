#!/usr/bin/env python3
"""Bind actual DOS KEY enumeration, failure composition and source-only replay."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','proof','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT/'build');v=json.loads(path.read_text());assert v['passed'];receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in v['sources'].items():assert sha(ROOT/n)==h;sources[n]=h
  return v
 core=load(a.build.resolve()/'result.json');cold=load(a.proof.resolve()/'result.json')
 assert core['original_inputs']==cold['original_inputs']==[] and core['cpu']=='8086' and core['unchanged_files']==1009
 assert 'PASS 137372 checks; scan state 130 bytes;' in core['transcript'] and core['transcript']==cold['transcript']
 assert sha(a.build.resolve()/'KEYSCAN.EXE')==core['binary_sha256']==cold['binary_sha256'] and cold['source_count']==16 and cold['ancestor_git_unavailable']
 assert core['scanner_owned_DGROUP_bytes']==0
 for segments in core['scanner_owned_segments'].values():assert all(n=='_TEXT' or not size for n,size in segments.items())
 for n in ('standalone/record_meta_scan.py','standalone/prove_meta_scan_source.py','docs/META_PICKER_SCAN.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,component_only=True,installed_changed=False,terminal_changed=False,physical_runtime_verified=False,binary_sha256=core['binary_sha256'],assertions=137372,scan_state_bytes=130,scanner_owned_DGROUP_bytes=0,scanner_owned_segments=core['scanner_owned_segments'],unchanged_fixture_files=1009,isolated_source_files=16,maximum_find_calls_per_step=1,maximum_sort_comparisons_per_step=64,entry_limit=1001,declared_fault_modes=6,original_inputs=[],sources=sources,receipts=receipts,
 limitations=['Actual source-built DOS8086 FindFirst/Next over owned fixtures, including interleaved separate find context and per-step DTA sentinels. Six declared wrapper modes inject IO errors/malformed/ineligible records; not observed hardware faults.', 'Assertion count includes each sentinel byte and file-list membership check, not independent scenario count. Maintained enumeration, not an original-binary comparison.', 'Explicit absolute ASCII DOS83 pattern only; CP437 stems retained. Resource fallback/claims and file/EXEC admission remain open. Limit means collection stopped at cap; does not itself establish additional matches.', 'No modal/terminal integration, missing-file defaults/create, checked adoption/quarantine, parent memory/capacity/BBS or physical acceptance. Installed RCE81708 unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS Meta enumeration receipt:137372 assertions,1009 files,zero scanner-owned DGROUP,16-file source rebuild')
if __name__=='__main__':main()
