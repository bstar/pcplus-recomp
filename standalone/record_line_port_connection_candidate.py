#!/usr/bin/env python3
"""Bind the exact Alt-P package, DOS workflows and public-source reproduction."""
import argparse,json
from pathlib import Path
from package_connection_test import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','contract','proof','control','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--modes-prefix',required=True);a=p.parse_args();sources={};receipts={}
 def bind(items):
  for n,h in items.items():
   path=(ROOT/n).resolve();assert path.is_relative_to(ROOT) and sha(path)==h,n
   (receipts if path.is_relative_to(ROOT/'build') else sources)[str(path.relative_to(ROOT))]=h
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT/'build')
  receipts[str(path.relative_to(ROOT))]=sha(path);v=json.loads(path.read_text());assert v['passed'],path
  bind(v.get('sources',{}));return v
 build=a.build.resolve();r=load(build/'result.json');package=build/'package'
 recipe=ROOT/'standalone/line_port_connection_candidate_recipe.json';declared=json.loads(recipe.read_text())
 assert sha(recipe)==r['recipe_sha256']
 m=json.loads((package/'manifest.json').read_text());bind(m['sources']);receipts[str((package/'manifest.json').relative_to(ROOT))]=sha(package/'manifest.json')
 assert m['files']==r['files']==declared['expected_files'] and len(m['files'])==14
 assert m['original_inputs']==[] and not m['card_written'] and m['dos_directory']=='PCPLUS'
 assert m['experimental_line_port_overlay'] and m['parent_render_capability']==20 and m['experimental_emulate_VM']
 for name,h in m['files'].items():assert sha(package/'PCPLUS'/name)==h,name
 archive=load(build/'archive/result.json')
 assert sha(build/'archive/PCPLUSSE.ZIP')==archive['archive_sha256']==r['archive_sha256']==declared['expected_archive_sha256']
 prior=ROOT/'docs/validation/line-port-overlay.json';core=json.loads(prior.read_text());receipts[str(prior.relative_to(ROOT))]=sha(prior)
 assert core['named_application_gates_passed'] and core['aspect_capacity_gate_passed'] and core['carrier']['independently_audited']
 assert set(core['bbs'])=={'enigma','synchronet'}
 for name,h in core['products'].items():assert m['files'][name]==h,name
 contract=load(a.contract.resolve()/'result.json');assert len(contract['cases'])==14
 assert contract['terminal_sha256']==m['files']['TERMINAL.EXE'] and contract['overlay_sha256']==m['files']['PCLINE.OVL']
 assert contract['package_manifest_sha256']==sha(package/'manifest.json')
 modes=[]
 for mode in ('precompile','setup','splash','chat-help','line-port'):
  root=ROOT/'build'/f'{a.modes_prefix}-{mode}-20261107';v=load(root/'result.json')
  assert v['package_manifest_sha256']==sha(package/'manifest.json') and v['package_files']==m['files']
  assert v['cpu']=='8086' and v['port']==3 and v['irq']==5 and len(v['private_fixture_sha256'])==6
  if mode=='precompile':assert v['packaged_ASPECT_EMULATE_exercised'] and v['packaged_ASPECT_clock_alarm_exercised'] and v['bios_port_omitted']
  if mode=='line-port':assert v['native_line_port']
  if mode=='chat-help':assert v['chat_help']
  for n,h in v['artifacts'].items():assert sha(root/n)==h,n
  modes.append(dict(mode=mode,checks=v['checks'],private_files=6))
 cold=load(a.proof.resolve()/'result.json')
 assert cold['files']==m['files'] and cold['archive_sha256']==r['archive_sha256'] and cold['ancestor_git_unavailable'] and cold['original_inputs']==[]
 control=load(a.control.resolve()/'result.json');legacy=json.loads((ROOT/'standalone/emulate_connection_candidate_recipe.json').read_text())
 assert control['files']==legacy['expected_files'] and len(control['files'])==13
 assert control['archive_sha256']==legacy['expected_archive_sha256']
 assert sha(a.control.resolve()/'archive/PCPLUSSE.ZIP')==control['archive_sha256']
 sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
 report=dict(passed=True,software_package_verified=True,release_selected=False,installed_changed=False,physical_runtime_verified=False,
  products={n:m['files'][n] for n in ('TERMINAL.EXE','PCLINE.OVL','ASPECT.EXE','ASPCOMP.EXE')},files=m['files'],archive_sha256=r['archive_sha256'],
  summary=dict(package_files=14,executables=5,contract_cases=14,DOS_modes=modes,cold_source_files=cold['source_count'],source_export_commit=cold['source_commit'],source_base_commit=r['source_base_commit'],previous_13_file_archive_reproduced=True),
  sources=sources,receipts=receipts,original_inputs=[],
  limitations=['Public-source rebuild reproduces every file and deterministic archive; no originals, private settings, prior objects or Git metadata in the export. Pinned Nix bootstrap is run in the outer checkout.',
   'Actual DOS8086 package workflows use dummy UARTs and six synthetic private-file sentinels. Prior native capacity and BBS receipts apply to the identical parent/module/interpreter; their historical source snapshots are retained.',
   'This records software acceptance only; release selection, verified deployment, physical Boca/SPA2102/SynthModem acceptance, broader fault/flow and full original feature parity remain separate.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
 print('PASS matched Alt-P package:14 files,14 admission cases,5 DOS modes,exact source reproduction; no selection/deployment')


if __name__=='__main__':main()
