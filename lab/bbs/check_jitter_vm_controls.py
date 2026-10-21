#!/usr/bin/env python3
"""Exercise the buffered-pair audit with rehashed, semantically damaged evidence."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
from synthmodem_vm_control import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 original=a.candidate.resolve();cases=[]
 for mode in ('pristine','guest-data-mismatch','stale-zero-difference-claim'):
  cohort=out/mode;shutil.copytree(original,cohort)
  receipt=json.loads((cohort/'result.json').read_text());analysis=json.loads((cohort/'PCM-analysis.json').read_text())
  receipt['tested_inputs']={str(cohort/Path(n).relative_to(original)):h for n,h in receipt['tested_inputs'].items()}
  if mode=='guest-data-mismatch':
   target=cohort/'guest-decoded.bin';body=bytearray(target.read_bytes());body[0]^=1;target.write_bytes(body)
  elif mode=='stale-zero-difference-claim':
   target=cohort/'modem_rx_8k.raw';body=bytearray(target.read_bytes());at=2*(analysis['sample_alignment']['dominant_offset_samples']+40000);assert at<len(body);body[at]^=1;target.write_bytes(body)
   # Refresh the claimed decoder capture identity without rerunning it. The
   # auditor must still verify the actual waveform, not trust that old claim.
   decoder=json.loads((cohort/'offline-guest.json').read_text());decoder['capture_sha256']=sha(target)
   (cohort/'offline-guest.json').write_text(json.dumps(decoder,indent=2)+'\n')
  receipt['captures_sha256']={n:sha(cohort/n) for n in receipt['captures_sha256']}
  (cohort/'result.json').write_text(json.dumps(receipt,indent=2)+'\n')
  analysis['frozen_inputs']={n:sha(cohort/n) for n in analysis['frozen_inputs']}
  (cohort/'PCM-analysis.json').write_text(json.dumps(analysis,indent=2)+'\n')
  destination=out/(mode+'-audit')
  with (out/(mode+'.stdout')).open('w') as log:
   process=subprocess.run([sys.executable,str(ROOT/'lab/bbs/audit_jitter_vm.py'),'--baseline',str(a.baseline.resolve()),'--candidate',str(cohort),'--baseline-variant','candidate','--candidate-variant','buffered','--network-profile','buffered-increase','--output',str(destination)],stdout=log,stderr=subprocess.STDOUT)
  result=json.loads((destination/'result.json').read_text());checks=result['checks']
  passed=(process.returncode==0 and result['passed']) if mode=='pristine' else (process.returncode!=0 and not result['passed'])
  if mode=='guest-data-mismatch':passed &= result['cohorts']['candidate']['checks']['guest_frames_equal_observed_data'] is False
  if mode=='stale-zero-difference-claim':passed &= checks['candidate_raw_PCM_matches_RTP_prefix'] is False and checks['all_provenance_and_transport_invariants'] is True
  cases.append(dict(mode=mode,passed=bool(passed),auditor_exit=process.returncode,checks=checks,audit_sha256=sha(destination/'result.json')))
 result=dict(passed=all(v['passed'] for v in cases),cases=cases,baseline=str(a.baseline.resolve()),candidate=str(original),
  inputs={n:sha(ROOT/n) for n in ('lab/bbs/check_jitter_vm_controls.py','lab/bbs/audit_jitter_vm.py','lab/bbs/check_buffered_dmodem_build.py')},
  scope='One pristine cloned growth pair and two rehashed evidence corruptions. Verifies actual framed-data mismatch rejection and independent raw-PCM rejection despite stale analyzer/decoder identity claims. Evidence checks only; no additional modem/DOS/physical run.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']


if __name__=='__main__':main()
