#!/usr/bin/env python3
"""Optional freeze of authored original EXECUTE grammar; CHAIN is not a keyword."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
COMPILER='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
REPORTS=[('01','b42d0060a95c19b8fef8bfccb66e777c747a3c86968f23d4e8a94556d2bae760','compiler_probe.py','1653790dbc37374a25e721bed7eda656d19b24e5993473508bbb6ff748b5ae6a'),('02','79c60754e1a71819f911096cfdcecdf04f8d64dab5459a1d31f56c8e2e43028d','compiler_probe02.py','5716103b7155d27087db2ea4bf15e72b37b0aab8529f0da22202372303fa49dd')]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 yes=[];no=[];provenance=[]
 for number,digest,probe,pdigest in REPORTS:
  name=f'analysis/aspect-chain/compiler-{number}/report.json';raw=(ROOT/name).read_bytes();assert sha(raw)==digest;r=json.loads(raw);assert r['compiler_sha256']==COMPILER and r['harness_sha256']==pdigest;assert sha((ROOT/'analysis/aspect-chain'/probe).read_bytes())==pdigest;provenance.append(dict(report=name,report_sha256=digest,probe=probe,probe_sha256=pdigest))
  for c in r['cases']:
   assert sha(c['source'].encode('cp437'))==c['source_sha256'];v={k:c[k]for k in ['name','label','source','source_sha256']}
   if c['success']:
    assert sha(bytes.fromhex(c['hex']))==c['asx_sha256'];v.update(hex=c['hex'],asx_sha256=c['asx_sha256']);yes.append(v)
   else:v['errors']=c['errors'];no.append(v)
 assert len(yes)==35 and len(no)==41
 result=dict(schema='aspect-chain-compiler-v1',source_encoding='cp437',source_command='EXECUTE',rejected_keyword='CHAIN',compiler_sha256=COMPILER,provenance=provenance,freezer_sha256=sha(Path(__file__).read_bytes()),vectors=yes,rejected=no,scope='Compilergrammar/emissiononly. Rawfilenamebytespreserved; noextensionvalidation/parameterlist/unreachableelimination. Nativeexecution/restart999/pathresolutionremainseparate.')
 (ROOT/'standalone/fixtures/aspect_chain_compiler_vectors.json').write_text(json.dumps(result,indent=2)+'\n');print('Frozen35accepted41rejectedbeforeimplementation')
if __name__=='__main__':main()
