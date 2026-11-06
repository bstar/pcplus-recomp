#!/usr/bin/env python3
"""Bind the four-height Help matrix and cold rebuild to the accepted products."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('matrix','cold','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT)
  r=json.loads(path.read_text());assert r['passed'],path
  receipts[str(path.relative_to(ROOT))]=sha(path)
  for name,digest in r.get('sources',{}).items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
  return r
 matrix=load(a.matrix/'result.json');cold=load(a.cold/'result.json')
 assert matrix['products']==cold['products']
 expected={(rows,case) for rows in (25,28,43,50) for case in ('normal','repeat','missing-helper','missing-resource','bad-resource','flow')}
 assert len(matrix['cases'])==24 and {(r['rows'],r['case']) for r in matrix['cases']}==expected
 counts={}
 for case in matrix['cases']:
  assert case['passed'];path=ROOT/case['receipt'];assert sha(path)==case['receipt_sha256']
  r=load(path);assert (r['rows'],r['case'])==(case['rows'],case['case']) and r['products']==matrix['products']
  assert all(r['checks'].values()) and r['observer_words'][3]==r['rows']
  if r['case'] not in ('missing-helper','missing-resource','bad-resource'):assert r['checks']['helper_footer_at_actual_bottom']
  counts[case['name']]=len(r['checks'])
 for name,digest in cold['overlay_sources'].items():assert sha(ROOT/name)==digest,name
 for r in cold['runs']:assert all(r['checks'].values())
 baseline=ROOT/'docs/validation/global-help.json';accepted=json.loads(baseline.read_text())
 assert accepted['passed'] and accepted['products']==matrix['products']
 receipts[str(baseline.relative_to(ROOT))]=sha(baseline)
 sources['standalone/record_global_help_rows.py']=sha(Path(__file__))
 report=dict(passed=True,products=matrix['products'],sources=sources,receipts=receipts,checks_per_case=counts,
  cold_source_files=cold['source_files'],cold_base_commit=cold['base_commit'],
  scope='24 current-parent normal-main Help sessions at25/28/43/50 BIOS rows, six workflows at each height, plus exact four-product cold rebuild repeating25-row normal/flow sessions. Product identities unchanged from accepted global-help receipt; its BBS/ASPECT/Chat evidence is retained there rather than rerun or relabeled.',
  limitations=['No new original-helper comparison at28/43 rows.','Only reference context41 wired; no additional mouse/input/alternate-mode parity claim.','No physical deployment or hardware/SIP/audio acceptance.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
 print('PASS global Help four-height receipt:24 sessions')
if __name__=='__main__':main()
