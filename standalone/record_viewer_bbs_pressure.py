#!/usr/bin/env python3
"""Bind whole BBS viewer roundtrips, independent screen audits and sink pressure."""
import argparse,json
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','enigma','synchronet','pressure','controls','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary=a.terminal.resolve();manifest=json.loads(binary.with_name('manifest.json').read_text());digest=sha(binary)
 assert digest==manifest['binary_sha256'] and manifest['experimental_file_viewer']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 def bind(path):return dict(path=str(path.resolve().relative_to(ROOT)),sha256=sha(path))
 def checked(path):
  r=json.loads(path.read_text());assert r['passed'],path
  if isinstance(r.get('checks'),dict):assert all(r['checks'].values()),path
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n
  return r
 pressure=checked(a.pressure);assert pressure['binary_sha256']==digest
 assert {c['case'] for c in pressure['cases']}=={'capture','hold','capture-printer','hold-printer','printer'}
 for c in pressure['cases']:assert c['passed'] and all(c['checks'].values()) and c['binary_sha256']==digest
 servers=[]
 for name,folder in [('Enigma',a.enigma),('Synchronet',a.synchronet)]:
  r=checked(folder/'proxy-integration.json');audit=checked(folder/'screen-reference-audit.json');base=checked(folder/'result.json')
  assert r['binary_sha256']==audit['binary_sha256']==base['binary_sha256']==digest
  assert audit['different_cells']==0 and audit['matched_cells']==1920
  viewer=r['file_viewer'];assert viewer['passed'] and all(viewer['checks'].values())
  assert len((folder/'VFVIEW.BIN').read_bytes())==12024
  if name=='Synchronet':
   assert base['cpu']=='386' and base['video_observer_high_requested']
   assert viewer['observer_high_required'] and viewer['observer_resident_segment']>=0xa000
   assert r['checks']['actual_ASPECT_login']
  else:assert base['cpu']=='8086' and not base['video_observer_high_requested']
  servers.append(dict(server=name,cpu=base['cpu'],report=bind(folder/'proxy-integration.json'),screen_audit=bind(folder/'screen-reference-audit.json'),checks=r['checks'],viewer=viewer,matched_cells=audit['matched_cells'],different_cells=audit['different_cells'],delivered_bytes=audit['delivered_bytes'],artifacts=[bind(folder/n) for n in ['VFVIEW.BIN','VFSEG.BIN','VIEW.DAT','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','serial-sent.bin','serial-received.bin']]))
 controls=checked(a.controls);assert len(controls['cases'])==3 and all(c['identical'] for c in controls['cases'])
 result=dict(passed=True,binary_sha256=digest,physical_deployment_changed=False,servers=servers,
  pressure=dict(report=bind(a.pressure),cases=pressure['cases'],sources=pressure['sources']),existing_fixture_controls=dict(report=bind(a.controls),cases=controls['cases']),
  conventional_memory_limit='The stock Synchronet run with the full observer in conventional memory failed DOS EXEC with error8. Its accepted386 run explicitly enables XMS/UMB, disables EMS and verifies the observer segment. This does not establish an8086 conventional-memory ASPECT/viewer pass.',
  sources={n:sha(ROOT/n) for n in ['standalone/record_viewer_bbs_pressure.py','standalone/build_path_session.py']},original_inputs=[],
  limits=['No SIP/audio/DSP/analog or physical acceptance.','Printer is DOSBox virtual PRN.','No application memory-loan experiment was promoted.','Installed release, selector and private configuration are unchanged.'])
 out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS two whole BBS viewer roundtrips and five sink pressure cases')
if __name__=='__main__':main()
