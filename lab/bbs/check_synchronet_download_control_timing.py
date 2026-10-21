#!/usr/bin/env python3
"""Reject premature/late native ACKs using the actual audio frontend timeline."""
import argparse,json
from pathlib import Path
from audio_synchronet import ROOT,sha
from audio_synchronet_download import source
from modem import Telnet
from audit_audio_download import frontend_trace
from test_transfer_dos import audit_protocol,audit_controls,timestamp

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and not (out/'download-control-timing.json').exists()
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 base=json.loads((out/'independent-audit-v2.json').read_text());assert base['passed']
 trace,provenance=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes']);protocol=audit_protocol(display,source().read_bytes())
 end=timestamp(trace,'bbs',protocol['end']-1)
 post=next(r for r in trace if r['direction']=='dos' and r['seconds']>end and b' ' in sent[r['offset']:r['offset']+r['size']])
 controls=audit_controls(protocol,display,sent,trace,'bbs',post['seconds'],ack_timeout=30)
 assert [c['response'] for c in controls]==[6]*14+[21,6]
 assert sent.endswith(b'\x15\x06 Q');final_ack=len(sent)-3;first_ack=sent.index(b'\x06')
 checks={'actual14_block_ACKs_then_EOT_NAK_ACK':True}
 for name,offset,when in [('final_ACK_before_second_EOT',final_ack,end-.001),('final_ACK_after_menu_input',final_ack,post['seconds']+.001),('first_ACK_before_complete_block',first_ack,timestamp(trace,'bbs',protocol['frames'][0]['end']-1)-.001)]:
  changed=[]
  for row in trace:
   a=row['offset'];b=a+row['size']
   if row['direction']!='dos' or not a<=offset<b:changed.append(dict(row));continue
   if a<offset:changed.append(dict(row,size=offset-a))
   changed.append(dict(row,offset=offset,size=1,seconds=when))
   if offset+1<b:changed.append(dict(row,offset=offset+1,size=b-offset-1))
  try:audit_controls(protocol,display,sent,changed,'bbs',post['seconds'],ack_timeout=30)
  except AssertionError:checks[name+'_rejected']=True
  else:checks[name+'_rejected']=False
 result=dict(passed=all(checks.values()),checks=checks,inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audit_audio_download.py',ROOT/'lab/bbs/test_transfer_dos.py']},
  captures_sha256={n:sha(out/n) for n in ('result.json','independent-audit.json','independent-audit-v2.json','bbs-input.bin','bbs-output.bin','serial-input-events.jsonl','serial-write-events.jsonl')},
  scope='Actual full XMODEM control timeline passes14 block ACKs and two-EOT NAK/ACK. Three timing-only counterexamples must reject: early block ACK, early final ACK and final ACK after post-transfer input. Original captures and original failed literal-count audit are unchanged.')
 (out/'download-control-timing.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
