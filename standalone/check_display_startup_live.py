#!/usr/bin/env python3
"""Linked imported-display startup handoff; BIOS/UART/DOS boundaries modeled."""
import argparse,hashlib,json
from pathlib import Path
import check_transport as transport
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((binary.parent/'manifest.json').read_text());assert manifest['experimental_display_startup'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 transport.BINARY=binary;transport.MAP=binary.parent/'terminal.map'
 from check_display_transaction_live import Transaction
 from check_recording_rx_live import ordinary
 cases=[]
 def done(name,count):cases.append(dict(case=name,inputs=count,passed=True));print(name,count,'PASS',flush=True)
 m=Transaction();before=m.all();assert m.invoke(entry='_terminal_display_startup')==0 and m.all()==before;done('absent-import-keeps-baseline-without-selector-or-preference-invention',1)
 count=0
 for rows in (25,28,43,50):
  for selector in range(5):
   for hidden in (0,65535):
    m=Transaction();m.saved(hidden,selector,rows,3);saved=bytes(m.uc.mem_read(m.symbols['_terminal_display_preferences'],8));assert m.invoke(entry='_terminal_display_startup')==0
    physical=rows if selector in (2,4) else 25;m.verify(physical,bool(hidden));assert m.meta()==(selector,1,0,0)
    assert bytes(m.uc.mem_read(m.symbols['_terminal_display_preferences'],8))==saved
    logical=physical if hidden else physical-1
    ordinary(m,b'\x1bc\x1b[18t\x1b[99;80H\x1b[6n');m.drain();assert bytes(m.tx)==b'\x1b'+f'[8;{logical};80t'.encode()+b'\x1b'+f'[{logical};80R'.encode();count+=1
 done('accepted-selectors-heights-hidden-words-canonical-shadow-and-RIS-queries',count)
 count=0
 for mode in (0,0x12):
  for selector in (3,4):
   for hidden in (0,1):
    m=Transaction();m.saved(hidden,selector,50,mode);assert m.invoke(entry='_terminal_display_startup')==0;m.verify(25,hidden)
    assert m.meta()==(1,1,1,3 if mode else 0);count+=1
 done('ineligible-and-graphics-requests-use-verified-baseline-fallback',count)
 count=0
 for ready,selector,result in [(2,1,7),(65535,1,7),(1,5,1),(1,65535,1)]:
  m=Transaction();m.saved(selector=selector);m.put('_terminal_display_preferences_ready',ready);before=m.all();assert m.invoke(entry='_terminal_display_startup')==result and m.all()==before;count+=1
 for owner in ('connection_state','terminal_transfer_pending','terminal_program_active','terminal_screen_pause_active'):
  m=Transaction();m.saved(selector=2);m.put(owner,1);before=m.all();assert m.invoke(entry='_terminal_display_startup')==3 and m.all()==before;count+=1
 done('invalid-capture-or-selector-and-busy-owners-refuse-without-mutation',count)
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 sources=['standalone/check_display_startup_live.py','standalone/check_display_transaction_live.py','standalone/check_row_geometry_live.py']
 r=dict(passed=True,terminal_sha256=sha(binary),manifest_sha256=sha(binary.parent/'manifest.json'),inputs=sum(c['inputs'] for c in cases),cases=cases,sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Delegates to actual composed selector transaction. Main ordering, import/file/IRQ cleanup and actual startup media are separate DOS evidence; no physical/BBS acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main()
