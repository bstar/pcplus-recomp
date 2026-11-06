#!/usr/bin/env python3
"""Bind connected Enigma editor/Chat/Help return and independent cell evidence."""
import argparse,json,struct
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('package','capture','bridge','controls','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();package=a.package.resolve();capture=a.capture.resolve();bridge=a.bridge.resolve();receipts={};sources={}
 for path in (package,capture,bridge,a.controls.resolve()):assert path.is_relative_to(ROOT/'build')
 bundle=json.loads((package/'package.json').read_text());products=bundle['products']
 for n,h in bundle['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
 for n,h in products.items():assert sha(package/n)==h,n
 def load(path):
  path=path.resolve();assert path.is_relative_to(ROOT)
  r=json.loads(path.read_text());assert r['passed'],path;receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in r.get('sources',{}).items():
   assert sha(ROOT/n)==h,n
   assert n not in sources or sources[n]==h,n
   sources[n]=h
  return r
 producer=load(capture/'proxy-integration.json')
 assert producer['binary_sha256']==products['TERMINAL.EXE'] and all(producer['checks'].values())
 for n,h in producer['product_inputs'].items():assert sha(ROOT/n)==h,n
 chat=load(capture/'chat-help-audit.json');assert chat['proof']['products']==products and all(chat['checks'].values())
 semantic=load(capture/'semantic-audit.json');assert semantic['authority']['stock_server'] and semantic['checks']['stock_editor_entered'] and semantic['checks']['no_post_saved'] and all(semantic['checks'].values())
 cells=load(capture/'screen-reference-audit.json');size=load(capture/'size-probe-screen-audit.json');controls=load(a.controls/'result.json')
 assert all(cells['checks'].values()) and cells['different_cells']==0 and cells['matched_cells']==1920 and cells['actual_CPR']==[9,8]
 assert size['NAWS']==[[80,24]] and (size['physical_rows'],size['logical_rows'])==(25,24)
 expected={'unchanged','character','attribute','bottom-character','bottom-attribute','cursor','prefix-truncated','unsupported-font','proxy-input-truncated'}
 assert len(controls['cases'])==9 and {r['case'] for r in controls['cases']}==expected
 for r in controls['cases']:assert r['passed'] and r['rejected']==(r['case']!='unchanged')
 assert controls['original_capture_sha256']==sha(capture/'screen-reference-audit.json')
 raw=(capture/'BBHELP.BIN').read_bytes();assert len(raw)==20052
 w=struct.unpack_from('<26H',raw);frames=[raw[52+i*4000:52+(i+1)*4000] for i in range(5)]
 assert w[:3]==(0x4845,4,1) and w[5]==25 and w[16:21]==(2,0,0,1,11) and w[21:24]==(2,0,0)
 assert frames[0]==frames[4] and frames[1]==frames[3]
 assert all(b'ON-LINE' in frames[i][3840::2] for i in (0,4))
 assert w[6]==w[10] and w[11]==w[15] and w[7]==w[9] and w[12]==w[14]
 ready=json.loads((bridge/'ready.json').read_text());closed=json.loads((bridge/'1-closed.json').read_text())
 assert ready['terminalSizeProbe'] and ready['terminalRows']==24 and closed['source_unchanged']
 assert len(list(bridge.glob('*-closed.json')))==1
 assert len((capture/'BEFORE.BIN').read_bytes())==42 and (capture/'BEFORE.BIN').read_bytes()==(capture/'AFTER.BIN').read_bytes()
 for n,h in ready['installed_sources'].items():assert sha(ROOT/'build/menu-size-accepted-20261104/candidate'/n)==h,n
 paths=['BBHELP.BIN','SCREEN.BIN','BEFORE.BIN','AFTER.BIN','TEST.PRM','serial-sent.bin','serial-received.bin','server-session.jsonl']
 captures={str((capture/n).relative_to(ROOT)):sha(capture/n) for n in paths}
 for n in ('ready.json','1-closed.json','1-screen-reference.json','1-screen-prefix.bin','1-serial-input.bin','1-serial-output.bin','1-telnet-input.bin','1-telnet-output.bin'):captures[str((bridge/n).relative_to(ROOT))]=sha(bridge/n)
 baseline=ROOT/'docs/validation/chat-help-busy.json';prior=json.loads(baseline.read_text());assert prior['passed'] and prior['products']==products;receipts[str(baseline.relative_to(ROOT))]=sha(baseline)
 sources['standalone/record_chat_help_bbs.py']=sha(Path(__file__))
 report=dict(passed=True,products=products,sources=sources,receipts=receipts,captures=captures,
  summary=dict(BIOS_rows=25,logical_rows=24,modal_frames=5,full_editor_bytes_restored=4000,full_Chat_bytes_restored=4000,final_reference_cells=1920,final_different_cells=0,actual_CPR=[9,8],negative_screen_controls=8,positive_screen_control=1,status_preserved='ON-LINE'),
  limitations=['Stock editor idle during local Help; no BBS payload deliberately scheduled inside the DOS child.',
   'Hayes/nullmodem lab model holds CTS ready; no physical flow timing, Boca/SPA2102/SIP/audio acceptance.',
   'One25-row/24-logical-row source profile and one stock editor workflow; no all-BBS/screens/layout claim.',
   'Geometry/allocation/lifetime faults, other waits/contexts and full original parity remain open.',
   'No physical deployment or selected-package change.'],
  scope='Actual owned Enigma authentication/unsaved editor over actual SynthModem Telnet proxy, normal DOS8086 main Chat/context3 PCHELP/Chat/editor return, discarded local X, resumed native editor input and exact independent final cells/cursor/NAWS. Acceptance additionally checks all25 editor rows including ON-LINE status; lower-level audit separately reports24 logical rows. Prior same-product evidence retained without relabeling reruns.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS connected Enigma Chat Help editor and full-cell receipt')
if __name__=='__main__':main()
