#!/usr/bin/env python3
"""Bind the exact optional Alt-P parent and its observed application gates."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha
CASES=('noop','escape','save','reference','browser','serviced','unsupported','readonly','conflict','portbusy')


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('parent','control','proof','move','capacity-control','capacity-failure','capacity-failure-report','runner'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--cases-prefix',required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();parent=a.parent.resolve();control=a.control.resolve();proof=a.proof.resolve();move=a.move.resolve()
 m=json.loads((parent/'manifest.json').read_text());c=json.loads((control/'manifest.json').read_text())
 product=sha(parent/'TERMINAL.EXE');assert m['experimental_line_port'] and m['binary_sha256']==product
 assert not c['experimental_line_port'] and c['binary_sha256']==sha(control/'TERMINAL.EXE')=='856a9c85887312099ae92a9f47592ca8b04f6812e7e6e404ad240bad63a6f6d7'
 sources={};receipts={};cases=[]
 def record(path):receipts[str(path.relative_to(ROOT))]=sha(path);return json.loads(path.read_text())
 def check_sources(values):
  for n,h in values.items():assert sha(ROOT/n)==h,n;sources[n]=h
 check_sources(m['sources']);check_sources(c['sources'])
 record(parent/'manifest.json');record(control/'manifest.json')
 for case in CASES:
  path=ROOT/'build'/f'{a.cases_prefix}-{case}-20261107/result.json'
  r=record(path);assert r['passed'] and r['binary_sha256']==product and all(r['checks'].values())
  check_sources(r['sources']);base=record(Path(r['base_receipt']));assert base['passed'] and base['binary_sha256']==product
  cases.append(dict(case=case,checks=len(r['checks']),post_lcr=r['post_lcr']))
 q=record(proof/'result.json');assert q['passed'] and q['binary_sha256']==product and q['ancestor_git_unavailable']
 check_sources(q['sources']);assert [r['case']for r in q['runs']]==['save','serviced','readonly','portbusy']
 assert all(all(r['checks'].values())for r in q['runs'])
 v=record(move/'result.json');assert v['passed'] and v['terminal_sha256']==product and v['result']['passed']
 assert all(v['result']['checks'].values());check_sources(v['sources'])
 for n,h in v['captures'].items():assert sha(move/n)==h,n;receipts[str((move/n).relative_to(ROOT))]=h
 for n in ('standalone/record_line_port_live.py','standalone/build_line_port_profile.py','docs/LINE_PORT_LIVE.md'):
  sources[n]=sha(ROOT/n)
 mem=m['memory_layout'];assert mem['near_bytes']==65520 and mem['resident_CS_extent_bytes']==65536
 assert mem['line_port_front_far_state_bytes']==256 and mem['line_port_front_DGROUP_bytes']==0
 # Keep successful UI evidence separate from the failed release gate. The
 # first run stopped on missing HOLD0.BIN; the fixed diagnostic records failure.
 runner=a.runner.resolve();rm=record(runner/'manifest.json')
 check_sources(rm['sources']);runner_sha=sha(runner/'ASPECT.EXE')
 assert runner_sha==rm['binary_sha256']=='5c641ac458494d8d6d7cb048d13dc531830689a4e401df7011092057c37ef066'
 cap=record(a.capacity_control.resolve()/'result.json')
 assert cap['passed'] and all(cap['checks'].values()) and len(cap['checks'])==29
 assert cap['binary_sha256']==c['binary_sha256'] and cap['interpreter_sha256']==runner_sha
 check_sources(cap['sources'])
 failure=a.capacity_failure.resolve();bad=record(failure/'result.json')
 assert not bad['passed'] and bad['binary_sha256']==product
 failed_report=record(a.capacity_failure_report.resolve()/'result.json')
 assert not failed_report['passed'] and not failed_report['checks']['held_files_preserved']
 assert failed_report['binary_sha256']==product and failed_report['interpreter_sha256']==runner_sha
 check_sources(failed_report['sources'])
 assert not (failure/'HOLD0.BIN').exists()
 assert 'invalid operand (error 7, opcode 41, step 9, native 4)' in (failure/'screen.txt').read_text()
 for n in ('SCREEN.BIN','screen.txt','FIRST.ASX','SIX.ASX','MISSING.ASX','NEST.COM','TEST.PRM'):
  receipts[str((failure/n).relative_to(ROOT))]=sha(failure/n)
 log=ROOT/'build/line-port-aspect-capacity-20261107-current-runner.log'
 assert 'FileNotFoundError' in log.read_text() and 'HOLD0.BIN' in log.read_text()
 receipts[str(log.relative_to(ROOT))]=sha(log)
 result=dict(named_application_gates_passed=True,release_eligible=False,aspect_capacity_gate_passed=False,
  aspect_capacity=dict(control_checks=29,control_passed=True,interpreter_sha256=runner_sha,
   candidate_first_held_file_missing=True,candidate_top_level_summary_available=True,
   observation='ASPECT invalid operand error 7, opcode 41, step 9; held stream file absent.',
   cause='Paired control establishes regression. Separate diagnostic observes DOS AH=4A refusal; precise CRT allocation owner remains uninstrumented.'),
  parent_sha256=product,control_sha256=c['binary_sha256'],
  application_cases=cases,application_checks=sum(r['checks']for r in cases),
  offline_move_checks=len(v['result']['checks']),source_files_in_export=q['source_count'],
  memory={n:mem[n]for n in ('near_bytes','near_spare_bytes','resident_CS_extent_bytes','resident_CS_spare_bytes','minimum_allocated_module_bytes','line_port_front_far_state_bytes','line_port_front_DGROUP_bytes')},
  sources=sources,receipts=receipts,release_selected=False,installed_package_changed=False,physical_runtime_verified=False,
  limitations=['Known ASPECT capacity regression: candidate fails held-stream/nested-child/profile-switch workload; unchanged parent passes 29 checks with the same interpreter. Do not promote.',
   'Named DOS synthetic-peer and offline-move gates only; BBS/transfers/reconnect/package regressions remain open for this parent.',
   '80x25 default-color comparison; other geometry/colors/full port matrix and live injected close/rollback uncertainty remain unverified.',
   'Physical Boca/SPA2102/SynthModem acceptance and full original feature parity are separate.'])
 assert result['application_checks']==257 and result['offline_move_checks']==17
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded Alt-P: 257 UI checks /17 move checks /cold reproduction; ASPECT capacity FAILED, control 29 passed; NOT release eligible')


if __name__=='__main__':main()
