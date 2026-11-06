#!/usr/bin/env python3
"""Bind Chat Help recovery/flow matrix and current-parent BBS regressions."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('matrix','cold','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT)
  r=json.loads(path.read_text());assert r['passed'],path;receipts[str(path.relative_to(ROOT))]=sha(path)
  for name,digest in r.get('sources',{}).items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
  return r
 matrix=load(a.matrix/'result.json');cold=load(a.cold/'result.json');products=matrix['products']
 assert cold['products']==products
 expected={(rows,case) for rows in (25,28,43,50) for case in ('normal','repeat','missing-helper','missing-resource','bad-resource','flow')}
 assert len(matrix['cases'])==24 and {(r['rows'],r['case']) for r in matrix['cases']}==expected
 for case in matrix['cases']:
  assert case['passed'];file=ROOT/case['receipt'];assert sha(file)==case['receipt_sha256']
  r=load(file);assert r['products']==products and (r['rows'],r['case'])==(case['rows'],case['case']) and all(r['checks'].values())
  assert r['observer_words'][3]==r['rows']
  if case['case']=='repeat':assert r['observer_words'][1]==5
  if case['case']=='flow':assert r['checks']['data_held_until_XON'] and r['checks']['raw_CP437_resumed_in_Chat']
 assert {r['case'] for r in cold['runs']}=={'normal','flow','Chat-25','Chat-50'}
 for r in cold['runs']:assert all(r['checks'].values())
 for name,digest in cold['overlay_sources'].items():assert sha(ROOT/name)==digest,name
 busy=load(ROOT/'build/chat-help-busy-pressure-20261106/result.json')
 assert busy['binary_sha256']==products['TERMINAL.EXE'] and busy['pressure_keys']==40 and len(busy['cases'])==4
 for r in busy['cases']:assert r['passed'] and all(r['checks'].values())
 sync=load(ROOT/'build/bbs-lab/results/synchronet/chat-help-sync-20261106/proxy-integration.json')
 assert sync['binary_sha256']==products['TERMINAL.EXE'] and len(sync['checks'])==25 and all(sync['checks'].values())
 enigma=load(ROOT/'build/bbs-lab/results/enigma/chat-help-enigma-20261106/carrier-checks.json')
 assert enigma['products']['TERMINAL.EXE']['sha256']==products['TERMINAL.EXE'] and len(enigma['checks'])==16 and all(enigma['checks'].values())
 audit=load(ROOT/'build/chat-help-enigma-audit-20261106/result.json')
 assert audit['terminal_sha256']==products['TERMINAL.EXE'] and audit['exact_retry_bytes']==65539
 baseline=ROOT/'docs/validation/chat-global-help.json';r=json.loads(baseline.read_text());assert r['passed'] and r['products']==products
 receipts[str(baseline.relative_to(ROOT))]=sha(baseline)
 sources['standalone/record_chat_help_recovery.py']=sha(Path(__file__))
 report=dict(passed=True,products=products,sources=sources,receipts=receipts,
  summary=dict(Chat_Help_sessions=24,BIOS_rows=[25,28,43,50],busy_pressure_cases=4,busy_pressure_keys=40,Synchronet_checks=25,Enigma_checks=16,Enigma_exact_retry_bytes=65539,cold_source_files=cold['source_files']),
  limitations=['Busy pressure regression covers prior TEXT/cancellation behavior, not Alt-Z queued during a native-parser wait.',
   'Module memory identity and lifetime faults, queued Help at busy/full FIFO and geometry faults remain open.',
   'BBS regressions exercise current parent without Chat/Help invocation inside a real BBS session.',
   'No physical deployment/acceptance, SIP/audio acceptance, other Help contexts or full original parity.'],
  scope='Same four products as the initial Chat Help checkpoint. Actual DOS main failure/repeat/raw CP437 software-flow and four-height return coverage, current-build Enigma/Synchronet and independent wire/CRC/carrier audit. Corrected observer waits for prompt dismissal/restored cursor; earlier failed observer captures retained. No application change needed.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS Chat Help recovery receipt')
if __name__=='__main__':main()
