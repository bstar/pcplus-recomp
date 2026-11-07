#!/usr/bin/env python3
"""Bind the transient Alt-P products and named application gates, not a release."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

CASES=('noop','escape','save','reference','browser','serviced','unsupported','readonly','conflict','portbusy')


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('parent','control','runner','capacity','around','move','proof','bridge','usage','output'):
  p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--cases-prefix',required=True);p.add_argument('--faults-prefix',required=True)
 for n in ('bbs-enigma','bbs-synchronet','carrier','carrier-audit'):
  p.add_argument('--'+n,type=Path)
 a=p.parse_args();sources={};receipts={}
 def read(path):
  path=path.resolve();assert path.is_relative_to(ROOT/'build')
  receipts[str(path.relative_to(ROOT))]=sha(path);return json.loads(path.read_text())
 def checked(values):
  for n,h in values.items():
   path=(ROOT/n).resolve();assert path.is_relative_to(ROOT) and sha(path)==h,n
   (receipts if path.is_relative_to(ROOT/'build') else sources)[str(path.relative_to(ROOT))]=h
 parent=a.parent.resolve();m=read(parent/'manifest.json');product=sha(parent/'TERMINAL.EXE')
 assert m['binary_sha256']==product and m['experimental_line_port_overlay']
 module=sha(parent/'PCLINE.OVL');assert module==m['line_port_overlay']['sha256']
 c=read(a.control.resolve()/'manifest.json');r=read(a.runner.resolve()/'manifest.json')
 assert c['binary_sha256']==sha(a.control.resolve()/'TERMINAL.EXE')=='856a9c85887312099ae92a9f47592ca8b04f6812e7e6e404ad240bad63a6f6d7'
 assert r['binary_sha256']==sha(a.runner.resolve()/'ASPECT.EXE')=='5c641ac458494d8d6d7cb048d13dc531830689a4e401df7011092057c37ef066'
 for manifest in (m,c,r):checked(manifest['sources'])
 cases=[]
 for case in CASES:
  v=read(ROOT/'build'/f'{a.cases_prefix}-{case}-20261107/result.json')
  assert v['passed'] and all(v['checks'].values()) and v['binary_sha256']==product and v['open_delay_ms']==1300
  checked(v['sources']);base=read(Path(v['base_receipt']));assert base['passed']
  cases.append(dict(case=case,checks=len(v['checks'])))
 capacity=[]
 for directory,around in ((a.capacity,False),(a.around,True)):
  v=read(directory.resolve()/'result.json');assert v['passed'] and all(v['checks'].values())
  assert v['cpu']=='8086' and not v['program_result_probe'] and v['line_port_around_scripts']==around
  assert v['held_streams'] and v['streams_around_child'] and v['nested_child_count']==3 and v['emulate_profile_switch']
  assert v['binary_sha256']==product and v['interpreter_sha256']==r['binary_sha256'] and v['overlay_sha256']==module
  checked(v['sources']);capacity.append(dict(around_popup=around,checks=len(v['checks'])))
 v=read(a.move.resolve()/'result.json');assert v['passed'] and v['terminal_sha256']==product and all(v['result']['checks'].values())
 checked(v['sources']);move_checks=len(v['result']['checks'])
 for n,h in v['captures'].items():assert sha(a.move.resolve()/n)==h
 q=read(a.proof.resolve()/'result.json');assert q['passed'] and q['binary_sha256']==product and q['overlay_sha256']==module and q['ancestor_git_unavailable']
 assert [v['case']for v in q['runs']]==['save','serviced','readonly','portbusy']
 assert all(all(v['checks'].values())for v in q['runs']);checked(q['sources'])
 b=read(a.bridge.resolve()/'result.json');assert b['passed'] and b['calls']==2200 and b['argument_counts']==list(range(11)) and b['cpu']=='8086'
 checked(b['sources'])
 u=read(a.usage.resolve()/'result.json');assert u['passed'] and u['parent_sha256']==product and u['control_sha256']==c['binary_sha256'] and u['overlay_sha256']==module
 assert [v['case']for v in u['cases']]==['control','same-drive','other-drive','missing'];checked(u['sources'])
 faults=[]
 for case in ('missing','short','corrupt','extra'):
  v=read(ROOT/'build'/f'{a.faults_prefix}-{case}-20261107/result.json')
  assert v['passed'] and all(v['checks'].values()) and v['parent_sha256']==product and v['expected_overlay_sha256']==module
  checked(v['sources']);faults.append(dict(case=case,checks=len(v['checks'])))
 bbs={}
 for name,directory in (('enigma',a.bbs_enigma),('synchronet',a.bbs_synchronet)):
  if directory is None:continue
  directory=directory.resolve();v=read(directory/'proxy-integration.json')
  assert v['passed'] and all(v['checks'].values()) and v['binary_sha256']==product
  assert v['bridge']['inputSequenceTimeoutMs']==250 and v['bridge']['inputByteDelayMs']==20 and v['bridge']['terminalSizeProbe']
  checked(v['product_inputs'])
  assert module in v['product_inputs'].values()
  screen=read(directory/'size-probe-screen-audit.json');external=read(directory/'external-viewer-audit.json')
  assert screen['passed'] and screen['binary_sha256']==product and screen['different_cells']==0 and screen['matched_cells']==1920
  assert external['passed'] and all(external['checks'].values())
  bbs[name]=dict(checks=len(v['checks']),external_viewer_checks=len(external['checks']),matched_cells=1920,different_cells=0,framing_ms=250,byte_delay_ms=20,size_probe=True)
 assert (a.carrier is None)==(a.carrier_audit is None)
 carrier=None
 if a.carrier is not None:
  v=read(a.carrier.resolve()/'carrier-checks.json');audit=read(a.carrier_audit.resolve()/'result.json')
  assert v['passed'] and all(v['checks'].values()) and not v['errors'] and audit['passed']
  assert v['products']['TERMINAL.EXE']['sha256']==audit['terminal_sha256']==product
  assert v['products']['ASPECT.EXE']['sha256']==r['binary_sha256']
  assert v['products']['ASPCOMP.EXE']['sha256']=='ac58a8a1ee07f6253b4dfb4d531eb1d456da3b6f7ea15afca8814db626e997e2'
  assert audit['exact_retry_bytes']==65539 and len(audit['sessions'])==2
  for record in (v,audit):checked(record['sources'])
  assert sha(a.carrier.resolve()/'program/PCLINE.OVL')==module
  carrier=dict(checks=len(v['checks']),exact_retry_bytes=65539,sessions=2,independently_audited=True)
 for n in ('standalone/record_line_port_overlay.py','standalone/build_line_port_profile.py','docs/LINE_PORT_OVERLAY.md'):
  sources[n]=sha(ROOT/n)
 mem=m['memory_layout'];assert mem['minimum_allocated_module_bytes']==479024 and mem['near_bytes']==65520
 assert mem['line_port_overlay_contract_verified'] and mem['configuration_cdecl_shared_entry_bytes']==30 and mem['configuration_cdecl_tail_frames_verified']
 result=dict(named_application_gates_passed=True,aspect_capacity_gate_passed=True,release_eligible=False,
  products={'TERMINAL.EXE':product,'PCLINE.OVL':module,'ASPECT.EXE':r['binary_sha256']},
  control_sha256=c['binary_sha256'],application_cases=cases,application_checks=sum(v['checks']for v in cases),
  capacity=capacity,offline_move_checks=move_checks,faults=faults,bridge_calls=2200,
  isolated_source_files=q['source_count'],startup_help_bytes=1492,
  memory={n:mem[n]for n in ('minimum_allocated_module_bytes','near_bytes','near_spare_bytes','resident_CS_extent_bytes','resident_CS_spare_bytes','line_port_overlay_bytes','line_port_overlay_state_bytes','line_port_overlay_usage_bytes')},
  module=m['line_port_overlay'],sources=sources,receipts=receipts,original_inputs=[],
  bbs=bbs,carrier=carrier,
  installed_package_changed=False,release_selected=False,physical_runtime_verified=False,
  limitations=['Named synthetic-peer/DOS/source gates; BBS receipts cover the recorded bridge profiles. Matched-package/deployment acceptance is separate.',
   'No physical analog/SIP/DCD/CTS claim, complete geometry/port-pair matrix or live injected close/rollback composition.',
   'Setup keys are handled after loading; Escape cancels before readiness. CRC binds bytes, not hostile-file authenticity.',
   'Full original feature inventory remains open.'])
 assert result['application_checks']==257 and move_checks==18 and all(v['checks']==30 for v in capacity)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded transient Alt-P:257 UI,18 move,2x30 capacity,2200 ABI calls,4 module faults,exact source reproduction; no deployment')


if __name__=='__main__':main()
