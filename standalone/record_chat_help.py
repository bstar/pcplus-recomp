#!/usr/bin/env python3
"""Bind the opt-in Chat Help checkpoint without claiming unrun BBS/hardware gates."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('package','cold','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();package=a.package.resolve();cold_dir=a.cold.resolve()
 assert package.is_relative_to(ROOT/'build') and cold_dir.is_relative_to(ROOT/'build')
 m=json.loads((package/'manifest.json').read_text());bundle=json.loads((package/'package.json').read_text());sources=dict(bundle['sources']);receipts={}
 assert m['experimental_chat_help'] and bundle['mapped_contexts']==[3,41]
 for name,digest in bundle['products'].items():assert sha(package/name)==digest,name
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT)
  r=json.loads(path.read_text());assert r['passed'],path;receipts[str(path.relative_to(ROOT))]=sha(path)
  for name,digest in r.get('sources',{}).items():
   assert sha(ROOT/name)==digest,name
   assert name not in sources or sources[name]==digest,name
   sources[name]=digest
  return r
 cold=load(cold_dir/'result.json');assert cold['products']==bundle['products']
 assert {r['case'] for r in cold['runs']}=={'normal','flow','Chat-25','Chat-50'}
 for r in cold['runs']:assert all(r['checks'].values())
 for name,digest in cold['overlay_sources'].items():assert sha(ROOT/name)==digest,name
 for rows in (25,50):
  r=load(cold_dir/f'source/build/chat-help-{rows}/result.json')
  assert r['products']==bundle['products'] and r['rows']==rows and all(r['checks'].values())
  assert r['observer_words'][:2]==[0x4847,3] and r['observer_words'][3]==rows
 aspect=load(ROOT/'build/chat-help-aspect-candidate-20261106/result.json')
 assert aspect['binary_sha256']==bundle['products']['TERMINAL.EXE'] and all(aspect['checks'].values())
 assert len(aspect['checks'])==25
 paths=load(ROOT/'build/chat-help-paths-size-20261106/result.json')
 assert paths['optimized_shared'] and paths['cases']==2688 and paths['base']=='RESOURCE PATH PASS 30 checks'
 control=ROOT/'build/chat-help-disabled-final-20261106/TERMINAL.EXE'
 control_m=json.loads(control.with_name('manifest.json').read_text())
 for name,digest in control_m['sources'].items():assert sha(ROOT/name)==digest,name
 assert not control_m['experimental_chat_help'] and sha(control)=='471d58567f8a20ceb1ca4686347313fdd2237faabe057a0d306bb0c8477749f4'
 layout=m['memory_layout'];assert layout['minimum_allocated_module_bytes']==479392 and m['data_stack_bytes']==65504 and layout['resident_code_bytes']==65452
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 sources['standalone/record_chat_help.py']=sha(Path(__file__))
 report=dict(passed=True,products=bundle['products'],sources=sources,receipts=receipts,
  disabled_control_sha256=sha(control),mapped_contexts=bundle['mapped_contexts'],
  parent_memory=dict(minimum_DOS_bytes=479392,DS_SS_bytes=65504,resident_CS_bytes=65452,stack_bytes=8192),
  summary=dict(Chat_main_rows=[25,50],cold_source_files=cold['source_files'],cold_cases=[r['case'] for r in cold['runs']],ASPECT_checks=25,path_pair_cases=2688,path_bounds_checks=30),
  limitations=['Positive normal-main Chat Help only; module memory identity not independently sampled.',
   'Busy parser/TEXT, deferred queue, repeated Help, failure/RX/flow/geometry edges remain open.',
   'Current-parent Enigma/Synchronet regressions not yet run; prior-parent BBS evidence not relabeled.',
   'No physical deployment/acceptance, SIP/audio acceptance, other contexts or full original parity.'],
  scope='Opt-in source-built Chat context3 Help through private PROGRAM admission, exact frame/cursor and unfinished-line return at25/50 rows, cold exact products, existing reference normal/flow, six-stream/nested-ASPECT and optimized scanner comparison. Failed oversized candidates retained and rejected.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
 print('PASS Chat Help checkpoint',bundle['products']['TERMINAL.EXE'])
if __name__=='__main__':main()
