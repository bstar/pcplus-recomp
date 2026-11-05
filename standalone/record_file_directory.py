#!/usr/bin/env python3
"""Bind the optional File Directory application's current software acceptance."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from product_inputs import select_product,sha
from terminal_memory import inspect_terminal_memory

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','search','linked','dos','source-proof','gateway','path','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--enigma-label',required=True);p.add_argument('--synchronet-label',required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary,_=select_product(a.terminal,'TERMINAL.EXE');digest=sha(binary)
 def bind(path):
  path=Path(path).resolve();assert path.is_relative_to(ROOT/'build');return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
 def checked(path,terminal=True):
  r=json.loads(Path(path).read_text());assert r['passed']
  if terminal:assert r['binary_sha256']==digest
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n
  if isinstance(r.get('checks'),dict):assert all(r['checks'].values())
  return r
 search=checked(a.search);assert len(search['cases'])==19 and all(c['passed'] for c in search['cases'])
 linked=checked(a.linked);assert linked['formatter_cases']==900 and linked['editor_cases']==1170
 source=checked(a.source_proof);assert source['original_inputs']==[] and source['ancestor_git_unavailable']
 assert source['source_count']==len(source['sources']) and source['disabled_sha256']=='ae6cbad95094fd59f98fd95a7831cbdc014b404ec37886a290294fe05089d90b'
 dos=checked(a.dos);expected={'cancel','empty','page','next','missing','reference','browser','serviced','loading-cancel'}
 assert {c['case'] for c in dos['cases']}==expected
 dos_cases=[]
 for c in dos['cases']:
  assert c['passed'] and all(c['checks'].values())
  folder=ROOT/'build/connection-dos'/(a.dos.parent.name+'-'+c['case'])
  raw=(folder/'FILEVIEW.BIN').read_bytes();assert len(raw)==4071 and struct.unpack_from('<2H',raw)==(0x4644,3)
  assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
  files=['FILEVIEW.BIN','SCREEN.BIN','BEFORE.BIN','AFTER.BIN','serial.bin','TEST.PRM','dosbox.conf','FILEOBS.COM']
  dos_cases.append(dict(case=c['case'],checks=c['checks'],evidence=[bind(folder/n) for n in files]))
 regressions=[]
 for n,path,count in [('gateway',a.gateway,3),('path',a.path,1)]:
  r=checked(path);assert len(r['cases'])==count and all(c['passed'] for c in r['cases'])
  regressions.append(dict(name=n,report=bind(path),scope=r['scope']))
 peers=[]
 for peer,label in [('enigma',a.enigma_label),('synchronet',a.synchronet_label)]:
  folder=ROOT/'build/bbs-lab/results'/peer/label
  producer=checked(folder/'proxy-integration.json');base=checked(folder/'result.json');gateway=checked(folder/'gateway-audit.json',False);cells=checked(folder/'screen-reference-audit.json')
  assert producer['gateway']==gateway and cells['matched_cells']==1920 and cells['different_cells']==0
  assert cells['fixture_CPR_consumed'] and cells['actual_CPR']==cells['reference_cursor']
  for n,h in producer['product_inputs'].items():assert sha(ROOT/n)==h,n
  for n,h in cells['captures'].items():assert sha(Path(n))==h,n
  assert base['serial']['com']==3 and base['serial']['irq']==5 and base['cpu']=='8086'
  files=['result.json','proxy-integration.json','gateway-audit.json','screen-reference-audit.json','GWVIEW.BIN','GWCHILD.BIN','serial-received.bin']
  peers.append(dict(peer=peer,passed=True,matched_cells=1920,evidence=[bind(folder/n) for n in files],scope=gateway['scope']))
 memory=inspect_terminal_memory(binary,binary.with_name('terminal.map'));assert memory['near_bytes']==65488 and memory['file_directory_state_bytes']==1724
 result=dict(passed=True,binary_sha256=digest,terminal=bind(binary),manifest=bind(binary.with_name('manifest.json')),product_source_commit=source['source_commit'],source_files=len(json.loads(binary.with_name('manifest.json').read_text())['sources']),
  source_proof=bind(a.source_proof),linked_search=bind(a.search),linked_format_editor=bind(a.linked),DOS_report=bind(a.dos),DOS_cases=dos_cases,regressions=regressions,BBS=peers,
  memory={k:memory[k] for k in ['near_bytes','near_spare_bytes','resident_code_bytes','resident_code_spare_bytes','file_directory_state_bytes','file_directory_DGROUP_bytes','retained_parent_paragraphs']},original_inputs=[],physical_deployment_changed=False,
  recorder_sha256=sha(Path(__file__)),scope='Optional normal File Directory frontend: linked actual code with modeled DOS/readiness and near-memory canary; nine actual DOS listing/return workflows; existing AltF7/Gateway regressions; two stock-editor Gateway return and1920-cell audits. BBS regressions do not open File Directory. Fresh original-free public-source enabled/disabled rebuild. No physical/audio/DOS6.22 or full original-feature-parity claim.',
  remaining=['Listing during stock editor sessions and capture/HOLD/PRN, pressure/loss/reconnect/transfer composition.','Physical Boca/SPA2102/SynthModem and Microsoft DOS6.22 acceptance; selected physical release unchanged.','Internal/configured viewers, external editor integration and remaining directory/key/Chat/ASPECT/emulation/protocol/Host parity.'])
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS listing:19search,900format,1170edit,9DOS,4older-command workflows and3840stock-editor cells; exact public rebuild')
if __name__=='__main__':main()
