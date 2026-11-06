#!/usr/bin/env python3
"""Bind transfer loss, running-child loss, live recovery witnesses and composition."""
import argparse,json,struct
from pathlib import Path
from build_path_session import ROOT,sha

def child_checks(folder):
 child=(folder/'VLOSS.BIN').read_bytes();live=(folder/'VACT.BIN').read_bytes()
 c=struct.unpack('<14H',child);s=struct.unpack_from('<16H',live);frame=live[32:]
 return dict(child_identity=c[:2]==(0xc156,1),actual_DCD_transition=c[6:8]==(1,1) and bool(c[3]&0x80) and not(c[11]&0x80),IRQs_enabled=bool(c[2]&0x200) and bool(c[10]&0x200),DTR_kept_RTS_paused=c[4]&3==c[12]&3==1,IER_quiet=c[5]==c[13]==0,bounded_wait=0<c[8]<162,
  live_identity=len(live)==4032 and s[:2]==(0xca56,1) and s[3]==1,second_connection=s[5]==6,owners_released=s[6:11]==(0,0,0x5658,0,0),live_geometry=s[11:13]==(0x5003,25) and s[15]==16,live_remote_display=frame[::2].startswith(b'FIRST BYTE SAFE') and frame[160:178:2]==b'REDIAL OK' and frame[320:330:2]==b'KEYOK')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','transfer-prefix','child','composed','output']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();digest=sha(binary);manifest=json.loads(binary.with_name('manifest.json').read_text())
 assert digest==manifest['binary_sha256'] and manifest['experimental_external_viewer']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 def bind(path):return dict(path=str(path.resolve().relative_to(ROOT)),sha256=sha(path))
 def read(path):
  r=json.loads(path.read_text());assert r['passed'],path
  assert r.get('binary_sha256',r.get('terminal_sha256'))==digest,path
  if isinstance(r.get('checks'),dict):assert all(r['checks'].values()),path
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n
  for n,h in r.get('artifacts',{}).items():assert sha(ROOT/n)==h,n
  for c in r['cases']:assert c['passed'] and all(c['checks'].values()),path
  return r
 names=['receive-negotiation','receive-partial','upload-unacked','upload-partial']+[f'{p}-{k}' for p in ['ymodem','zmodem'] for k in ['receive-metadata','receive-partial','receive-retained','upload-metadata','upload-partial']]
 transfer=[]
 for name in names:
  path=Path(str(a.transfer_prefix)+name+'-20261105')/'result.json';r=read(path);assert len(r['cases'])==1 and r['cases'][0]['case']==name
  c=r['cases'][0];assert c['checks']['carrier_fault'] and c['checks']['two_actual_connections'] and c['checks']['keyboard_after_redial']
  transfer.append(dict(case=name,report=bind(path),checks=c['checks']))
 child=read(a.child);assert {c['case'] for c in child['cases']}=={'text','graphics'}
 for c in child['cases']:assert all(child_checks(a.child.parent/c['case']).values())
 composed=read(a.composed);assert {c['case'] for c in composed['cases']}=={'ymodem-receive-retained','zmodem-upload-partial'}
 for c in composed['cases']:
  assert c['checks']['actual_external_child'] and c['checks']['carrier_fault'] and c['checks']['two_actual_connections']
  for n,h in c['carrier']['artifacts'].items():assert sha(ROOT/n)==h,n
 out.mkdir();controls=[];source=a.child.parent/'graphics'
 for name,leaf,at in [('initial-carrier','VLOSS.BIN',6),('carrier-drop','VLOSS.BIN',14),('live-mode','VACT.BIN',22),('program-owner','VACT.BIN',12),('viewer-pending','VACT.BIN',20),('live-remote-marker','VACT.BIN',352)]:
  folder=out/name;folder.mkdir()
  for n in ['VLOSS.BIN','VACT.BIN']:(folder/n).write_bytes((source/n).read_bytes())
  path=folder/leaf;raw=bytearray(path.read_bytes());raw[at]^=0x80 if name=='initial-carrier' else 1;path.write_bytes(raw)
  checks=child_checks(folder);assert not all(checks.values()),name
  controls.append(dict(case=name,rejected=True,failed_checks=[n for n,v in checks.items() if not v]))
 result=dict(passed=True,binary_sha256=digest,application_unchanged=True,physical_deployment_changed=False,transfer_cases=transfer,child=dict(report=bind(a.child),cases=child['cases']),composed=dict(report=bind(a.composed),cases=composed['cases']),negative_controls=controls,
  sources={n:sha(ROOT/n) for n in ['standalone/record_external_carrier_recovery.py','standalone/build_path_session.py']},original_inputs=[],
  limits=['Actual DOSBox modem MSR/DCD changes come from owned socket closure; this is software evidence, not Boca/SPA2102/SIP/audio/DSP/analog or physical CTS acceptance.','Fourteen direct transfer cases exercise the current candidate without a preceding viewer; two extra cases compose the graphics viewer with subsequent YMODEM/ZMODEM partial-transfer loss.','Running children are bounded owned fixtures with IRQs enabled. A hung or IRQ-disabled third-party child and remote termination of arbitrary programs remain unverified.','The read-only live witness records graphics recovery and released ownership before parent exit; it does not inject keys, terminal replies or product state.','No physical deployment, private configuration or selected-package change.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS14 transfer-loss cases,2 running-child cases,2 composed cases and6 rejected data controls')
if __name__=='__main__':main()
