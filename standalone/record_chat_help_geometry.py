#!/usr/bin/env python3
"""Bind the geometry admission fix to frozen negative and current DOS evidence."""
import argparse,json,struct
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 sources={};receipts={}
 def load(name,positive=True,frozen=False):
  path=ROOT/name;r=json.loads(path.read_text());assert r['passed']==positive,name;receipts[name]=sha(path)
  for n,h in r.get('sources',{}).items():
   assert sha(path.parent/'sources'/n if frozen else ROOT/n)==h,n
   if not frozen:
    assert n not in sources or sources[n]==h,n
    sources[n]=h
  return r
 prefix='build/chat-help-geometry-'
 package=load(prefix+'first-20261106/package.json');products=package['products']
 for n,h in products.items():assert sha(ROOT/(prefix+'first-20261106')/n)==h,n
 assert products['TERMINAL.EXE']=='fab5ac9e046627b3f59050619acf4508b3703a3b4f04455bcb9bdb8104be6dd0'
 manifest=json.loads((ROOT/(prefix+'first-20261106/manifest.json')).read_text());layout=manifest['memory_layout']
 assert manifest['data_stack_bytes']==65504 and layout['resident_CS_extent_bytes']==65452 and layout['minimum_allocated_module_bytes']==479408
 matrix=load(prefix+'matrix-20261106/result.json');assert matrix['binary_sha256']==products['TERMINAL.EXE'] and matrix['module_sha256']==products['PCCHAT.OVL']
 assert len(matrix['cases'])==12 and {(c['rows'],c['fault']) for c in matrix['cases']}=={(r,f) for r in (25,28,43,50) for f in (0,1,2)}
 count=0
 for c in matrix['cases']:
  assert c['passed'] and c['exit_code']==0 and sha(ROOT/c['receipt'])==c['receipt_sha256']
  r=load(c['receipt']);assert r['errors']==0 and r['binary_sha256']==products['TERMINAL.EXE'] and not r['original_inputs'];count+=r['checks']
  for n,h in r['artifacts'].items():assert sha((ROOT/c['receipt']).parent/n)==h,n
 assert count==206028
 negative=load(prefix+'old-mode13-probe-20261106/result.json',False,True)
 assert negative['binary_sha256']=='6fd8aafc3fa06155239bd209f3c1b152959eea0d820b70eb7af24e73ae58ce10' and negative['module_sha256']==products['PCCHAT.OVL']
 assert negative['checks']==34018 and negative['errors']==1 and negative['output']=='FAIL line 65\nHELPGEOM rows=25 fault=2 checks=34018 errors=1\n' and not negative['original_inputs']
 assert [n for n,h in negative['sources'].items() if sha(ROOT/n)!=h]==['src/chat/frontend.c']
 negdir=ROOT/(prefix+'old-mode13-probe-20261106')
 for n,h in negative['artifacts'].items():assert sha(negdir/n)==h,n
 assert sha(negdir/'drive/PARENT.EXE')==negative['binary_sha256']
 recovery=load(prefix+'recovery-matrix-20261106/result.json');busy=load(prefix+'busy-matrix-20261106/result.json')
 assert len(recovery['cases'])==24 and len(busy['cases'])==8
 for group in (recovery,busy):
  assert group['products']==products
  for c in group['cases']:
   assert c['passed'] and c['exit_code']==0 and sha(ROOT/c['receipt'])==c['receipt_sha256']
   r=load(c['receipt']);assert r['products']==products and all(r['checks'].values())
 cold=load(prefix+'cold-20261106/result.json');assert cold['products']==products and cold['source_files']==5323 and len(cold['runs'])==6
 for n,h in cold['overlay_sources'].items():assert sha(ROOT/n)==h,n
 for c in cold['runs']:assert all(c['checks'].values())
 aspect=load(prefix+'aspect-20261106/result.json');assert aspect['binary_sha256']==products['TERMINAL.EXE'] and len(aspect['checks'])==25 and all(aspect['checks'].values())
 cap='build/bbs-lab/results/enigma/chat-help-geometry-editor-20261106/'
 editor=load(cap+'proxy-integration.json');chat=load(cap+'chat-help-audit.json');cells=load(cap+'screen-reference-audit.json');size=load(cap+'size-probe-screen-audit.json')
 assert editor['binary_sha256']==products['TERMINAL.EXE'] and all(editor['checks'].values()) and chat['proof']['products']==products and all(chat['checks'].values())
 assert cells['different_cells']==0 and cells['matched_cells']==1920 and cells['actual_CPR']==[9,8] and all(cells['checks'].values()) and size['NAWS']==[[80,24]]
 raw=(ROOT/cap/'BBHELP.BIN').read_bytes();assert len(raw)==20052;w=struct.unpack_from('<26H',raw);frames=[raw[52+i*4000:52+(i+1)*4000] for i in range(5)]
 assert frames[0]==frames[4] and frames[1]==frames[3] and w[6]==w[10] and w[11]==w[15] and w[7]==w[9] and w[12]==w[14]
 assert all(b'ON-LINE' in frames[i][3840::2] for i in (0,4))
 controls=load(prefix+'screen-controls-20261106/result.json');assert len(controls['cases'])==9 and all(c['passed'] and c['rejected']==(c['case']!='unchanged') for c in controls['cases'])
 sync=load('build/bbs-lab/results/synchronet/chat-help-geometry-sync-20261106/proxy-integration.json');assert sync['binary_sha256']==products['TERMINAL.EXE'] and all(sync['checks'].values())
 carrier=load('build/bbs-lab/results/enigma/chat-help-geometry-carrier-20261106/carrier-checks.json');audit=load(prefix+'carrier-audit-20261106/result.json')
 assert carrier['products']['TERMINAL.EXE']['sha256']==audit['terminal_sha256']==products['TERMINAL.EXE'] and all(carrier['checks'].values()) and not carrier['errors'] and audit['exact_retry_bytes']==65539
 for n,h in audit['captures'].items():assert sha(ROOT/n)==h,n
 disabled=load(prefix+'disabled-20261106/package.json');assert disabled['products']['TERMINAL.EXE']=='471d58567f8a20ceb1ca4686347313fdd2237faabe057a0d306bb0c8477749f4'
 assert all(disabled['products'][n]==h for n,h in products.items() if n!='TERMINAL.EXE')
 sources['standalone/record_chat_help_geometry.py']=sha(Path(__file__))
 result=dict(passed=True,products=products,sources=sources,receipts=receipts,
  summary=dict(geometry_cases=12,geometry_checks=count,old_parent_negative_checks=34018,old_parent_expected_errors=1,recovery_sessions=24,busy_sessions=8,cold_sessions=6,cold_source_files=5323,ASPECT_checks=25,minimum_module_bytes=479408,minimum_growth_bytes=16,DS_SS_bytes=65504,resident_CS_bytes=65452,editor_frame_bytes=4000,Chat_frame_bytes=4000,independent_cells=1920,screen_negative_controls=8),
  limitations=['Geometry matrix invokes exact loaded parent/module entries on real parent DS=SS/stack with fixture-supplied canonical startup. Valid Help queues but is not executed in this component test.',
   'No whole-main continuation test under an external geometry fault; BIOS mode reset may erase live Chat pixels. Clean retirement restores preserved underlay, not erased live Chat pixels.',
   'Ordinary Chat geometry-fault and retirement policy unchanged. Allocation/lifetime faults and other original features remain open.',
   'Connected editor idle during Help; no deliberately scheduled remote payload inside the child. Hayes/nullmodem model holds CTS ready.',
   'No physical Boca/SPA2102/SIP/audio acceptance, deployment or selected-package change.'],
  scope='Source-maintained non-destructive Help admission guard. Frozen old-parent negative and new actual DOS8086 geometry controls, ordinary main-loop recovery/queued input, clean source rebuild, nested ASPECT and current Enigma/Synchronet/reconnect regressions. Not a claim of byte-identical original behavior or full original parity.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS geometry guard and current-product regression receipt')
if __name__=='__main__':main()
