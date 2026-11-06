#!/usr/bin/env python3
"""Bind post-child Enigma/Synchronet viewer return and independent screen audits."""
import argparse,json,struct,sys
from pathlib import Path
from build_path_session import ROOT,sha
sys.path.insert(0,str(ROOT/'lab/bbs'))
from external_viewer_bbs_support import audit

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','runner','enigma','synchronet','controls','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary=a.terminal.resolve();m=json.loads(binary.with_name('manifest.json').read_text());digest=sha(binary)
 assert m['experimental_external_viewer'] and digest==m['binary_sha256']
 runner=a.runner.resolve();rm=json.loads(runner.with_name('manifest.json').read_text())
 assert sha(runner)==rm['binary_sha256']=='23caac9350b0a4be6f5898ce4bbc52c21604a5410a5f3340feae7732e04b004f'
 for manifest in [m,rm]:
  assert not manifest.get('original_inputs')
  for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 def bind(path):return dict(path=str(path.resolve().relative_to(ROOT)),sha256=sha(path))
 servers=[]
 for name,folder in [('Enigma',a.enigma),('Synchronet',a.synchronet)]:
  r=json.loads((folder/'proxy-integration.json').read_text());base=json.loads((folder/'result.json').read_text());screen=json.loads((folder/'screen-reference-audit.json').read_text())
  assert all(x['passed'] and x['binary_sha256']==digest for x in [r,base,screen])
  assert all(r['checks'].values()) and screen['different_cells']==0 and screen['matched_cells']==1920
  v=r['external_viewer'];assert v['passed'] and all(v['checks'].values())
  assert len((folder/'VFVIEW.BIN').read_bytes())==12024
  for n,h in v['sources'].items():assert sha(ROOT/n)==h,n
  if name=='Synchronet':
   assert base['cpu']=='386' and base['video_observer_high_requested'] and r['external_observer_segment']>=0xa000 and r['external_key_helper_segment']>=0xa000
   assert r['checks']['actual_ASPECT_login']
  else:assert base['cpu']=='8086'
  servers.append(dict(server=name,report=bind(folder/'proxy-integration.json'),screen_audit=bind(folder/'screen-reference-audit.json'),viewer=v,cpu=base['cpu'],matched_cells=1920,different_cells=0,delivered_bytes=screen['delivered_bytes'],artifacts=[bind(folder/n) for n in ['VFVIEW.BIN','VCHILD.BIN','VFSEG.BIN','SCREEN.BIN','serial-sent.bin','serial-received.bin']]))
 controls=json.loads(a.controls.read_text());assert controls['passed'] and len(controls['cases'])==6 and all(c['identical'] for c in controls['cases'])
 for n,h in controls['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir();negative=[];original=a.enigma
 for name,target,offset in [('editor-cell','VFVIEW.BIN',4024),('cursor','VFVIEW.BIN',14),('post-child-completion','VFVIEW.BIN',6),('child-tail','VCHILD.BIN',9),('local-parameters','serial-received.bin',None)]:
  folder=out/name;folder.mkdir()
  for leaf in ['VFVIEW.BIN','VCHILD.BIN','serial-received.bin','TEST.PRM']:(folder/leaf).write_bytes((original/leaf).read_bytes())
  path=folder/target;data=bytearray(path.read_bytes())
  if offset is None:data+=b'PAGE.DAT'
  else:data[offset]^=1
  path.write_bytes(data);r=audit(folder);assert not r['passed'],name
  negative.append(dict(case=name,rejected=True,failed_checks=[n for n,v in r['checks'].items() if not v]))
 result=dict(passed=True,binary_sha256=digest,runner_sha256=sha(runner),servers=servers,fixture_controls=dict(report=bind(a.controls),cases=controls['cases']),negative_controls=negative,physical_deployment_changed=False,
  sources={n:sha(ROOT/n) for n in ['standalone/record_viewer_external_bbs.py','standalone/build_path_session.py']},
  limits=['Owned stock loopback BBSes and isolated SynthModem Telnet proxy, synthetic modem serial transport; no SIP/audio/DSP/analog/physical acceptance.','Synchronet uses386/XMS/UMB and verifies both observer and BIOS key producer actually loaded high; no8086 low-memory ASPECT/editor assertion.','The first Synchronet runtime did not launch ASPECT with the key producer in conventional memory. Moving that test producer high allowed the unchanged parent/runner to start the script; this is a lab memory constraint, not a promoted application memory-loan fix.','The owned viewer deliberately leaves mode13h, then sends a private completion marker to gate post-child capture; it does not patch product memory.','Parameters/default geometry only; arbitrary viewers, other video modes, transfers/cancellation/carrier/reconnect through this path remain open.','No application memory-loan change, deployment, live service or private configuration change.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS2 post-child BBS editor returns,3840 reference cells,6 unchanged fixtures and5 rejected data controls')
if __name__=='__main__':main()
