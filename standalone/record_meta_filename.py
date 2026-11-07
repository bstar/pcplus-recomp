#!/usr/bin/env python3
"""Bind serviced filename-field, file composition and original analysis evidence."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','proof','evidence','capture','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT/'build');v=json.loads(path.read_text());assert v['passed'];receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in v['sources'].items():assert sha(ROOT/n)==h;sources[n]=h
  return v
 core=load(a.build.resolve()/'result.json');cold=load(a.proof.resolve()/'result.json')
 assert core['original_inputs']==cold['original_inputs']==[] and core['cpu']=='8086' and core['native_cases']==314 and core['native_states']==1304
 assert sha(a.build.resolve()/'KEYNAME.EXE')==core['binary_sha256']==cold['binary_sha256'] and core['transcript']==cold['transcript'] and 'PASS 5555 checks;' in core['transcript']
 assert cold['source_count']==23 and cold['ancestor_git_unavailable']
 fixture=ROOT/'standalone/fixtures/meta_filename_native.json';v=json.loads(fixture.read_text());assert sha(a.capture.resolve())==sha(fixture) and v['original_sha256']=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 evidence=a.evidence.resolve();assert evidence.is_relative_to(ROOT/'analysis');bundle=json.loads(evidence.read_text());records={r['evidence_id']:r for r in bundle['records']}
 authorities={}
 for label,address,key in [('load','0x1e0d0',v['REA_load']),('save','0x1e16e',v['REA_save']),('callback','0x14aa7',v['REA_callback']),('normalize','0x1e18a','ev_3c4203cbaaf4ae88d584aabfab5ca1e9c4e9c6c907a5638830cc6eeb55dabc8c'),('picker','0x1d0d0','ev_b5f69bd5a2bcae47a2d2777f8bc324e0ad53ef9a36ba2106d466fe481c9e462d')]:
  r=records[key];assert r['operation']=='analyze_function' and r['normalized_result']['procedure']['address']==address and r['subject']['digest']['sha256']=='fff9700d3b5e76b8f0d76c3a9df7051bfa39f87c0891bd593a8f84f19c758b19';authorities[label]=dict(evidence_id=key,address=address,body=r['normalized_result']['procedure']['body'])
 for n in ('standalone/record_meta_filename.py','standalone/prove_meta_filename_source.py','standalone/capture_meta_filename_original.py','docs/META_FILENAMES.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,component_only=True,installed_changed=False,terminal_changed=False,physical_runtime_verified=False,binary_sha256=core['binary_sha256'],checks=5555,native_cases=314,native_states=1304,field_state_bytes=22,prompt_state_bytes=92,isolated_source_files=23,original_inputs=[],sources=sources,receipts=receipts,native_authorities=authorities,analyst_evidence_bundle_sha256=sha(evidence),
 limitations=['Native filename instruction replay uses synthetic bytes and modeled keyboard/render/cursor/bell services; static synthetic image never executed. Ordinary builds use frozen traces, not original executables.', 'Actual checked DOS files composed with serviced dialog/prompt under a fixture resource resolver. Picker completion modeled; enumeration/sort/viewport UI is still missing.', 'Original higher-level load/default/create policy, resource lookup/claims, file/EXEC admission, quarantine/live adoption, scheduling, native VGA, application memory/capacity/BBS/physical acceptance remain open. Installed RCE81708 unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS Meta filename receipt:314 cases,1304 states,5555 checks,23-file source rebuild')
if __name__=='__main__':main()
