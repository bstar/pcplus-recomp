#!/usr/bin/env python3
"""Read-only cancellation causality with deliberately premature/late controls."""
import argparse,hashlib,json
from pathlib import Path
from audit_audio_download import frontend_trace
from audit_zmodem import scan,packet
from modem import Telnet
from test_transfer_dos import timestamp


def verify(t):
 assert t['metadata_crc']<t['ZRPOS_first']<=t['ZRPOS_last']<t['data_header']
 assert t['data_crc']<t['ACK_first']<=t['ACK_last']<t['CAN_first']
 assert t['CAN_first']<=t['CAN_last']<t['search_first']


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 target=out/'cancel-timing-verifier.json';assert not target.exists()
 read=lambda n:json.loads((out/n).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 r=read('result.json');a=read('upload-cancel-audit.json');base=read('independent-audit.json')
 assert r['upload_cancel'] and a['passed'] and base['passed']
 assert all(sha(out/n)==h for n,h in a['capture_sha256'].items())
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 trace,_=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes'])
 detail=a['protocol'];offer=detail['offer'];meta=packet(sent,offer['end'],offer['format']);body=detail['first_data'];ack=detail['ACK']
 assert ack['position']==body['length']==1024
 data=next(h for h in scan(sent,meta['end']) if h['type']==10)
 zrpos=next(h for h in scan(display) if h['type']==9 and h['position']==0 and timestamp(trace,'bbs',h['offset'])>timestamp(trace,'dos',meta['crc_end']-1))
 t={'metadata_crc':timestamp(trace,'dos',meta['crc_end']-1),'ZRPOS_first':timestamp(trace,'bbs',zrpos['offset']),
  'ZRPOS_last':timestamp(trace,'bbs',zrpos['end']-1),'data_header':timestamp(trace,'dos',data['offset']),
  'data_crc':timestamp(trace,'dos',body['crc_end']-1),'ACK_first':timestamp(trace,'bbs',ack['offset']),
  'ACK_last':timestamp(trace,'bbs',ack['end']-1),'CAN_first':timestamp(trace,'dos',detail['cancel_offset']),
  'CAN_last':timestamp(trace,'dos',detail['cancel_offset']+17),'search_first':timestamp(trace,'dos',detail['search_offset'])}
 verify(t)
 mutants=[('premature-ZRPOS',dict(t,ZRPOS_first=t['metadata_crc']-.001,ZRPOS_last=t['metadata_crc']-.001)),
  ('premature-ACK',dict(t,ACK_first=t['data_crc']-.001,ACK_last=t['data_crc']-.001)),
  ('ACK-after-cancellation',dict(t,ACK_first=t['CAN_first']+.001,ACK_last=t['CAN_first']+.001)),
  ('cancellation-before-valid-data',dict(t,CAN_first=t['data_crc']-.001,CAN_last=t['data_crc']-.001))]
 cases=[]
 for name,mutant in mutants:
  try:verify(mutant)
  except AssertionError:cases.append({'case':name,'rejected':True})
  else:raise AssertionError(name)
 names=['upload-cancel-audit.json','result.json','independent-audit.json','bbs-input.bin','bbs-output.bin','serial-input-events.jsonl','serial-write-events.jsonl']
 report={'passed':True,'input_transfer_audit_passed':True,'control_times_seconds':t,'negative_cases':cases,
  'capture_sha256':{n:sha(out/n) for n in names},'checker_sha256':sha(Path(__file__)),
  'scope':'Read-only CRC-valid metadata/ZRPOS/data/ACK/CAN/search ordering on the actual Node frontend timeline. Four copied-time mutants must fail. Captures are unchanged; timestamps are transport observations, not DOS application-consumption times. Does not establish server temporary cleanup, retry or physical acceptance.'}
 with target.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'passed':True,'negative_cases_rejected':len(cases),'control_times_seconds':t}))

if __name__=='__main__':main()
