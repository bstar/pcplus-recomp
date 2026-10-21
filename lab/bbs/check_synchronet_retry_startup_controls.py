#!/usr/bin/env python3
"""Challenge the same-call retry audit without altering any captured byte."""
import argparse,json
from pathlib import Path
from audio_synchronet import ROOT,sha
from audio_synchronet_retry_startup import NAME,payload
from audit_synchronet_retry_startup_audio_dos import retry_protocol
from audit_audio_download import frontend_trace
from modem import Telnet

def retime(trace,direction,offset,when):
 changed=[];hits=0
 for row in trace:
  a=row['offset'];b=a+row['size']
  if row['direction']!=direction or not a<=offset<b:
   changed.append(dict(row));continue
  hits+=1
  if a<offset:changed.append(dict(row,size=offset-a))
  changed.append(dict(row,offset=offset,size=1,seconds=when))
  if offset+1<b:changed.append(dict(row,offset=offset+1,size=b-offset-1))
 assert hits==1
 return changed

def challenge(sent,display,trace,expected):
 from test_transfer_dos import timestamp
 protocol=retry_protocol(sent,display,trace,expected)
 checks={'complete_same_source_retry_baseline':True}
 def reject(name,s=sent,d=display,t=trace,e=expected):
  try:retry_protocol(s,d,t,e)
  except (AssertionError,ValueError):checks[name]=True
  else:checks[name]=False
 retry=protocol['retry'];cancel=protocol['cancel_offset']
 for name,direction,offset,when in [
  ('first_ACK_after_CAN','bbs',protocol['first_ACK_offset'],protocol['cancel_seconds']+.001),
  ('CAN_before_first_ACK','dos',cancel,protocol['first_ACK_seconds']-.001),
  ('final_EOT_after_menu','dos',retry['end']-1,protocol['post_input_seconds']+.001)]:
  reject(name,t=retime(trace,direction,offset,when))
 for name,offset,value in [
  ('cancel_replaced_by_EOT',cancel,4),
  ('corrupt_first_source',protocol['first_frames'][0]['offset']+10,None),
  ('corrupt_retry_source',retry['frames'][0]['offset']+10,None),
  ('retry_missing_second_EOT',retry['end']-1,0),
  ('unexpected_menu_command',cancel+2,ord('X'))]:
  changed=bytearray(sent);changed[offset]=changed[offset]^1 if value is None else value
  reject(name,s=bytes(changed))
 reject('different_source_fixture',e=bytes([expected[0]^1])+expected[1:])
 reject('no_retry',s=sent[:cancel+2]+b' Q')
 second=protocol['first_frames'][1]['offset']
 reject('original_midframe_cancel',s=sent[:second+78]+b'\x18\x18 Q')
 final_complete=timestamp(trace,'dos',retry['end']-1)
 ack_candidates=[i for i,b in enumerate(display) if b==6 and final_complete<=timestamp(trace,'bbs',i)<protocol['post_input_seconds']]
 assert len(ack_candidates)==1
 reject('final_ACK_after_menu',t=retime(trace,'bbs',ack_candidates[0],protocol['post_input_seconds']+.001))
 return checks

def selfcheck():
 import binascii
 source=payload(NAME);sent=bytearray();display=bytearray();trace=[]
 def add(direction,data,seconds):
  stream=sent if direction=='dos' else display
  trace.append(dict(direction=direction,offset=len(stream),size=len(data),seconds=seconds));stream.extend(data)
 def frame(number,data):
  return bytes([2 if len(data)==1024 else 1,number,255-number])+data+binascii.crc_hqx(data,0).to_bytes(2,'big')
 add('bbs',b'Start XMODEM-1K/CRC transfer now C',.5)
 add('dos',frame(1,source[:1024]),1);add('bbs',b'\x06',2)
 add('dos',frame(2,source[1024:2048]),3);add('bbs',b'\x06',4)
 add('dos',b'\x18\x18',5)
 add('dos',b' USXRUP003.BIN\rySynthetic PCPlus audio retry\r1n',6)
 add('bbs',b'\r\n[Hit a key] Files Start XMODEM-1K/CRC transfer now C',7)
 padded=source+b'\x1a'*127;offset=0
 for n in range(1,15):
  size=1024 if n<=11 else 128
  add('dos',frame(n,padded[offset:offset+size]),8+n*2);add('bbs',b'\x06',9+n*2);offset+=size
 add('dos',b'\x04',38);add('bbs',b'\x15',39)
 add('dos',b'\x04',40);add('bbs',b'\x06',41)
 add('dos',b' Q',42);add('bbs',b'[Hit a key] Files Main',43)
 return challenge(bytes(sent),bytes(display),trace,source)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path,nargs='?');p.add_argument('--selfcheck',type=Path);a=p.parse_args()
 if a.selfcheck:
  assert a.cohort is None
  target=a.selfcheck.resolve();assert target.is_relative_to(ROOT/'build') and not target.exists()
  checks=selfcheck();result=dict(passed=all(checks.values()),checks=checks,checker_sha256=sha(Path(__file__)),scope='Synthetic auditor rejection checks only; no DOS, audio or actual BBS acceptance.')
  with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
  print(json.dumps(result));assert result['passed'];raise SystemExit(0)
 assert a.cohort is not None
 out=a.cohort.resolve()
 assert out.is_relative_to(ROOT/'build') and not (out/'retry-control-checks.json').exists()
 base=json.loads((out/'independent-audit.json').read_text());assert base['passed']
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 trace,_=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes'])
 checks=challenge(sent,display,trace,payload(NAME))
 names=('lab/bbs/check_synchronet_retry_startup_controls.py','lab/bbs/audit_synchronet_retry_startup_audio_dos.py','lab/bbs/audio_synchronet_retry_startup.py','lab/bbs/audit_audio_download.py','lab/bbs/test_transfer_dos.py','lab/bbs/audit_indexed_controls.py')
 captures=('result.json','independent-audit.json','bbs-input.bin','bbs-output.bin','serial-input-events.jsonl','serial-write-events.jsonl')
 result=dict(passed=all(checks.values()),checks=checks,inputs={n:sha(ROOT/n) for n in names},captures_sha256={n:sha(out/n) for n in captures},scope='One actual same-call CRC retry baseline and twelve timing/source/menu/finish counterexamples. Captures and native state remain unchanged; mutated copies must reject.')
 with (out/'retry-control-checks.json').open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result));assert result['passed']
