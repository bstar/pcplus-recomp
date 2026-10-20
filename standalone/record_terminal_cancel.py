#!/usr/bin/env python3
"""Audit actual modal cancellation, unchanged controls and source provenance."""
import argparse,json,re,struct
from pathlib import Path
from build_aspect_process import ROOT,sha

def read(path):return json.loads(path.read_text())
def current(folder,sources):
 for n,h in sources.items():assert sha(ROOT/n)==sha(folder/'sources'/n)==h,n
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['keyboard','mouse','script-keyboard','script-mouse','trap-keyboard','trap-mouse','normal-keyboard','normal-mouse','retry-keyboard','retry-mouse','prompt','source','baseline']:
  p.add_argument('--'+name,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 for k,v in vars(a).items():
  if k!='output':assert re.fullmatch(r'[A-Za-z0-9_-]+',v)
 expected={'browser','editor','capture','download','receive','receive-partial','upload','send','program','reload','serial','profile','translation','port'}
 routes=[];raw_evidence={};products={}
 for mouse,label,wanted in [(False,a.keyboard,expected),(True,a.mouse,expected),
   (False,a.script_keyboard,{'script-return'}),(True,a.script_mouse,{'script-return'})]:
  folder=ROOT/'build/terminal-cancel-tests'/label;report=read(folder/'result.json')
  binary=ROOT/'build'/('terminal-traps-mouse' if mouse else 'terminal-traps')/'TERMINAL.EXE'
  assert report['passed'] and report['binary_sha256']==sha(binary)
  assert {c['case'] for c in report['cases']}==wanted
  current(folder,report['sources']);products[str(binary.relative_to(ROOT))]=sha(binary)
  if wanted=={'script-return'}:
   assert report['script_wait_adapter_sha256']==sha(ROOT/'standalone/test_terminal_cancel_script_wait.py')
   assert sha(folder/'sources/standalone/test_terminal_cancel_script_wait.py')==report['script_wait_adapter_sha256']
  for case in report['cases']:
   run=folder/case['case'];assert case==read(run/'result.json') and case['passed'] and all(case['checks'].values())
   assert case['mouse']==mouse
   assert sha(run/'TERMINAL.EXE')==sha(binary) and sha(run/'CANCEL.EXE')==report['parent_sha256']
   r=struct.unpack('<16H',(run/'CANCEL.BIN').read_bytes());assert list(r)==case['witness']
   assert r[0:2]==(0xca16,16) and r[2]!=0 and r[3:5]==(1,0) and r[5]<18
   assert r[6:9]==(1,0,1) and r[12]==1 and r[13]==r[14]
   view=(run/'CANCEL.VID').read_bytes();marker=case['marker'].rstrip('+').encode()
   assert len(view)==2000 and marker in view
   if case['case']=='script-return':
    assert r[10]==1 and b'Program could not run. Press a key to return.' in view
    assert not (run/'ASPECT.EXE').exists()
   screen=(run/'SCREEN.BIN').read_bytes();assert len(screen)==4000 and marker not in screen[::2]
   assert (run/'BEFORE.BIN').read_bytes()==(run/'AFTER.BIN').read_bytes()
   if case['case']=='receive-partial':
    assert r[11]==r[15]==1 and b'\x06' in (run/'serial.bin').read_bytes()
    assert not (run/'RECV.BIN').exists() and not (run/'PCRX.$$$').exists()
   routes.append(dict(mouse=mouse,case=case['case'],ticks_to_exit=r[5],hardware_active=r[9],
    program_active=r[10],transfer_active=r[11],accepted_blocks=r[15],checks=len(case['checks'])))
   raw_evidence[str(run.relative_to(ROOT))]={n:sha(run/n) for n in ['CANCEL.BIN','CANCEL.VID','SCREEN.BIN','BEFORE.BIN','AFTER.BIN','result.json','serial.bin']}
 baseline_folder=ROOT/'build/terminal-cancel-tests'/a.baseline;baseline=read(baseline_folder/'result.json')
 assert not baseline['passed'] and {c['case'] for c in baseline['cases']}=={'browser','capture','download'}
 for n,h in baseline['sources'].items():assert sha(baseline_folder/'sources'/n)==h,n
 negatives=[]
 for case in baseline['cases']:
  run=baseline_folder/case['case'];r=struct.unpack('<16H',(run/'CANCEL.BIN').read_bytes())
  assert r[0]==0xca16 and r[3]==1 and r[4]>=1 and r[5]>=36 and r[6:9]==(1,0,1)
  assert case['binary_sha256']!=products['build/terminal-traps/TERMINAL.EXE']
  negatives.append(dict(case=case['case'],rescue_keys=r[4],ticks_to_exit=r[5],
   witness_sha256=sha(run/'CANCEL.BIN'),binary_sha256=case['binary_sha256']))
 regressions=[]
 for mouse,label in [(False,a.trap_keyboard),(True,a.trap_mouse)]:
  folder=ROOT/'build/terminal-trap-tests'/label;report=read(folder/'result.json')
  assert report['passed'] and len(report['cases'])==10;current(folder,report['sources'])
  assert {(c['mode'],c['initial_break']) for c in report['cases']}=={(m,b) for m in range(5) for b in [0,1]}
  for case in report['cases']:
   run=folder/case['case'];mode=case['mode'];initial=case['initial_break']
   assert case['passed'] and all(case['checks'].values())
   assert sha(run/'TERMINAL.EXE')==case['child_sha256']
   probe=ROOT/'build'/(('terminal-traps-mouse' if mouse else 'terminal-traps')+'-probe-'+str(mode))/'TERMINAL.EXE'
   assert sha(probe)==case['child_sha256']
   r=struct.unpack('<31H',(run/'TRAPWIT.BIN').read_bytes())
   child=struct.unpack('<11H',(run/'CHILTRAP.BIN').read_bytes())
   assert r[0:2]==(0x5452,mode) and r[3]==(4 if mode==4 else 0) and r[5]==0
   assert r[4]==(2 if mode==3 else 1 if mode in [1,2] else 0)
   assert r[6]==initial and r[7]==(0 if mode==4 else initial) and r[30]==1
   assert child[:4]==(0x4354,r[2],2,0) and child[4:10]==r[12:18] and child[10]==initial
   if mode!=4:assert r[12:18]==r[18:24]
   else:assert r[18:20]==r[24:26] and r[29]>0
   if mode==2:assert r[11]&255==3
   if mode==3:assert (r[8],r[9],r[11])==(0x0801,12,0x0803)
  regressions.append(dict(kind='trap',receipt=str((folder/'result.json').relative_to(ROOT)),sha256=sha(folder/'result.json'),cases=10))
 for mouse,label in [(False,a.normal_keyboard),(True,a.normal_mouse)]:
  folder=ROOT/'build'/('aspect-parent-break'+('-mouse' if mouse else '')+'-guarded-banked-traps')/label
  report=read(folder/'result.json');assert report['passed'] and len(report['cases'])==13
  assert {c['case'] for c in report['cases']}=={'G','T','W','R','F'}|{f'full-{port}-{flow}' for port in [1,2] for flow in 'NSHB'}
  assert report['parent_sha256']==products['build/'+('terminal-traps-mouse' if mouse else 'terminal-traps')+'/TERMINAL.EXE']
  current(folder,report['source_hashes'])
  assert all(c['passed'] and all(c['checks'].values()) for c in report['cases'])
  regressions.append(dict(kind='ASPECT',receipt=str((folder/'result.json').relative_to(ROOT)),sha256=sha(folder/'result.json'),cases=13,
   checks=sum(len(c['checks']) for c in report['cases'])))
 for mouse,label,expected_case in [(False,a.retry_keyboard,'Q-1-H'),(True,a.retry_mouse,'Q-2-B')]:
  folder=ROOT/'build'/('aspect-parent-exit'+('-mouse' if mouse else '')+'-retry-guarded-banked-traps')/label
  report=read(folder/'result.json');assert report['passed'] and len(report['cases'])==1
  current(folder,report['source_hashes']);case=report['cases'][0]
  assert case['case']==expected_case and case['passed'] and all(case['checks'].values())
  assert report['parent_sha256']==products['build/'+('terminal-traps-mouse' if mouse else 'terminal-traps')+'/TERMINAL.EXE']
  raw=(folder/expected_case/'RENDER.BIN').read_bytes();assert raw.count(b'TRAPOBS1')==1
  snapshot=struct.unpack_from('<16H',raw,raw.index(b'TRAPOBS1')+8)
  assert snapshot[0]==2 and snapshot[15]==1 and snapshot[1:7]==snapshot[8:14]
  retry=case['retry_probe'];assert (retry['callback_before'],retry['callback_after'])==(1,2)
  assert (retry['vector_before_off'],retry['vector_before_seg'])==snapshot[1:3]
  assert (retry['vector_after_off'],retry['vector_after_seg'])==snapshot[1:3]
  regressions.append(dict(kind='retained-retry',receipt=str((folder/'result.json').relative_to(ROOT)),
   sha256=sha(folder/'result.json'),cases=1,checks=len(case['checks'])))
 folder=ROOT/'build/terminal-cancel-controls'/a.prompt;prompt=read(folder/'result.json')
 assert prompt['passed'] and prompt['binary_sha256']==products['build/terminal-traps/TERMINAL.EXE']
 current(folder,prompt['sources']);assert {c['kind'] for c in prompt['cases']}=={'accept','decline','early-answer'}
 regressions.append(dict(kind='prompt',receipt=str((folder/'result.json').relative_to(ROOT)),sha256=sha(folder/'result.json'),cases=3))
 folder=ROOT/'build/terminal-traps-source'/a.source;proof=read(folder/'result.json')
 assert proof['passed'] and len(proof['products'])==18 and not proof['original_inputs']
 for n,h in proof['sources'].items():assert sha(ROOT/n)==h,n
 assert all(pair['expected']==pair['actual'] for pair in proof['products'].values())
 model_path=ROOT/'build/terminal-traps-mouse/trap-model.json';model=read(model_path)
 assert model['passed'] and model['dialog_keys']==[0,0x011b,0x4b00,0x1c0d]
 assert model['binary_sha256']==products['build/terminal-traps-mouse/TERMINAL.EXE']
 assert model['checker_sha256']==sha(ROOT/'standalone/check_terminal_traps.py')
 floors={name:read(ROOT/Path(name).parent/'manifest.json')['memory_layout']['retained_parent_paragraphs'] for name in products}
 assert floors=={'build/terminal-traps/TERMINAL.EXE':21635,'build/terminal-traps-mouse/TERMINAL.EXE':21823}
 directory=read(ROOT/'build/terminal-cancel-tests/directory-controls.json')
 assert directory['passed'] and len(directory['binaries'])==2
 for n,h in directory['binaries'].items():assert sha(ROOT/n)==h,n
 receipt=dict(passed=True,routes=routes,checks=sum(c['checks'] for c in routes),baseline=negatives,
  labels={k:v for k,v in vars(a).items() if k!='output'},
  regressions=regressions,products=products,evidence=raw_evidence,retained_parent_paragraphs=floors,
  unchanged_directory_controls=directory['binaries'],
  directory_builder_sources={n:sha(ROOT/n) for n in ['standalone/build_directory_editor.py','standalone/build_directory_browser.py','src/terminal/trap_wait.inc']},
  source_products=proof['products'],source_receipt_sha256=sha(folder/'result.json'),
  linked_model_sha256=sha(model_path),auditor_sha256=sha(Path(__file__)),
  scope='Actual modal/transfer cancellation from synthetic timer INT1B, quiet CTS-ready nullmodem, ordinary DOS exit16, restoration and partial-stage removal; modeled key API boundaries. No physical device/BREAK, other kernel, continuous hostile stream, blocked CTS or all nonlocal-error claim.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(receipt,indent=2)+'\n')
 print('Independent cancellation audit PASS:',len(routes),'routes',receipt['checks'],'checks')
if __name__=='__main__':main()
