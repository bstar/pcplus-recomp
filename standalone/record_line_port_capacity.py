#!/usr/bin/env python3
"""Record paired passive heap-resize evidence, never a release acceptance."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('candidate','control','default-observer','previous-observer','output'):
  p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();receipts={};sources={}
 def read(folder):
  folder=folder.resolve();r=json.loads((folder/'result.json').read_text())
  assert folder.is_relative_to(ROOT/'build') and r['cpu']=='386'
  assert r['heap_resize_watch'] and r['exit_watch_high']
  assert r['exit_watch']['resident_segment']>=0xa000
  assert r['nested_child_count']==3 and r['held_streams'] and r['streams_around_child'] and r['emulate_profile_switch']
  for n,h in r['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
  receipts[str((folder/'result.json').relative_to(ROOT))]=sha(folder/'result.json')
  assert sha(folder/'EWATCH.COM')==r['observer_sha256']
  receipts[str((folder/'EWATCH.COM').relative_to(ROOT))]=r['observer_sha256']
  capture=ROOT/'build/connection-dos'/folder.name
  for n in ('EXITSTAT.BIN','SCREEN.BIN','screen.txt','result.json'):
   receipts[str((capture/n).relative_to(ROOT))]=sha(capture/n)
  return r
 bad=read(a.candidate);good=read(a.control)
 assert not bad['passed'] and good['passed'] and all(good['checks'].values())
 assert bad['binary_sha256']=='a057b35cfa1d187e0a355cee62ac3c99489c226e499fe898bf6b5a2722aef134'
 assert good['binary_sha256']=='856a9c85887312099ae92a9f47592ca8b04f6812e7e6e404ad240bad63a6f6d7'
 assert bad['interpreter_sha256']==good['interpreter_sha256']=='5c641ac458494d8d6d7cb048d13dc531830689a4e401df7011092057c37ef066'
 failures=[r for r in bad['exit_watch']['allocations']if r['request_ah']==0x4a and r['carry']]
 assert failures and all(r['ax']==8 and r['paragraphs']==8259 and r['bx']==8228 for r in failures)
 assert all(r['mcb_owner_before']==r['target_es']for r in failures)
 assert [r['exit']for r in bad['exit_watch']['exits']]==[7,0,0,7]
 assert all(r['ds']==r['ss'] and not r['cleanup_error'] and not r['process_busy'] and not r['program_busy']for r in bad['exit_watch']['exits'])
 assert [r['exit']for r in good['exit_watch']['exits']]==[0,0,0,0]
 successes=[r for r in good['exit_watch']['allocations']if r['request_ah']==0x4a and not r['carry']]
 peak=max(r['paragraphs']for r in successes);maximum=failures[0]['bx']
 assert peak==8675 and (peak-maximum)*16==7152
 old=a.previous_observer.resolve();new=a.default_observer.resolve()
 assert old.is_relative_to(ROOT/'build') and new.is_relative_to(ROOT/'build')
 assert old.read_bytes()==new.read_bytes()
 for path in (old,new):receipts[str(path.relative_to(ROOT))]=sha(path)
 for n in ('standalone/record_line_port_capacity.py','docs/LINE_PORT_CAPACITY.md'):
  sources[n]=sha(ROOT/n)
 result=dict(diagnostic_verified=True,release_eligible=False,installed_package_changed=False,
  candidate_parent_sha256=bad['binary_sha256'],control_parent_sha256=good['binary_sha256'],
  interpreter_sha256=bad['interpreter_sha256'],control_checks=len(good['checks']),
  candidate_failed_resize_requests=len(failures),first_requested_paragraphs=8259,
  maximum_reported_paragraphs=maximum,first_request_shortfall_bytes=(8259-maximum)*16,
  control_maximum_observed_successful_paragraphs=peak,
  observed_control_extent_exceeds_candidate_maximum_bytes=(peak-maximum)*16,
  default_observer_unchanged=True,default_observer_sha256=sha(new),sources=sources,receipts=receipts,
  limitations=['Separate 386/UMB diagnostic. The passive observer changes the environment; it does not replace ordinary unobserved 8086 acceptance.',
   'Only the first 16 admitted child allocation/resize requests are captured. Observed extent is a lower bound, not a complete peak or sufficient funding target.',
   'AH=4A carry/AX=8 proves DOS resize refusal in this run. It does not by itself identify each CRT allocation owner or establish a general physical-memory requirement.',
   'No application fix, module unload/reload, deployment or physical compatibility claim.'])
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('Verified DOS resize failure: 496-byte immediate shortfall; observed control extent +7152 bytes; release remains ineligible')


if __name__=='__main__':main()
