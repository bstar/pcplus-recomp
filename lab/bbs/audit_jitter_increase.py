#!/usr/bin/env python3
"""Verify a retained modem corruption after bounded FIFO delay growth."""
import argparse,json
from pathlib import Path
from analyze_receive_trace import packets,pcm
from audit_jitter_vm import inspect
from synthmodem_vm_control import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);a=p.parse_args();out=a.cohort.resolve()
 assert out.is_relative_to(ROOT/'build')
 ledger=ROOT/'docs/validation/synthmodem-jitter-policy.json'
 report,_,producer=inspect(out,'candidate',json.loads(ledger.read_text())['builds'],'buffered-increase')
 analysis=json.loads((out/'PCM-analysis.json').read_text())
 source=b''.join(pcm(v) for v in packets(out/'rtp-to-guest.bin'));guest=(out/'modem_rx_8k.raw').read_bytes()
 # Independently check every equal interval and every claimed edit against the
 # raw samples. Frame hashes or a dominant-offset estimate alone are weaker.
 source_at=guest_at=0;insertions=[]
 for edit in analysis['frame_alignment_changes']:
  i,j,k,l=[edit[n] for n in ('RTP_frame_start','RTP_frame_end','guest_frame_start','guest_frame_end')]
  assert 0<=source_at<=i<=j<=len(source)//320 and 0<=guest_at<=k<=l<=len(guest)//320
  assert source[source_at*320:i*320]==guest[guest_at*320:k*320]
  if edit['operation']=='insert':
   assert i==j and k<l and not any(guest[k*320:l*320])
   insertions.append(dict(before_RTP_frame=i,guest_frame=k,frames=l-k,samples=(l-k)*160))
  else:
   assert edit['operation']=='delete' and k==l and j==len(source)//320 and l==len(guest)//320
  source_at=j;guest_at=l
 assert source[source_at*320:]==guest[guest_at*320:]
 in_call=[v for v in insertions if v['before_RTP_frame']>0]
 checks=dict(report['checks'])
 checks.update(retained_upstream_failure=not producer['passed'] and [n for n,v in producer['checks'].items() if not v]==['upstream_exact_after_declared_idle'],
  guest_and_independent_decoder_both_corrupt=not report['upstream_exact'] and not report['offline_guest_exact'],
  guest_PCM_reconstructs_from_RTP_and_silence=bool(in_call),
  delay_increase_observed_at_host=analysis['packet_arrival_gaps']['rtp-to-guest']['over100ms']==1)
 captures={n:sha(out/n) for n in ('result.json','PCM-analysis.json','offline-caller.json','offline-guest.json','node-result.json')}
 result=dict(passed=False,diagnostic_verification_passed=all(checks.values()),compatibility_accepted=False,
  checks=checks,cohort=str(out.relative_to(ROOT)),silence_insertions=insertions,observations=report,
  captures_sha256=captures,auditor_sha256=sha(Path(__file__)),shared_auditor_sha256=sha(ROOT/'lab/bbs/audit_jitter_vm.py'),
  scope='Independent provenance, actual framed guest data, exact independent caller decode, RTP continuity/unaltered delivered prefixes and full raw PCM reconstruction. Confirms a controlled 120ms delay-growth counterexample with the 40ms DISCARD_NONE candidate. No fix, full DOS workflow or physical hardware acceptance.')
 (out/'delay-increase-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(diagnostic_verification_passed=result['diagnostic_verification_passed'],checks=checks,silence_insertions=insertions)))
 assert result['diagnostic_verification_passed']


if __name__=='__main__':main()
