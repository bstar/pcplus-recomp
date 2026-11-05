#!/usr/bin/env python3
"""Bind decoder DOS/linked/source-export proofs and original content-row captures."""
import argparse,json,struct
from pathlib import Path
from build_path_session import ROOT,sha
from test_viewer_decode_dos import vectors

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['program','dos','linked','public-source','original','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 def bind(path):
  path=path.resolve();return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
 def checked(path):
  r=json.loads(path.read_text());assert r['passed'],path
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n
  return r
 binary=a.program.resolve();manifest=json.loads(binary.with_name('manifest.json').read_text())
 digest=sha(binary);assert manifest['binary_sha256']==digest and not manifest['original_inputs']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 dos=checked(a.dos);linked=checked(a.linked);public=checked(a.public_source);original=checked(a.original)
 assert dos['binary_sha256']==linked['binary_sha256']==public['binary_sha256']==digest
 assert dos['vectors']==175 and dos['state_placements']==2 and dos['checks']==45745
 assert linked['inputs']==66 and all(c['passed'] for c in linked['cases'])
 assert len(public['source_files'])==5 and public['original_inputs']==[]
 for n,h in dos['artifacts'].items():assert sha(a.dos.parent/n)==h,n
 blob=b'VD01'+struct.pack('<H',len(vectors()))
 for v in vectors():blob+=struct.pack('<6H2L',v['width'],v['rows'],v['block'],len(v['data']),v['used'],v['status'],v['start'],v['next'])+v['data']+v['page']
 assert (a.dos.parent/'drive/VECTORS.BIN').read_bytes()==blob
 segments=manifest['decoder_segments'];assert segments['FILE_CODE']['class']=='FARCODE'
 assert all(s['bytes']==0 for n,s in segments.items() if n!='FILE_CODE')
 comparisons=[]
 for v in [v for v in vectors() if v['original_oracle'] and v['block']==256]:
  c=next(c for c in original['cases'] if c['case']==v['name']);index=0 if v['name']=='large' else 4 if v['name']=='retry' else 2
  f=c['captures'][index];path=ROOT/f['path'];assert sha(path)==f['sha256']
  frame=path.read_bytes();assert len(frame)==4000 and frame[:3840:2]==v['page']
  comparisons.append(dict(case=v['name'],matched_character_bytes=1920,capture=f))
 assert len(comparisons)==8
 r=dict(passed=True,binary_sha256=digest,state_bytes=26,decoder_code_bytes=segments['FILE_CODE']['bytes'],persistent_DGROUP_bytes=0,
  DOS=dict(vectors=175,state_placements=2,checks=45745,report=bind(a.dos)),
  linked=dict(inputs=66,report=bind(a.linked)),public_source=bind(a.public_source),original_receipt=bind(a.original),
  original_comparisons=comparisons,original_inputs=[],manifest=bind(binary.with_name('manifest.json')),
  sources={**dos['sources'],**linked['sources'],'standalone/record_viewer_decode.py':sha(Path(__file__))},
  scope='Source-only banked incremental decoder;175 actualDOS8086 vectors at two state placements,66 linked far-page/state/ABI/no-interrupt cases,15360 content bytes matched to eight original viewer captures and byte-identical five-file public-source rebuild. No terminal/UI/file-handle integration or physical deployment/acceptance.',
  remaining=['Read-only DOS handle/seek ownership, canonical/share checks, failure/close quarantine.',
             'Serviced viewer UI, paging checkpoints, exact frame/cursor restoration and Alt-V dispatch.',
             'Capture/HOLD/PRN, live BBS/editor, carrier-loss/reconnect/transfer composition.',
             'Configured external-viewer binding, physical DOS6.22/Boca/SIP route and full remaining parity inventory.'])
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS decoder proofs and15360 original content bytes')
if __name__=='__main__':main()
