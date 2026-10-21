#!/usr/bin/env python3
"""Passive closing-tail timing across DOS frontend, audio and BBS relay."""
import argparse,datetime,hashlib,json
from pathlib import Path
from modem import Telnet
from audit_zmodem import header


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path)
 out=p.parse_args().cohort.resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 read=lambda n:json.loads((out/n).read_text())
 audit=read('upload-audit.json');assert audit['checks']['complete_CRC_ZMODEM_and_opposite_controls']
 assert all(sha(out/n)==v for n,v in audit['capture_sha256'].items())
 protocol=audit['protocol'];end=protocol['end'];sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes())
 display,_=Telnet().feed((out/'bbs-output.bin').read_bytes());assert sent[end-2:end]==b'OO'
 rows=[json.loads(v) for v in (out/'server-session.jsonl').read_text().splitlines()]
 exits=[v for v in rows if v.get('msg')=='Process exited'];assert len(exits)==1 and exits[0]['exitCode']==0
 exitms=datetime.datetime.fromisoformat(exits[0]['time'].replace('Z','+00:00')).timestamp()*1000
 serial=[json.loads(v) for v in (out/'serial-input-events.jsonl').read_text().splitlines()]
 prefix=audit['control_timing']['directions']['dos']['raw_prefix_bytes']
 oo=next(v for v in serial if v['offset']<=prefix+end-1<v['offset']+v['length'])
 fin=next(v for v in audit['protocol']['controls'] if v['type']==8 and v['position']==0)
 fin_header=header(display,fin['offset'])
 write=[json.loads(v) for v in (out/'serial-write-events.jsonl').read_text().splitlines()]
 down_prefix=audit['control_timing']['directions']['bbs']['raw_prefix_bytes']
 last=next(v for v in write if v['offset']<=down_prefix+fin_header['end']-1<v['offset']+v['length'])
 anchor=audit['control_timing']['clock_anchor']
 finms=anchor['wallTimeMs']+(last['submittedAt']-anchor['seconds'])*1000
 anchors=read('clock-anchors.json')
 offsets=[int(v['wall_ns'])-(int(v['monotonic_before_ns'])+int(v['monotonic_after_ns']))//2 for v in anchors]
 widths=[int(v['monotonic_after_ns'])-int(v['monotonic_before_ns']) for v in anchors]
 assert max(offsets)-min(offsets)<1000000 and max(widths)<1000000
 # Retain actual relay receive timing, never early DOS output as peer arrival.
 events=[json.loads(v) for v in (out/'BBS-relay-events.jsonl').read_text().splitlines()]
 raw=(out/'bbs-input.bin').read_bytes();decoder=Telnet();decoded=bytearray();cursor=0;relay_oo=[]
 for event in events:
  if event['direction']!='to_bbs':continue
  assert event['offset']==cursor
  body,_=decoder.feed(raw[cursor:cursor+event['count']]);cursor+=event['count']
  start=len(decoded);decoded.extend(body)
  if start<end and end-2<len(decoded):
   relay_oo.append({'canonical_start':start,'canonical_bytes':len(body),
    'wall_ms':(int(event['monotonic_ns'])+offsets[0])/1000000})
 assert cursor==len(raw) and bytes(decoded)==sent and relay_oo
 result={'transfer_audit_passed':audit['passed'],'helper_exit':exits[0]['time'],
  'receiver_ZFIN_last_byte_submitted_to_DOS_wall_ms':finms,
  'receiver_ZFIN_last_byte_after_helper_exit_ms':finms-exitms,
  'sender_OO_frontend_wall_ms':oo['wallTimeMs'],
  'sender_OO_frontend_after_helper_exit_ms':oo['wallTimeMs']-exitms,
  'sender_OO_relay_observations':relay_oo,
  'sender_OO_relay_after_helper_exit_ms':[v['wall_ms']-exitms for v in relay_oo],
  'closing_bytes_hex':sent[end-2:end].hex(),'post_protocol_keyboard_hex':sent[end:].hex(),
  'late_header_controls':audit['late_protocol_controls'],
  'wall_monotonic_anchor_drift_ns':max(offsets)-min(offsets),
  'maximum_anchor_measurement_interval_ns':max(widths),
  'capture_sha256':{n:sha(out/n) for n in ['upload-audit.json','result.json','server-session.jsonl','serial-input-events.jsonl','serial-write-events.jsonl','BBS-relay-events.jsonl','clock-anchors.json','bbs-input.bin','bbs-output.bin']},
  'checker_sha256':sha(Path(__file__)),
  'scope':'Read-only transport and authoritative helper-exit timing. Full opposite ZFIN and literal OO validate, but this does not waive late-tail acceptance or prove how a BBS form consumed those bytes. Frontend submission is not DOS application consumption; relay observation precedes forwarding to the BBS socket. No injected replies, modified captures or new physical test.'}
 target=out/'upload-finish-diagnosis.json'
 assert not target.exists()
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('capture_sha256','sender_OO_relay_observations')},indent=2))


if __name__=='__main__':main()
