#!/usr/bin/env python3
"""Bind checked KEY ownership, declared failures and isolated DOS replay."""
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
 assert core['original_inputs']==cold['original_inputs']==[] and core['cpu']=='8086' and core['process_cases']==21 and core['owner_state_bytes']==1518
 assert sha(a.build.resolve()/'KEYOWN.EXE')==core['binary_sha256']==cold['binary_sha256'] and core['logs']==cold['logs'] and cold['source_count']==28 and cold['ancestor_git_unavailable']
 assert core['logs']['0'].startswith('PASS 597 checks;') and all(v.startswith('PASS') for v in core['logs'].values()) and core['owner_owned_DGROUP_bytes']==0
 assert all(n=='_TEXT' or not size for n,size in core['owner_owned_segments'].items())
 provenance=ROOT/'reconstruction/meta_editor/provenance.json';native=json.loads(provenance.read_text());default=native['ranges'][0];assert native['original_sha256']=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904' and default['name']=='defaults' and default['bytes']==23
 for n in ('standalone/record_meta_owner.py','standalone/prove_meta_owner_source.py','docs/META_KEY_OWNER.md','reconstruction/meta_editor/provenance.json'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,component_only=True,installed_changed=False,terminal_changed=False,physical_runtime_verified=False,binary_sha256=core['binary_sha256'],process_cases=21,normal_assertions=597,owner_state_bytes=1518,owner_owned_DGROUP_bytes=0,owner_owned_segments=core['owner_owned_segments'],isolated_source_files=28,logs=core['logs'],original_inputs=[],default_authority=dict(original_sha256=native['original_sha256'],range=default,reused_not_new_instruction_replay=True),sources=sources,receipts=receipts,
 limitations=['Actual DOS KEY IO and capture reservation library with declared filesystem/lease-release faults over owned scratch files. HELD cases run in separate processes; test-only handle/scratch cleanup is not product recovery.', 'In-process target/stage/backup reservations and local EXEC predicate, not external locks or global terminal/EXEC admission. Bind preserves active edits; only explicit Load replaces its supplied destination. Native broader failure/default behavior is not claimed.', 'No live action adoption, modal/transient residency, application memory/capacity/UART/BBS or physical acceptance. Callback/state must remain alive until successful end or return to DOS. Installed RCE81708 unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS KEY owner receipt:21 DOS cases,597 normal assertions,28-file rebuild,zero owner-owned DGROUP')
if __name__=='__main__':main()
