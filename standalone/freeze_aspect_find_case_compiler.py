#!/usr/bin/env python3
"""Optional freeze of authored FIND/SWITCH originalcompiler outcomes."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
REPORTS=[('01','9012f46999b927b3a6603e4bab9231cd9db9358edb44a6c5108f2f674d3df1dc','compiler_probe.py','56c94f44bc5a743aab145925647bbfb74bced731b7174ed037af758d7dfc3dbb'),('02','bee7863edf03016b6bfeed01e09dd6817078a5b9a671c7aabd907bd69c8bcfb3','compiler_probe02.py','0c046530f7577596569442d378379fea39f5dded383bf25044f2c9afd4901ce7'),('03','0254b6f4fbd4e084256eff682585e41503d0531d8cf6b8e30f0cf5a7b4b79177','compiler_probe03.py','a5187113d6262b329cac699137dbbf437b3a52c31466eca5ed2dae2c54826abe')]
COMPILER='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 yes=[];no=[];provenance=[]
 for number,digest,probe,pdigest in REPORTS:
  name=f'analysis/aspect-findcase/compiler-{number}/report.json';raw=(ROOT/name).read_bytes();assert sha(raw)==digest;r=json.loads(raw);assert r['compiler_sha256']==COMPILER and r['harness_sha256']==pdigest;assert sha((ROOT/'analysis/aspect-findcase'/probe).read_bytes())==pdigest
  provenance.append(dict(report=name,report_sha256=digest,probe=probe,probe_sha256=pdigest))
  for c in r['cases']:
   assert sha(c['source'].encode('cp437'))==c['source_sha256'];v={k:c[k]for k in ['name','label','source','source_sha256']}
   if c['success']:
    assert sha(bytes.fromhex(c['hex']))==c['asx_sha256'];v.update(hex=c['hex'],asx_sha256=c['asx_sha256']);yes.append(v)
   else:v['errors']=c['errors'];no.append(v)
 assert len(yes)==54 and len(no)==72
 out=dict(schema='aspect-find-case-compiler-v1',source_encoding='cp437',compiler_sha256=COMPILER,provenance=provenance,freezer_sha256=sha(Path(__file__).read_bytes()),vectors=yes,rejected=no,scope='Authored compilergrammar/encoding only. FIND/SWITCH runtime support not established by compilation. BREAK0D is seriallineBREAK, not switchcontrol.')
 (ROOT/'standalone/fixtures/aspect_find_case_compiler_vectors.json').write_text(json.dumps(out,indent=2)+'\n');print('Frozen54accepted72rejected beforemaintainedcompilerchanges')
if __name__=='__main__':main()
