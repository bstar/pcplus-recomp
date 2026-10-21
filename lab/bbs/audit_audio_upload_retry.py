#!/usr/bin/env python3
"""Re-audit retry captures, distinguishing repeated ZFILE offers from helper calls."""
import argparse,datetime,hashlib,json
from pathlib import Path
import audio_upload,enigma
from modem import Telnet
from audit_zmodem import scan,packet,metadata,audit_batch,audit_controls
from audit_audio_download import frontend_trace
from test_transfer_dos import timestamp


from audio_upload_retry import check


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 read=lambda n:json.loads((out/n).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 r=read('result.json');assert r['route']=='upload' and r['upload_cancel_retry'] and r['upload_cancel']
 from enigma_receive_finish_instance import from_result
 context=from_result(r);assert context
 base=read('independent-audit.json');io=read('serial-io-audit.json')
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 source=out/'SEND/AUDIOUP.BIN';expected=source.read_bytes()
 rows=[json.loads(s) for s in (out/'server-session.jsonl').read_text().splitlines()]
 checks,details=check(out,rows,r['upload']['prepared'])
 checks.update(producer=r['passed'],whole_stream_and_cleanup=base['passed'],serial_ownership=io['evidence_consistent'])
 errors=[];protocol=None;cancel_detail=None;timing=None
 try:
  trace,timing=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes'])
  cancel=sent.index(b'\x18'*8+b'\x08'*10);assert sent.count(b'\x18'*8+b'\x08'*10)==1
  offers=[h for h in scan(sent) if h['type']==4]
  assert len(offers)>=2 and len([h for h in offers if h['offset']<cancel])==1
  assert offers[0]['offset']<cancel<offers[1]['offset']
  meta=packet(sent,offers[0]['end'],offers[0]['format']);assert metadata(meta['payload'])==('AUDIOUP.BIN',11521)
  data=next(h for h in scan(sent,meta['end']) if h['type']==10);body=packet(sent,data['end'],data['format'])
  assert body['payload']==expected[:1024] and body['length']==1024 and body['end']<cancel
  when=timestamp(trace,'dos',cancel)
  ack=next(h for h in scan(display) if h['type']==3 and h['position']==1024 and timestamp(trace,'dos',body['crc_end']-1)<timestamp(trace,'bbs',h['offset']) and timestamp(trace,'bbs',h['end']-1)<when)
  assert not any(h['type'] in (8,11) and h['offset']<cancel for h in scan(sent))
  protocol=audit_batch(sent,{'AUDIOUP.BIN':expected},cancel+18)
  assert protocol['start']==offers[1]['offset']
  search=sent.index(b'S\r',protocol['end']);assert b'AUDIOUP.BIN\r\r' in sent[search:]
  protocol['controls']=audit_controls(protocol,display,trace,'dos',timestamp(trace,'dos',search))
  assert not list(scan(sent,protocol['end']))
  # The final required OO must be handed to the frontend before the second
  # actual helper retires. Keep the same closing gate as the successful run.
  exits=[v for v in rows if v.get('msg')=='Process exited'];assert len(exits)==2
  exit_ms=datetime.datetime.fromisoformat(exits[1]['time'].replace('Z','+00:00')).timestamp()*1000
  prefix=timing['directions']['dos']['raw_prefix_bytes']
  inputs=[json.loads(s) for s in (out/'serial-input-events.jsonl').read_text().splitlines()]
  tail=next(v for v in inputs if v['offset']<=prefix+protocol['end']-1<v['offset']+v['length'])
  assert tail['wallTimeMs']<=exit_ms
  checks.update(valid_source_and_ACK_before_cancel=True,complete_retry_CRC_controls_FIN_OO=True,no_protocol_tail_after_helper_exit=True,real_postretry_search=True)
  cancel_detail={'cancel_offset':cancel,'first_data':{k:v for k,v in body.items() if k!='payload'},'ACK':ack,'retry_offer':offers[1],'retry_offer_count':len(offers)-1,'search_offset':search}
 except Exception as error:
  errors.append(repr(error));checks.update(valid_source_and_ACK_before_cancel=False,complete_retry_CRC_controls_FIN_OO=False,no_protocol_tail_after_helper_exit=False,real_postretry_search=False)
 checks['captures_unchanged']=all(sha(out/n)==h for n,h in r['captures_sha256'].items())
 if protocol:
  for f in protocol['files']:f.pop('source',None)
 names=['result.json','independent-audit.json','serial-io-audit.json','bbs-input.bin','bbs-output.bin','server-session.jsonl','serial-in.bin','serial-input-events.jsonl','serial-write-events.jsonl']
 result={'passed':all(checks.values()),'checks':checks,'errors':errors,'first_cancellation':cancel_detail,'retry_protocol':protocol,'control_timing':timing,
  'server_fixture':context,'official_upload':details,'capture_sha256':{n:sha(out/n) for n in names},'auditor_sha256':sha(Path(__file__)),
  'original_auditor_sha256':sha(Path(__file__).with_name('audio_upload_retry.py')),
  'reaudit_reason':'The original frozen auditor mistook two ZFILE announcements in one retry for extra helpers. The existing independent batch parser validates every repeated offer and all file/control/finish bytes; two actual helpers remain mandatory. Original auditor/report/captures unchanged.',
  'scope':'Actual DOS cancel-after-valid-data/ACK and complete same-source retry in one terminal/modem/BBS connection. Exact CRC/storage/source/control/return/cleanup gates retained; receiver candidate explicitly identified. No receiver temporary cleanup, loss/pressure, other-peer, physical or whole-application acceptance.'}
 (out/'upload-retry-audit-v2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']

if __name__=='__main__':main()
