#!/usr/bin/env python3
"""Optional freeze of authored original BREAK/SET/FETCH grammar evidence."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
REPORTS=[('01','c189ff76bab8774a19bae1503ab745a2917a9cc5fd33c9addad7f466914e1d3c','compiler_probe.py','69d64ef7df7e3f87cf26bb262241494096ef2407e8087751a5478f02f8fcc3c8'),('02','cb3f240d4afb1e92c08329e604af11de61e0640bb2b9c70d470c1521286bc6b1','compiler_probe02.py','90e51c754d5c82718fdb0113feda464b333bbd2b4755d3aac78fd2c2ed40abc3'),('03','2abcd15fe184e5650fa51f71a90dedff233c608faa42047b8559526cb9236104','compiler_probe03.py','270c70d229c2b2402a0310b9060911537dbe9273b2608b25f71cff34ae4319d4')]
COMPILER='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 yes=[];no=[];unsupported=[];provenance=[]
 for number,digest,probe,pdigest in REPORTS:
  name=f'analysis/aspect-break/compiler-{number}/report.json';raw=(ROOT/name).read_bytes();assert sha(raw)==digest;r=json.loads(raw);assert r['compiler_sha256']==COMPILER and r['harness_sha256']==pdigest;assert sha((ROOT/'analysis/aspect-break'/probe).read_bytes())==pdigest;provenance.append(dict(report=name,report_sha256=digest,probe=probe,probe_sha256=pdigest))
  for c in r['cases']:
   assert sha(c['source'].encode('cp437'))==c['source_sha256'];v={k:c[k]for k in ['name','label','source','source_sha256']}
   if c['success']:
    assert sha(bytes.fromhex(c['hex']))==c['asx_sha256'];v.update(hex=c['hex'],asx_sha256=c['asx_sha256'])
    yes.append(v)
   else:v['errors']=c['errors'];no.append(v)
 assert len(yes)==64 and len(no)==143 and not unsupported
 r=dict(schema='aspect-break-compiler-v1',source_encoding='cp437',compiler_sha256=COMPILER,provenance=provenance,freezer_sha256=sha(Path(__file__).read_bytes()),vectors=yes,rejected=no,unsupported=unsupported,native_setting_evidence=dict(private_report_sha256='d47042e1e0eeb638b1e1cfb6bdd49128dfde927ef1f646d779c9f8b33a8379f9',cases=12),scope='Sourcegrammar/emission only. NativeSETbounds0..32767; FETCHreturnsrawword. No UARTBREAK/runtimeavailability claim. Selected12FETCHsettingsonly.')
 (ROOT/'standalone/fixtures/aspect_break_compiler_vectors.json').write_text(json.dumps(r,indent=2)+'\n');print('Frozen64accepted143rejected; selected12FETCHsettings')
if __name__=='__main__':main()
