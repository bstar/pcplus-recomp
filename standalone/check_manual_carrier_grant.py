#!/usr/bin/env python3
"""Differential typed-command output grants during real modeled DCD debounce.
Actual controller/foreground/typed-owner/echo instructions; hardware modeled.
"""
import argparse,hashlib,json
from pathlib import Path
from check_call_timer_live import configure,ROOT
from check_auto_answer_live import Answer
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False);cases=[];images={}
 for label,path in [('baseline',a.baseline.resolve()),('candidate',a.terminal.resolve())]:
  manifest=json.loads((path.parent/'manifest.json').read_text());assert sha(path)==manifest['binary_sha256']
  if label=='baseline':assert sha(path)==json.loads((ROOT/'docs/validation/large-screen-pause.json').read_text())['images']['ordinary']['sha256']
  else:
   for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
  images[label]=dict(path=str(path.relative_to(ROOT)),sha256=sha(path));configure(path)
  for key,command in [(0x2400,b'ATZ\r'),(0x1500,b'ATS0=1\r')]:
   for duration in range(4):
    for echo in (0,1):
     m=Answer(online=True,duplex=echo);m.key(key);m.poll();assert bytes(m.tx)==b'A';m.carrier=False;start=m.tick+1
     body=bytes(m.uc.mem_read(0xb8000,3840))
     for delta in range(duration+1):m.tick=start+delta;m.call('terminal_poll_io')
     wire=bytes(m.tx);assert m.state()==6 and (m.active() or label=='baseline')
     if label=='candidate':assert wire==b'A' and bytes(m.uc.mem_read(0xb8000,3840))==body
     else:assert wire.startswith(b'AT')
     m.carrier=True;m.finish();assert bytes(m.tx)==command and not m.active() and not m.notice()
     cases.append(dict(image=label,key=key,low_ticks=duration,echo=echo,wire_during_low=wire.hex(),clean_completion_after_return=True,passed=True))
   m=Answer(online=True);m.key(key);m.poll();m.carrier=False;m.poll(8)
   status=2 if label=='baseline' and key==0x2400 else 7
   assert m.state()==0 and not m.active() and not m.notice() and m.get('terminal_manual_init_status')==status
   if label=='candidate':assert bytes(m.tx)==b'A'
   else:assert bytes(m.tx).startswith(b'AT')
   cases.append(dict(image=label,key=key,sustained_loss=True,wire=bytes(m.tx).hex(),typed_cleanup_status=status,passed=True))
   m=Answer();m.carrier=False;m.key(key);m.finish();assert bytes(m.tx)==command and m.state()==0
   cases.append(dict(image=label,key=key,offline_untracked_policy_retained=True,passed=True))
 for n,h in json.loads((a.terminal.parent/'manifest.json').read_text())['sources'].items():assert sha(ROOT/n)==h,n
 sources=['standalone/check_manual_carrier_grant.py','standalone/check_auto_answer_live.py','standalone/check_call_timer_live.py','standalone/check_transport.py']
 report=dict(passed=True,inputs=len(cases),cases=cases,images=images,sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Baseline intentionally shows output into the DCD-low interval; candidate withholds data/echo and preserves resumed command or qualified-loss cleanup. Not actual DOS/physical timing.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS typed carrier grant',len(cases),'baseline/candidate inputs')
if __name__=='__main__':main()
