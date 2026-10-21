#!/usr/bin/env python3
"""Reject bad source/CAN and premature cancellation using actual audio bytes."""
import argparse,json
from pathlib import Path
from audio_synchronet import ROOT,sha
from audio_synchronet_cancel_fixed import payload,name_for
from audit_synchronet_cancel_fixed_audio_dos import cancel_protocol
from audit_audio_download import frontend_trace
from modem import Telnet

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and not (out/'cancel-control-checks.json').exists()
 base=json.loads((out/'independent-audit.json').read_text());assert base['passed']
 run=json.loads((out/'result.json').read_text());NAME=run['upload']['name'];assert NAME in {name_for(slot) for slot in range(1,1000)}
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 trace,_=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes']);expected=payload(NAME)
 protocol=cancel_protocol(sent,display,trace,expected);checks={'actual_CRC_ACK_CAN_and_live_menu':True}
 cases=[('ACK_after_CAN','bbs',protocol['first_ACK_offset'],protocol['cancel_seconds']+.001),
  ('CAN_before_ACK','dos',protocol['cancel_offset'],protocol['first_ACK_seconds']-.001),
  ('menu_before_CAN','dos',protocol['cancel_offset']+2,protocol['cancel_seconds']-.001)]
 for name,direction,offset,when in cases:
  changed=[]
  for row in trace:
   a=row['offset'];b=a+row['size']
   if row['direction']!=direction or not a<=offset<b:changed.append(dict(row));continue
   if a<offset:changed.append(dict(row,size=offset-a))
   changed.append(dict(row,offset=offset,size=1,seconds=when))
   if offset+1<b:changed.append(dict(row,offset=offset+1,size=b-offset-1))
  try:cancel_protocol(sent,display,changed,expected)
  except AssertionError:checks[name+'_rejected']=True
  else:checks[name+'_rejected']=False
 for name,offset,value in [('corrupted_first_payload',protocol['frames'][0]['offset']+10,None),('EOT_instead_of_CAN',protocol['cancel_offset'],4)]:
  changed=bytearray(sent);changed[offset]=(changed[offset]^1) if value is None else value
  try:cancel_protocol(bytes(changed),display,trace,expected)
  except AssertionError:checks[name+'_rejected']=True
  else:checks[name+'_rejected']=False
 second=protocol['frames'][1]['offset'];mid=sent[:second+78]+b'\x18\x18 Q'
 try:cancel_protocol(mid,display,trace,expected)
 except AssertionError:checks['original_midframe_pattern_rejected']=True
 else:checks['original_midframe_pattern_rejected']=False
 result=dict(passed=all(checks.values()),checks=checks,inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audit_synchronet_cancel_fixed_audio_dos.py',ROOT/'lab/bbs/audio_synchronet_cancel_fixed.py',ROOT/'lab/bbs/audit_audio_download.py',ROOT/'lab/bbs/test_transfer_dos.py']},
  captures_sha256={n:sha(out/n) for n in ('result.json','independent-audit.json','bbs-input.bin','bbs-output.bin','serial-input-events.jsonl','serial-write-events.jsonl')},scope='Actual cancellation baseline plus five timing/byte counterexamples: ACK after CAN, CAN before ACK, premature menu, corrupted source and EOF replacing CAN must all reject. No mutation of original capture files or product state.')
 (out/'cancel-control-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
