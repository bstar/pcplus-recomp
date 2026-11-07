#!/usr/bin/env python3
"""Freeze authored EMULATE compiler outcomes; no proprietary compiler input."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 path=ROOT/'analysis/aspect-compiler/emulate-grammar-full-20261107/fixture.json'
 assert sha(path.read_bytes())=='3e7d23394a36631df90476d373d302b8519bafa37839581bce2a37364386b13d'
 oracle=json.loads(path.read_text())
 assert sha((ROOT/'standalone/probe_aspect_emulate_compiler.py').read_bytes())==oracle['probe_sha256']
 assert oracle['compiler_sha256']=='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
 accepted,rejected=[],[]
 for case in oracle['cases']:
  assert sha(case['source'].encode('cp437'))==case['source_sha256']
  vector={n:case[n] for n in ('label','source','source_sha256')}
  if case['success']:
   vector.update(hex=case['hex'],asx_sha256=sha(bytes.fromhex(case['hex'])));accepted.append(vector)
  else:rejected.append(vector)
 assert len(accepted)==36 and len(rejected)==62
 report=dict(schema='aspect-emulate-compiler-v1',compiler_sha256=oracle['compiler_sha256'],
  oracle_sha256=sha(path.read_bytes()),probe_sha256=oracle['probe_sha256'],freezer_sha256=sha(Path(__file__).read_bytes()),
  source_encoding='cp437',vectors=accepted,rejected=rejected,
  scope='Authored EMULATE grammar/emission only. No runtime execution or full compiler parity claim; originals are not normal build inputs.')
 (ROOT/'standalone/fixtures/aspect_emulate_compiler_vectors.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Frozen36 accepted and62 rejected EMULATE original-compiler outcomes')
if __name__=='__main__':main()
