#!/usr/bin/env python3
"""Bind the accepted global Help candidate to its retained DOS/BBS evidence."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--package',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();package=a.package.resolve()
 assert package.is_relative_to(ROOT/'build')
 m=json.loads((package/'manifest.json').read_text())
 bundle=json.loads((package/'package.json').read_text());products=bundle['products'];sources=dict(bundle['sources'])
 for name,digest in products.items():assert sha(package/name)==digest,name
 def load(path):
  file=ROOT/path;report=json.loads(file.read_text());assert report['passed'],path
  for name,digest in report.get('sources',{}).items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
  return report,dict(path=path,sha256=sha(file))
 paths={case:f'build/global-help-shared-{case}-20261106/result.json' for case in ['normal','repeat','missing-helper','missing-resource','bad-resource','flow']}
 paths.update(cold='build/global-help-shared-cold-final-20261106/result.json',
  paths='build/global-help-resource-pair-final-20261106/result.json',
  ASPECT='build/global-help-shared-aspect-20261106/result.json',
  Chat_lease='build/global-help-chat-lease-20261106/result.json',
  Chat_main50='build/global-help-chat-main50-20261106/result.json',
  Synchronet='build/bbs-lab/results/synchronet/global-help-sync-layout-20261106/proxy-integration.json',
  Enigma='build/bbs-lab/results/enigma/global-help-enigma-dev-20261106/carrier-checks.json',
  Enigma_audit='build/global-help-enigma-audit-20261106/result.json')
 reports={};receipts={}
 for name,path in paths.items():reports[name],receipts[name]=load(path)
 for case in ['normal','repeat','missing-helper','missing-resource','bad-resource','flow']:
  r=reports[case];assert r['case']==case and r['products']==products and all(r['checks'].values())
 assert reports['cold']['products']==products and reports['cold']['source_files']==5296
 for name,digest in reports['cold']['overlay_sources'].items():assert sha(ROOT/name)==digest,name
 assert reports['paths']['cases']==2688 and reports['paths']['base'].startswith('RESOURCE PATH PASS')
 for case in ['ASPECT','Chat_lease','Chat_main50','Synchronet']:
  assert reports[case]['binary_sha256']==products['TERMINAL.EXE'],case
 assert len(reports['ASPECT']['checks'])==25 and all(reports['ASPECT']['checks'].values())
 assert reports['ASPECT']['interpreter_sha256']=='cbdee1949f0ac6bba34f56ae9c594a17888ef9b5143ee5dca9cd76498737ccfd'
 assert reports['Chat_lease']['checks']==75085
 assert all(reports['Chat_main50']['checks'].values()) and reports['Chat_main50']['rows']==50
 assert len(reports['Synchronet']['checks'])==25 and all(reports['Synchronet']['checks'].values())
 assert reports['Enigma']['products']['TERMINAL.EXE']['sha256']==products['TERMINAL.EXE'] and all(reports['Enigma']['checks'].values())
 assert reports['Enigma_audit']['terminal_sha256']==products['TERMINAL.EXE'] and reports['Enigma_audit']['exact_retry_bytes']==65539
 layout=m['memory_layout']
 assert layout['minimum_allocated_module_bytes']==479408 and m['data_stack_bytes']==65504 and layout['resident_code_bytes']==65440
 control=ROOT/'build/global-help-control-final-20261106/TERMINAL.EXE'
 assert sha(control)=='0ba3c1f6f9af368a5d62d4dd43b9d4ff3f19b561e5d0de946faaa65a78121a0e'
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 sources['standalone/record_global_help.py']=sha(Path(__file__))
 report=dict(passed=True,products=products,sources=sources,receipts=receipts,
  parent_memory=dict(minimum_DOS_bytes=479408,DS_SS_bytes=65504,resident_CS_bytes=65440,stack_bytes=8192),
  disabled_control_sha256=sha(control),ASPECT_sha256=reports['ASPECT']['interpreter_sha256'],
  summary=dict(Help_cases=6,paired_path_cases=2688,Chat_lease_checks=75085,ASPECT_checks=25,Synchronet_checks=25,Enigma_exact_retry_bytes=65539,cold_source_files=5296),
  limitations=['Only reference Help context41 wired; authored47-topic resource, no original help prose.',
   'Main Help tests at25 rows; unchanged helper comparison separately covers25/50 rows.',
   'BBS tests exercise the current parent without invoking Help during the BBS session.',
   'Native unresolved UI word defaults0; full mouse semantics and helper mouse navigation remain open.',
   'No physical deployment/acceptance, SIP/audio acceptance or full original feature parity.'],
  scope='Exact source-only global Help package with real-DOS main/flow/failure/ASPECT/Chat checks, independent cold rebuild and actual owned Enigma/Synchronet regressions. Earlier oversized parent rejected; disabled control unchanged.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
 print('PASS global Help receipt',products['TERMINAL.EXE'])
if __name__=='__main__':main()
