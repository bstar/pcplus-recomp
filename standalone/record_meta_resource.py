#!/usr/bin/env python3
"""Bind canonical KEY resource selection, composed IO and isolated replay."""
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
 assert core['original_inputs']==cold['original_inputs']==[] and core['cpu']=='8086' and 'PASS 699 checks;' in core['transcript'] and core['transcript']==cold['transcript']
 assert sha(a.build.resolve()/'KEYRES.EXE')==core['binary_sha256']==cold['binary_sha256'] and cold['source_count']==28 and cold['ancestor_git_unavailable']
 assert core['resource_owned_DGROUP_bytes']==0 and all(n=='_TEXT' or not size for n,size in core['resource_owned_segments'].items())
 for n in ('standalone/record_meta_resource.py','standalone/prove_meta_resource_source.py','docs/META_KEY_RESOURCES.md'):sources[n]=sha(ROOT/n)
 result=dict(passed=True,component_only=True,installed_changed=False,terminal_changed=False,physical_runtime_verified=False,binary_sha256=core['binary_sha256'],assertions=699,result_bytes=74,resource_owned_DGROUP_bytes=0,resource_owned_segments=core['resource_owned_segments'],isolated_source_files=28,declared_fault_modes=5,original_inputs=[],sources=sources,receipts=receipts,
 limitations=['Actual source-built DOS canonicalization/attributes, real picker scans, bounded synthetic PSP/environment and checked frozen-path IO over owned fixtures. Maintained lookup policy, not native whole-workflow comparison.', 'ASCII DOS83 paths and63-byte identity/53-byte parent limits. Only absence enables bare-name PCPLUS fallback; qualified requests remain explicit. MISSING supplies context, not create authorization or a claim.', 'Canonical paths are not external locks/host-inode identities. File/EXEC claims, defaults/create, baseline/live adoption/recovery, modal/transient integration, memory/capacity/UART/BBS/physical acceptance remain open. Installed RCE81708 unchanged.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS KEY resource receipt:699 assertions,28-file source rebuild,frozen load/save,zero resource-owned DGROUP')
if __name__=='__main__':main()
