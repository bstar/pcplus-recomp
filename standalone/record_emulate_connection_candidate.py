#!/usr/bin/env python3
"""Bind the matched EMULATE package, DOS launch checks and public-source rebuild."""
import argparse,json
from pathlib import Path
from package_connection_test import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sources={};receipts={}
 def bind(items):
  for n,h in items.items():assert sha(ROOT/n)==h,n;sources[n]=h
 def load(name):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed'],name;receipts[name]=sha(path);bind(r.get('sources',{}));return r
 build=ROOT/'build/emulate-connection-candidate-20261107';r=load(str((build/'result.json').relative_to(ROOT)))
 recipe_path=ROOT/'standalone/emulate_connection_candidate_recipe.json';recipe=json.loads(recipe_path.read_text());assert sha(recipe_path)==r['recipe_sha256']
 package=build/'package';m=json.loads((package/'manifest.json').read_text());bind(m['sources']);receipts[str((package/'manifest.json').relative_to(ROOT))]=sha(package/'manifest.json')
 assert m['parent_render_capability']==20 and m['experimental_alarm_VM'] and m['experimental_emulate_VM'] and not m['card_written']
 assert m['files']==r['files']==recipe['expected_files'] and len(m['files'])==13
 for n,h in m['files'].items():assert sha(package/'PCPLUS'/n)==h,n
 archive=load(str((build/'archive/result.json').relative_to(ROOT)));assert archive['archive_sha256']==r['archive_sha256']==recipe['expected_archive_sha256']
 assert sha(build/'archive/PCPLUSSE.ZIP')==archive['archive_sha256']
 contract=load('build/emulate-package-contract-20261107/result.json');assert len(contract['cases'])==9
 modes=[]
 for mode in ('precompile','setup','splash','chat-help'):
  root=ROOT/'build'/('emulate-package-'+mode+'-20261107');x=load(str((root/'result.json').relative_to(ROOT)))
  assert x['package_manifest_sha256']==sha(package/'manifest.json') and x['package_files']==m['files'] and len(x['private_fixture_sha256'])==6
  assert x['cpu']=='8086' and x['port']==3 and x['irq']==5
  if mode=='precompile':assert x['packaged_ASPECT_EMULATE_exercised'] and x['packaged_ASPECT_clock_alarm_exercised'] and x['bios_port_omitted']
  if mode=='chat-help':assert x['chat_help']
  for name,h in x['artifacts'].items():assert sha(root/name)==h,name
  modes.append(dict(mode=mode,checks=x['checks'],private_files=6,EMULATE=x['packaged_ASPECT_EMULATE_exercised']))
 cold=load('build/emulate-connection-public-source-20261107/result.json')
 assert cold['files']==m['files'] and cold['archive_sha256']==r['archive_sha256'] and cold['ancestor_git_unavailable'] and cold['original_inputs']==[]
 products={n:m['files'][n]for n in ('TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE')}
 prior=ROOT/'docs/validation/aspect-emulate-integration.json';old=json.loads(prior.read_text());assert old['passed'] and old['products']==products
 receipts[str(prior.relative_to(ROOT))]=sha(prior)
 prior=ROOT/'docs/validation/aspect-emulate-io.json';old=json.loads(prior.read_text());assert old['passed'] and old['products']=={n:products[n]for n in ('TERMINAL.EXE','ASPECT.EXE')}
 receipts[str(prior.relative_to(ROOT))]=sha(prior)
 sources['standalone/record_emulate_connection_candidate.py']=sha(Path(__file__))
 report=dict(passed=True,software_package_verified=True,release_selected=False,installed_changed=False,files=m['files'],archive_sha256=r['archive_sha256'],products=products,sources=sources,receipts=receipts,original_inputs=[],summary=dict(package_files=13,executables=5,contract_cases=9,DOS_modes=modes,cold_source_files=cold['source_count'],source_export_commit=cold['source_commit'],source_base_commit=r['source_base_commit']),
  limitations=['Exact archived public payload and clean public-source reproduction; no originals/private configuration/prior objects/Git metadata in the exported build. Outer pinned Nix bootstrap runs in the working checkout.',
   'DOS8086 tests use synthetic six-file configuration/call-history sentinels and dummy UART. Actual packaged compiler/EMULATE/ALARM/DATE/TIME, launchers, splash and Chat/Help are checked; physical hardware/analog/SIP/audio and every original feature are not.',
   'Prior Enigma/Synchronet/bridge/WHEN/strict-IO/receive results apply to the identical application hashes. Those records remain historical source snapshots; packaging-only helper changes do not repeat all old runtime matrices.',
   'Software package verification does not select/deploy it or close native abort/fatal-reset expansion, stronger sustained flow/headroom or physical acceptance. Keep installed R59A85A8 until a separately recorded selection/deployment.'],scope=__doc__)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS matched EMULATE public package',report['summary'])
if __name__=='__main__':main()
