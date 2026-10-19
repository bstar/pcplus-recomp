#!/usr/bin/env python3
"""Publish only authored script source/compiled fixtures, never compiler bytes."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 rel='analysis/aspect-vm-runtime/execution-04/report.json';path=ROOT/rel;r=json.loads(path.read_text())
 assert r['compiler_sha256']==SHA and r['harness_sha256']==sha((ROOT/'standalone/aspect_execution_probe.py').read_bytes())
 assert len(r['cases'])==19 and all(c['success'] for c in r['cases'])
 vectors=[]
 for c in r['cases']:
  data=bytes.fromhex(c['hex']);source=c['source'].encode('ascii')
  assert sha(source)==c['source_sha256'] and sha(data)==c['asx_sha256']
  assert data==(path.parent/(c['name']+'.ASX')).read_bytes()
  vectors.append({k:c[k] for k in ['name','source','source_sha256','hex','asx_sha256','expected']})
 report=dict(compiler_sha256=SHA,private_report=rel,private_report_sha256=sha(path.read_bytes()),
  probe_sha256=r['harness_sha256'],freezer_sha256=sha(Path(__file__).read_bytes()),vectors=vectors,
  scope='Source-owned script source and original-compiler-produced ASX fixture bytes only. No original compiler/application/resources; normal builds do not need originals.')
 out=ROOT/'standalone/fixtures/aspect_execution_vectors.json';out.write_text(json.dumps(report,indent=2)+'\n');print(out.relative_to(ROOT))
if __name__=='__main__':main()
