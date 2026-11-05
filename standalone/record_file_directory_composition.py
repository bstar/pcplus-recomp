#!/usr/bin/env python3
"""Bind stock-editor File Directory returns and capture/HOLD/PRN pressure evidence."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from product_inputs import select_product,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','runner','runtime','controls','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--sinks',type=Path,required=True,action='append')
 p.add_argument('--enigma-label',required=True);p.add_argument('--synchronet-label',required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 binary,_=select_product(a.terminal,'TERMINAL.EXE');runner,_=select_product(a.runner,'ASPECT.EXE');digest=sha(binary)
 def bind(path):
  path=Path(path).resolve();assert path.is_relative_to(ROOT/'build');return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
 def checked(path):
  r=json.loads(Path(path).read_text());assert r['passed'],path
  for n,h in r.get('sources',{}).items():assert sha(ROOT/n)==h,n
  if isinstance(r.get('checks'),dict):assert all(r['checks'].values())
  return r
 peers=[]
 for peer,label in [('enigma',a.enigma_label),('synchronet',a.synchronet_label)]:
  folder=ROOT/'build/bbs-lab/results'/peer/label;bridge=ROOT/'build/bbs-lab'/(label+'-proxy')
  r=checked(folder/'proxy-integration.json');base=checked(folder/'result.json');listing=checked(folder/'file-directory-audit.json');cells=checked(folder/'screen-reference-audit.json')
  assert r['binary_sha256']==base['binary_sha256']==cells['binary_sha256']==digest and r['file_directory']==listing
  assert cells['matched_cells']==1920 and cells['different_cells']==0 and cells['fixture_CPR_consumed'] and cells['actual_CPR']==cells['reference_cursor']
  for n,h in r['product_inputs'].items():assert sha(ROOT/n)==h,n
  for n,h in cells['captures'].items():assert sha(Path(n))==h,n
  raw=(folder/'FDVIEW.BIN').read_bytes();assert len(raw)==8344 and struct.unpack_from('<4H',raw)==(0x464f,1,1,1)
  assert raw[24:4024]==raw[4024:8024] and sha(folder/'FDVIEW.BIN')==listing['capture_sha256']
  assert base['cpu']=='8086' and base['serial']['com']==3 and base['serial']['irq']==5
  ready=json.loads((bridge/'ready.json').read_text());closed=json.loads((bridge/'1-closed.json').read_text())
  assert ready['screenReference'] and ready['terminalSizeProbe'] and ready['terminalRows']==24 and closed['source_unchanged']
  assert ready['inputSequenceTimeoutMs']==250 and ready['inputByteDelayMs']==20
  for n,h in ready['installed_sources'].items():assert sha(a.runtime/n)==h,n
  if peer=='synchronet':assert r['interpreter_sha256']==sha(runner) and r['checks']['message_bodies_unchanged'] and r['checks']['no_message_mail_or_transfer_writes']
  else:assert checked(folder/'semantic-audit.json')['checks']['no_post_saved']
  names=['result.json','proxy-integration.json','file-directory-audit.json','screen-reference-audit.json','FDVIEW.BIN','serial-received.bin','OBSERVE.COM','TEST.PRM']
  peers.append(dict(peer=peer,passed=True,checks=listing['checks'],matched_cells=1920,observer_words=listing['observer_words'],scope=listing['scope'],evidence=[bind(folder/n) for n in names]+[bind(bridge/n) for n in ['ready.json','1-closed.json']]))
 flags={'capture':(1,0,0),'hold':(1,1,0),'capture-printer':(1,0,1),'hold-printer':(1,1,1),'printer':(0,0,1)}
 first=b'FIRST'+b'B'*600+b'\r\n';burst=b'A'*3200+b'\r\n';last=b'LAST\r\n';cases=[];reports=[]
 for report in a.sinks:
  suite=checked(report);assert suite['binary_sha256']==digest;reports.append(bind(report))
  for c in suite['cases']:
   assert c['passed'] and all(c['checks'].values()) and c['binary_sha256']==digest
   folder=report.parent/c['case'];capture,hold,printer=flags[c['case']]
   if capture:assert (folder/'CAP.LOG').read_bytes()==first+(b'' if hold else burst)+last
   else:assert not (folder/'CAP.LOG').exists()
   if printer:assert (folder/'PRINTER.RAW').read_bytes()==first+(b'PAUSED\r\n' if hold else b'')+burst+last
   assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes() and (folder/'AFTERCD.TXT').read_bytes().strip()==b'D:\\'
   raw=(folder/'FILEVIEW.BIN').read_bytes();assert len(raw)==4071 and struct.unpack_from('<2H',raw)==(0x4644,3) and raw[6:10]==b'A\x07A\x07'
   trace=(folder/'TRACE.BIN').read_bytes();assert len(trace)==8218 and trace[:6]==b'GS21\x0f\0'
   head=struct.unpack_from('<10H',trace,6);assert head[:2]==(0xc51b,1) and head[3]==0
   records=[struct.unpack_from('<4H',trace,26+i*8) for i in range(head[2])]
   start=c['observations']['findfirst_record'];end=c['observations']['findnext_record'];ds=c['observations']['parent_DS']
   assert records[start][0]>>8==0x4e and records[start][2:]==(0x10,ds) and records[end][0]>>8==0x4f and records[end][3]==ds
   assert not any(start<i<end and r[0]>>8==0x3e and r[3]==ds for i,r in enumerate(records))
   names=['result.json','FILEVIEW.BIN','TRACE.BIN','wire.bin','peer-text.bin','BEFORE.BIN','AFTER.BIN','AFTERCD.TXT','TEST.PRM','dosbox.conf','WATCH.COM','TRACE.COM','TDUMP.COM']
   if capture:names.append('CAP.LOG')
   if printer:names.append('PRINTER.RAW')
   cases.append(dict(case=c['case'],passed=True,checks=c['checks'],capture_bytes=c['capture_bytes'],printer_bytes=c['printer_bytes'],observations=c['observations'],scope=c['scope'],evidence=[bind(folder/n) for n in names]))
 assert len(cases)==5 and {c['case'] for c in cases}==set(flags)
 controls=checked(a.controls);assert len(controls['cases'])==11 and sum(c['rejected'] for c in controls['cases'])==10
 for n,h in controls['inputs'].items():assert sha(ROOT/controls['capture']/n)==h,n
 r=dict(passed=True,binary_sha256=digest,terminal=bind(binary),runner=bind(runner),BBS=peers,sink_reports=reports,sinks=cases,sink_checks=sum(len(c['checks']) for c in cases),controls=bind(a.controls),original_inputs=[],physical_deployment_changed=False,recorder_sha256=sha(Path(__file__)),
  scope='Unchanged normal File Directory terminal: actual Alt-F/file-spec/Escape inside stock Enigma and Synchronet editors with exact full-frame/cursor/shape return, continued editing and3840-cell audits; five actual8086 capture/HOLD/virtualPRN pressure combinations with3202-byte RX, fresh DSR, passive visible-page/traffic capture and DOS entry trace. No SIP/DSP/analog, physical printer/modem, DOS6.22 or whole-application-parity claim.',
  remaining=['File Directory carrier-loss/reconnect/transfer and kernel/media fault composition.','Microsoft DOS6.22 and physical Boca/SPA2102/SynthModem acceptance; selected physical release unchanged.','Internal/configured viewers, editor integration and remaining directory/key/Chat/ASPECT/emulation/protocol/Host parity.'])
 out.mkdir(parents=True);(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS two real listing/editor returns,3840cells,five sink combinations and ten copied negative controls')
if __name__=='__main__':main()
