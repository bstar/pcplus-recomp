#!/usr/bin/env python3
"""Seal the corrected viewer/redial candidate and its composed recovery gates."""
import argparse,json
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','ui','bbs','transfer','carrier','layout','source-proof','controls','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary=a.terminal.resolve();digest=sha(binary);m=json.loads(binary.with_name('manifest.json').read_text())
 assert digest==m['binary_sha256'] and m['experimental_external_viewer']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 def bind(path):return dict(path=str(path.resolve().relative_to(ROOT)),sha256=sha(path))
 def read(path):
  r=json.loads(path.read_text());assert r['passed'],path
  assert r.get('binary_sha256',digest)==digest,path
  if isinstance(r.get('checks'),dict):assert all(r['checks'].values()),path
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n
  return r
 ui=read(a.ui);bbs=read(a.bbs);transfer=read(a.transfer);carrier=read(a.carrier);layout=read(a.layout);proof=read(a.source_proof);controls=read(a.controls)
 assert len(ui['runtime'])==21 and len(ui['native_prompt_comparisons'])==7
 assert len(bbs['servers'])==2 and all(s['different_cells']==0 and s['matched_cells']==1920 for s in bbs['servers'])
 expected={'x-rx-binary','x-tx-binary','y-rx-cancel-retry','y-tx-binary','z-rx-default','z-tx-escape'}
 assert transfer['external_viewer'] and {c['case'] for c in transfer['cases']}==expected
 for c in transfer['cases']:assert c['passed'] and c['terminal_sha256']==digest and all(c['checks'].values())
 retry=next(c for c in transfer['cases'] if c['case']=='y-rx-cancel-retry')
 assert all(retry['checks'][n] for n in ['actual_CAN_pair','cancelled_and_resumed_before_retry','retry_completed_same_connection'])
 assert carrier['external_viewer'] and carrier['observer_words'][3:7]==[1,1,1,1] and carrier['observer_words'][10:14]==[0,0,0x5658,0]
 assert carrier['checks']['real_modem_loss'] and carrier['checks']['two_actual_connections']
 assert layout['private_action']==0xf300 and layout['redial_action']==0xf600 and len(layout['negative_controls'])==5
 assert any(c['gate']=='redial-action-collision' and c['rejected'] for c in layout['negative_controls'])
 assert len(controls['cases'])==12 and all(c['identical'] for c in controls['cases'])
 result=dict(passed=True,binary_sha256=digest,private_viewer_action='F300',browser_redial_action='F600',
  ui=bind(a.ui),bbs=bind(a.bbs),transfer=dict(report=bind(a.transfer),cases=transfer['cases']),carrier=dict(report=bind(a.carrier),checks=carrier['checks'],observer_words=carrier['observer_words']),
  layout=bind(a.layout),public_source_build=bind(a.source_proof),unchanged_prior_fixtures=dict(report=bind(a.controls),cases=controls['cases']),physical_deployment_changed=False,
  sources={n:sha(ROOT/n) for n in ['standalone/record_viewer_external_composition.py','standalone/build_path_session.py']},
  limits=['Corrected candidate differs from the prior viewer candidate by exactly two F6-to-F3 action bytes; this resolves intercepted browser redial. The failing prompt-carrier/redial run remains excluded.','Transfer peers are independent owned protocol implementations; virtual UART/DCD and local BBS proxy do not establish physical CTS/SIP/audio/DSP/analog acceptance.','Carrier loss occurs while external parameters own the screen, before a child starts. Loss during a running child or transfer is not established by this receipt.','ZMODEM escape means escaped wire-byte transfer, not cancellation; YMODEM specifically exercises local cancellation and successful retry on the same connection.','Synchronet editor evidence requires the386/XMS/UMB setup with both test helpers actually high.','This does not replace the selected physical package or close the remaining full-parity inventory.'])
 out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS corrected redial namespace,21 UI routes,2 BBSes,6 transfers,cancel/retry,carrier redial and cold source build')
if __name__=='__main__':main()
