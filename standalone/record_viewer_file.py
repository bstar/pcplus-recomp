#!/usr/bin/env python3
"""Bind actual DOS, linked fault and original-free source-build viewer owner proofs."""
import argparse,json
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['program','dos','linked','public-source','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 def bind(path):
  path=path.resolve();return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
 def checked(path):
  r=json.loads(path.read_text());assert r['passed'],path
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n
  return r
 binary=a.program.resolve();manifest=json.loads(binary.with_name('manifest.json').read_text());digest=sha(binary)
 assert digest==manifest['binary_sha256'] and manifest['original_inputs']==[]
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 dos=checked(a.dos);linked=checked(a.linked);public=checked(a.public_source)
 assert dos['binary_sha256']==linked['binary_sha256']==public['binary_sha256']==digest
 assert dos['checks']==897 and dos['cpu']=='8086' and dos['FPU'] is False
 assert linked['inputs']==25 and len(linked['cases'])==25 and all(c['passed'] for c in linked['cases'])
 assert len(public['sources'])==14 and public['original_inputs']==[]
 for n,h in dos['artifacts'].items():assert sha(a.dos.parent/n)==h,n
 for n,h in dos['fixture_hashes'].items():assert sha(a.dos.parent/'d'/n)==h,n
 assert (a.dos.parent/'d/.DBLOCALFILE_ATR_READONLY.BIN').read_bytes()==b'\0'
 assert (a.dos.parent/'c/AFTERCD.TXT').read_bytes().strip()==b'C:\\'
 segment=manifest['owner_segments'];assert segment['FILE_CODE']['class']=='FARCODE'
 assert all(not s['bytes'] for n,s in segment.items() if n!='FILE_CODE')
 r=dict(passed=True,binary_sha256=digest,owner_bytes=90,snapshot_bytes=84,owner_object_FILE_CODE_bytes=segment['FILE_CODE']['bytes'],persistent_DGROUP_bytes=0,
  DOS=dict(checks=897,report=bind(a.dos)),linked=dict(inputs=25,cases=linked['cases'],report=bind(a.linked)),
  public_source=bind(a.public_source),manifest=bind(binary.with_name('manifest.json')),
  sources={**dos['sources'],**linked['sources'],'standalone/record_viewer_file.py':sha(Path(__file__))},original_inputs=[],
  scope='Read-only FILE_CODE owner component with real capture reservation.897 actualDOS8086 checks,25 linked modeled-DOS error/ABI cases and byte-identical14-file original-free rebuild. Actual media faults, DOS6.22/SHARE enforcement, serviced terminal/viewer UI and hardware are not established.',
  retained_attempts=[dict(path='build/viewer-file-dos-20261105',reason='One diagnostic assertion compared stale idle snapshot after an explicit close; fixture corrected, no owner change.'),
    dict(path='build/viewer-file-accept-dos-20261105',reason='897 DOS checks passed; outer verifier rejected expected DOSBox readonly attribute sidecar.'),
    dict(path='build/viewer-file-native-20261105',reason='897 DOS checks passed; outer verifier expected sidecar01 rather than observed00 plus host readonly mode. Corrected fresh verifier passes.')],
  remaining=['Compose owner and decoder with retained read-ahead and paging offsets.',
    'Serviced viewer UI, frame/cursor restoration, Alt-V dispatch, capture/HOLD/PRN/BBS/carrier/transfer composition.',
    'Child/exit admission for uncertain viewer ownership and configured external-viewer integration.',
    'Physical DOS6.22/Boca/SIP acceptance and full remaining parity gates.'])
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS viewer owner DOS/fault/source proofs')
if __name__=='__main__':main()
