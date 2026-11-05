#!/usr/bin/env python3
"""Seal unchanged-parent viewer/transfer/recovery and independently replayed BBS evidence."""
import argparse,json
from pathlib import Path
from build_path_session import ROOT,sha

EXPECTED={'release':16,'carrier-idle':3,'carrier-transfer':4,'carrier-batch':10,'viewer-transfer':6,'viewer-carrier':1,'enigma-upload':1,'enigma-download':1,'enigma-cancel':1,'cancel-controls':9}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--report',action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads(binary.with_name('manifest.json').read_text());digest=sha(binary);assert digest==manifest['binary_sha256'] and manifest['experimental_file_viewer']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 supplied={}
 for entry in a.report:
  name,path=entry.split('=',1);assert name in EXPECTED and name not in supplied;supplied[name]=Path(path).resolve()
 assert supplied.keys()==EXPECTED.keys()
 groups=[];products=[]
 for name,path in supplied.items():
  assert path.is_relative_to(ROOT/'build');r=json.loads(path.read_text());assert r['passed'],name
  if isinstance(r.get('checks'),dict):assert all(r['checks'].values()),name
  for field in ['sources','captures']:
   for n,h in r.get(field,{}).items():assert sha(ROOT/n)==h,(name,n)
  cases=r.get('cases',[r]);assert len(cases)==EXPECTED[name],name
  for c in cases:
   assert c.get('passed',False),name
   if isinstance(c.get('checks'),dict):assert all(c['checks'].values()),name
  candidate=r.get('binary_sha256',r.get('terminal_sha256'))
  if candidate is not None:assert candidate==digest,name
  if name in ('enigma-upload','enigma-download','enigma-cancel'):
   assert r['payload_bytes']==65539;products.append(r['payload_sha256'])
  if name=='viewer-carrier':
   assert r['observer_words'][3:7]==[1,1,1,1] and r['observer_words'][10:14]==[3,0,65535,0]
  if name=='cancel-controls':assert sum(c['rejected'] for c in cases)==8
  summary=[]
  for c in cases:
   summary.append(dict(case=c.get('case',c.get('mode',name)),checks=c.get('checks',{}),passed=c['passed']))
  groups.append(dict(group=name,report=dict(path=str(path.relative_to(ROOT)),sha256=sha(path)),cases=summary))
 assert len(set(products))==1,'Upload/download/retry must retain identical bytes'
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 result=dict(passed=True,binary_sha256=digest,groups=groups,payload_bytes=65539,payload_sha256=products[0],application_sources_unchanged=True,physical_deployment_changed=False,original_inputs=[],
  sources={n:sha(ROOT/n) for n in ['standalone/record_viewer_recovery.py','standalone/build_path_session.py']},
  limits=['Direct transfer/carrier cases use owned synthetic peers and actual DOSBox virtual UART/DCD.','Stock Enigma uses the staged SynthModem serial-side proxy; no SIP/audio/DSP/analog acceptance.','All these DOS cases use the8086 model at25 physical rows,24 logical rows.','No physical printer, Boca flow timing or hardware acceptance.','No new installed package or selector change.'])
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS recovery receipt:',len(groups),'groups,43 positive runtime cases and8 rejected copied-artifact controls')
if __name__=='__main__':main()
