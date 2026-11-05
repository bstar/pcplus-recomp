#!/usr/bin/env python3
"""Bind source terminal Alt-V runtime, serial service, layout, component and rebuild proofs."""
import argparse,json,struct
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','service','layout','linked','source-proof','owner-dos','owner-linked','session-dos','session-linked','original','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--workflow',type=Path,action='append',required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 def bind(path):
  path=path.resolve();return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
 def checked(path):
  r=json.loads(path.read_text());assert r['passed'],path
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n
  if isinstance(r.get('checks'),dict):assert all(r['checks'].values()),path
  return r
 binary=a.terminal.resolve();m=json.loads(binary.with_name('manifest.json').read_text());digest=sha(binary)
 assert m['experimental_file_viewer'] and m['binary_sha256']==digest
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 workflows=[];captures={}
 for path in a.workflow:
  r=checked(path);assert r['binary_sha256']==digest and len(r['cases'])==1
  c=r['cases'][0];name=c['case'];assert c['passed'] and all(c['checks'].values())
  folder=ROOT/'build/connection-dos'/(path.parent.name+'-'+name)
  raw=(folder/'VIEWUI.BIN').read_bytes();words=struct.unpack_from('<9H',raw)
  assert len(raw)==12083 and words[0:2]==(0x5656,15) and raw[18:4018]==raw[8018:12018] and words[3:5]==words[7:9]
  assert sha(folder/'VIEWUI.BIN')==c['capture_sha256'] and raw[12018]==3 and raw[12019:].split(b'\0',1)[0]==b''
  wire=(folder/'serial.bin').read_bytes();assert wire.count(b'ready\r')==1 and b'\x1b[3;13R' in wire
  assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
  captures[name]=folder/'VIEWUI.BIN'
  workflows.append(dict(case=name,checks=c['checks'],report=bind(path),artifacts=[bind(folder/n) for n in ['VIEWUI.BIN','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','serial.bin','VIEWOBS.COM','TEST.PRM','dosbox.conf','result.json']]))
 assert len(workflows)==10 and set(captures)=={'cancel','page','next','home','missing','binary','empty','reference','browser','loading-cancel'}
 service=checked(a.service);layout=checked(a.layout);linked=checked(a.linked);proof=checked(a.source_proof);original=checked(a.original)
 assert service['binary_sha256']==layout['binary_sha256']==linked['binary_sha256']==proof['binary_sha256']==digest
 assert linked['editor_cases']==792 and len(linked['cases'])==10 and all(c['passed'] for c in linked['cases'])
 assert len(layout['negative_controls'])==4 and all(c['rejected'] for c in layout['negative_controls'])
 assert layout['viewer_state_bytes']==754 and layout['persistent_DGROUP_bytes']==0
 assert proof['disabled_sha256']=='74e3f0822044128b68c2f51660efa4e913292cca786edb649c2d662d53e72239'
 folder=ROOT/'build/connection-dos'/(a.service.parent.name+'-serviced');raw=(folder/'VIEWUI.BIN').read_bytes();words=struct.unpack_from('<9H',raw)
 assert sha(folder/'VIEWUI.BIN')==service['capture_sha256'] and words[:2]==(0x5656,15)
 expected=bytearray(raw[18:4018]);message=b'UART-WHILE-VIEW'
 for i,c in enumerate(message):expected[(22*80+i)*2:(22*80+i)*2+2]=bytes([c,7])
 assert raw[8018:12018]==expected and words[7]==(22<<8)|len(message) and words[8]==words[4]
 assert b'\x1b[23;16R' in (folder/'serial.bin').read_bytes()
 service_evidence=[bind(folder/n) for n in ['VIEWUI.BIN','BEFORE.BIN','AFTER.BIN','SCREEN.BIN','serial.bin','VIEWOBS.COM','TEST.PRM','result.json']]
 comparisons=[]
 for maintained,native,index in [('page','exact-page',2),('binary','binary',2),('empty','empty',2),('cancel','long',1),('missing','retry',2)]:
  origin=next(c for c in original['cases'] if c['case']==native)['captures'][index];path=ROOT/origin['path'];assert sha(path)==origin['sha256']
  actual=captures[maintained].read_bytes()[4018:8018];expected=path.read_bytes()
  if maintained in ['cancel','missing']:
   actual=b''.join(actual[(r*80+5)*2:(r*80+76)*2] for r in range(10,15));expected=b''.join(expected[(r*80+5)*2:(r*80+76)*2] for r in range(10,15))
  assert actual==expected
  comparisons.append(dict(case=maintained,matched_bytes=len(actual),original_capture=origin))
 components=[]
 for name,path,want in [('owner-DOS',a.owner_dos,902),('owner-linked',a.owner_linked,25),('session-DOS',a.session_dos,21727),('session-linked',a.session_linked,26)]:
  r=checked(path);assert r.get('checks',r.get('inputs'))==want
  for n,h in r['sources'].items():
   if n in m['sources']:assert h==m['sources'][n],n
  components.append(dict(case=name,report=bind(path),checks_or_inputs=want,binary_sha256=r['binary_sha256']))
 result=dict(passed=True,binary_sha256=digest,source_commit=proof['source_commit'],workflows=workflows,
  service=dict(report=bind(a.service),checks=service['checks'],evidence=service_evidence),
  linked=dict(report=bind(a.linked),editor_cases=792,lifecycle_cases=10),layout=bind(a.layout),source_proof=bind(a.source_proof),
  original_comparisons=comparisons,components=components,original_inputs=[],physical_deployment_changed=False,
  memory=dict(DGROUP_bytes=m['data_stack_bytes'],DGROUP_spare=m['memory_layout']['near_spare_bytes'],resident_bytes=m['memory_layout']['resident_CS_extent_bytes'],resident_spare=m['memory_layout']['resident_CS_spare_bytes'],viewer_state_bytes=754,borrowed_existing_page_bytes=3920),
  sources={'standalone/record_viewer_ui.py':sha(Path(__file__))},
  scope='Opt-in source-only Alt-V terminal integration, ten actualDOS8086 COM3/IRQ5 workflows plus live incoming serial service, passive full-frame/cursor restoration, three exact original4000-byte pages and two original710-byte popup comparisons, linked editor/geometry/fault/layout guards, dynamic viewer/fixed call-log reservation coexistence and exact enabled/disabled public-source rebuild. Not stock BBS editor/sink/transfer pressure, configured external viewer, physical DOS6.22/SHARE/SIP/modem or full feature parity.',
  remaining=['Stock Enigma/Synchronet editor and capture/HOLD/PRN pressure composition for this exact parent.',
   'Carrier-loss/reconnect/transfer/cancel and end-to-end nativeDOS main-loop fault/shutdown composition.',
   'Configured external-viewer PRM binding and remaining original file/editor/key/Chat/ASPECT/emulation/protocol/Host parity.',
   'Physical DOS6.22/Boca/SPA2102/SynthModem acceptance and verified deployment; installed selector unchanged.'])
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS10viewer workflows,live service,5original UI comparisons,ownership/layout/rebuild proofs')
if __name__=='__main__':main()
