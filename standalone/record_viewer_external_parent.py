#!/usr/bin/env python3
"""Bind the opt-in external parent to DOS, linked, layout and public-build evidence."""
import argparse,json
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['terminal','matrix-prefix','linked','layout','source-proof','native-prefix','output']:
  p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary=a.terminal.resolve();manifest=json.loads(binary.with_name('manifest.json').read_text());digest=sha(binary)
 assert manifest['experimental_external_viewer'] and digest==manifest['binary_sha256']
 for name,h in manifest['sources'].items():assert sha(ROOT/name)==h,name
 def bind(path):return dict(path=str(path.resolve().relative_to(ROOT)),sha256=sha(path))
 def read(path):
  r=json.loads(path.read_text());assert r['passed'],path
  assert r['binary_sha256']==digest,path
  for name,h in r.get('sources',{}).items():assert sha(ROOT/name)==h,name
  return r
 rows=[]
 for kind,names in [('external',['relative','absolute','options','spaces','empty','cancel','long','maximum','reference','browser','malformed']),('fallback',['cancel','page','next','home','missing','binary','empty','reference','browser','loading-cancel'])]:
  for name in names:
   path=Path(str(a.matrix_prefix)+'-'+kind+'-'+name+'-20261105')/'result.json';r=read(path)
   assert len(r['cases'])==1 and r['cases'][0]['passed'] and all(r['cases'][0]['checks'].values())
   rows.append(dict(kind=kind,case=name,report=bind(path)))
 comparisons=[]
 for name in ['relative','absolute','options','spaces','empty','cancel','long']:
  folder=Path(str(a.native_prefix)+'-'+name+'-20261105');native=json.loads((folder/'result.json').read_text())
  assert native['DOS_done'] and native['process_exit']==0 and native['generated_unchanged']
  original=(folder/'c/EDITVIEW.BIN').read_bytes()[4014:8014]
  parent=ROOT/('build/connection-dos/'+a.matrix_prefix.name+'-external-'+name+'-20261105-'+name)/'VIEWUI.BIN'
  actual=parent.read_bytes()[4018:8018]
  start=10*80*2+5*2;end=(14*80+76)*2
  # Compare only the native dialog's rectangle; live BBS content differs.
  native_box=b''.join(original[(r*80+5)*2:(r*80+76)*2] for r in range(10,15))
  source_box=b''.join(actual[(r*80+5)*2:(r*80+76)*2] for r in range(10,15))
  assert native_box==source_box and len(source_box)==710,name
  comparisons.append(dict(case=name,identical_bytes=710,native=bind(folder/'c/EDITVIEW.BIN'),parent=bind(parent)))
 linked=read(a.linked);layout=read(a.layout);proof=read(a.source_proof)
 assert len(linked['cases'])==13 and len(layout['negative_controls'])==5
 assert all(c['rejected'] for c in layout['negative_controls'])
 assert proof['disabled_sha256']=='1aa5cdb84a595c96ebba6ce2b359690723881c6d56266c2377fa040f81f0902e'
 result=dict(passed=True,binary_sha256=digest,physical_deployment_changed=False,runtime=rows,native_prompt_comparisons=comparisons,
  linked=bind(a.linked),layout=bind(a.layout),public_source_build=bind(a.source_proof),near_bytes=layout['near_bytes'],resident_code_bytes=layout['resident_code_bytes'],
  original_application_build_inputs=[],sources={n:sha(ROOT/n) for n in ['standalone/record_viewer_external_parent.py','standalone/build_path_session.py']},
  limits=['Synthetic COM3/IRQ5 modem in DOSBox; no physical/SIP/audio acceptance.','Default25-row colors and native prompt geometry only; long title clipping is a bounded source policy.','Missing interpreter/program, DOS allocation failure, nonzero child exit presentation, live BBS pressure, transfers and reconnects through this external child path remain unverified.','The prior internal-viewer BBS/transfer receipts describe their previous executable, not this candidate.','Installed selection, private settings and physical PC remain unchanged.'])
 out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS21 DOS workflows,7 native boxes,13 linked cases,5 static negative controls and public cold build')
if __name__=='__main__':main()
