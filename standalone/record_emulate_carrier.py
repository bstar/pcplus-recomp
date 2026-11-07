#!/usr/bin/env python3
"""Bind the matched package's active ALARM/carrier/service-error matrix."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={};cases=[]
 package=ROOT/'build/emulate-connection-candidate-20261107/package';m=json.loads((package/'manifest.json').read_text());products={n:m['files'][n]for n in ('TERMINAL.EXE','ASPECT.EXE')}
 for profile in (4,6):
  root=ROOT/'build'/f'emulate-package-alarm-carrier-p{profile}-20261107';path=root/'checks.json';r=json.loads(path.read_text());assert r['passed'] and not r['diagnostic_reuse'] and r['profile']==profile and r['products']==products
  receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in r['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
  assert [c['case'] for c in r['cases']]==['NONE','CALL','TX','XOFF']
  for c in r['cases']:
   assert c['passed'] and len(c['checks'])==37 and all(c['checks'].values())
   for n,h in c['captures'].items():
    target=root/c['case']/n
    assert sha(target)==h,(target,n);receipts[str(target.relative_to(ROOT))]=h
   cases.append(dict(profile=profile,case=c['case'],checks=37,typed_exit=c['child_header'][6],speaker=c['speaker_words'],disconnect=c['carrier_observation']))
 for n in ('TERMINAL.EXE','ASPECT.EXE'):assert sha(package/'PCPLUS'/n)==products[n]
 sources['standalone/record_emulate_carrier.py']=sha(Path(__file__))
 report=dict(passed=True,products=products,cases=cases,checks=296,sources=sources,receipts=receipts,original_inputs=[],physical_acceptance=False,
  limitations=['Ordinary matched products run with real DOSBox modem DCD changes and a passive UMB observer. No product memory writes or parser/reply substitutions. Native speaker gate activity is measured; audible physical output is not.',
   'Profiles4/6 with no handler, deferred CALL, TRANSMIT and XOFF service error cover the named matrix. No physical Boca/SIP/DSP/CTS timing or universal asynchronous fault/whole-feature claim.',
   'This software checkpoint does not itself select or install a release; physical acceptance must be recorded separately.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS matched active ALARM matrix',len(cases),'cases,296 checks')
if __name__=='__main__':main()
