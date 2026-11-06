#!/usr/bin/env python3
"""Bind the composed public package, source reproduction and DOS launch tests."""
import argparse,json
from pathlib import Path
from package_connection_test import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();receipts={};sources={}
 def load(name):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed'],name;receipts[name]=sha(path)
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n;sources[n]=h
  return r
 build=ROOT/'build/chat-help-connection-final-20261106';b=load(str(build.relative_to(ROOT))+'/result.json')
 m=json.loads((build/'package/manifest.json').read_text());assert sha(build/'package/manifest.json')==b['package_manifest_sha256'] and m['files']==b['files'] and not m['original_inputs'] and not m['card_written']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 for n,h in m['files'].items():assert sha(build/'package/PCPLUS'/n)==h,n
 assert len(m['files'])==13 and not any(Path(n).suffix.upper() in ('.PRM','.DIR','.KEY','.KBD','.XLT','.FON') for n in m['files'])
 recipe=ROOT/'standalone/chat_help_connection_candidate_recipe.json';r=json.loads(recipe.read_text());assert sha(recipe)==b['recipe_sha256'] and r['expected_files']==m['files'] and r['expected_archive_sha256']==b['archive_sha256']
 cold=load('build/chat-help-connection-source-proof-20261106/result.json');assert cold['files']==m['files'] and cold['archive_sha256']==b['archive_sha256'] and cold['ancestor_git_unavailable'] and not cold['original_inputs']
 archive=load('build/chat-help-connection-final-20261106/archive/result.json');assert archive['archive_sha256']==sha(build/'archive/PCPLUSSE.ZIP')==b['archive_sha256']
 guard=load('docs/validation/chat-help-geometry.json')
 for n,h in guard['products'].items():assert m['files'][n]==h,n
 assert m['files']['ASPECT.EXE']=='cbdee1949f0ac6bba34f56ae9c594a17888ef9b5143ee5dca9cd76498737ccfd'
 tests=[]
 for name in ('chat','splash','setup','precompile'):
  test=load('build/chat-help-package-accepted-'+name+'-20261106/result.json')
  assert test['package_manifest_sha256']==sha(build/'package/manifest.json') and test['package_files']==m['files'] and test['port']==3 and test['irq']==5 and test['cpu']=='8086'
  assert test['chat_help']==(name=='chat') and test['precompiled_before_terminal']==(name=='precompile')
  assert test['bios_port_omitted']==(name in ('chat','precompile'))
  for n,h in test['artifacts'].items():assert sha(ROOT/('build/chat-help-package-accepted-'+name+'-20261106')/n)==h,n
  tests.append(dict(case=name,checks=test['checks']))
 default=load('build/chat-help-package-default-control-20261106/result.json');assert default['archive_sha256']=='ea5df2d8043ba2fe351f8b8bcfdde228cc4c4d17769d9ef9b5a5a4d9a5e34df5' and len(default['files'])==10
 sources['standalone/record_chat_help_release.py']=sha(Path(__file__))
 result=dict(passed=True,files=m['files'],archive_sha256=archive['archive_sha256'],archive_bytes=archive['archive_bytes'],sources=sources,receipts=receipts,DOS_tests=tests,
  summary=dict(public_package_files=13,cold_source_files=cold['source_count'],launch_tests=4,COM=3,IRQ=5,BIOS_unlisted_cases=2,source_application_commit=m['source_base_commit'],source_package_commit=cold['source_commit']),
  limitations=['Dummy UART package tests do not establish physical Boca/SIP/audio or real CTS timing.',
   'BBS/editor/reconnect evidence is linked by exact product identities from the preceding geometry checkpoint; not rerun from the ZIP here.',
   'Separate application parity inventory and physical runtime acceptance remain open. This receipt does not select or install a release.'],
  scope=__doc__+' Source-only matched snapshot-lease parent/ASPECT, Chat overlay, PCHELP and authored resources. Four actual DOS8086 START/SETUP cases preserve private synthetic files and hardware/environment, capture original magenta LoC splash and exact Chat/Help/Chat frame/cursor/AB. Public archive excludes private settings/history; earlier default archive reproduces unchanged.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS composed connection package and source/launcher acceptance')
if __name__=='__main__':main()
