#!/usr/bin/env python3
"""Actual audio upload cancellation: preserve source and require live BBS input."""
import argparse,hashlib,json
from pathlib import Path
import audio_upload,enigma
from audit_zmodem import scan,packet,metadata
from audit_audio_download import frontend_trace
from modem import Telnet
from test_transfer_dos import timestamp


def check(out,rows,before):
 source=Path(before['source_path']);expected=audio_upload.payload()
 executions=[i for i,r in enumerate(rows) if r.get('msg')=='Executing external protocol']
 exits=[i for i,r in enumerate(rows) if r.get('msg')=='Process exited']
 tail=[r.get('menuName') for r in rows[exits[-1]+1:]] if exits else []
 resumed=False
 try:
  start=tail.index('fileBaseMainMenu');search=tail.index('fileBaseSearch',start+1)
  tail.index('fileBaseListEntries',search+1);resumed=True
 except ValueError:pass
 entries=audio_upload.metadata()
 checks={'fresh_owned_upload':not before['metadata_before'],
  'canceled_upload_not_installed':not entries and not (audio_upload.storage()/audio_upload.NAME).exists(),
  'unchanged_DOS_source':source.read_bytes()==expected and
   [source.stat().st_ino,source.stat().st_size,source.stat().st_mtime_ns]==before['source_stat'],
  'real_owned_receive_helper':len(executions)==1 and rows[executions[0]].get('cmd')==str(audio_upload.helper()) and rows[executions[0]].get('direction')=='recv',
  'canceled_helper_retired':len(executions)==len(exits)==1 and executions[0]<exits[0] and rows[exits[0]].get('signal')==0 and rows[exits[0]].get('exitCode') not in (None,0),
  'postcancel_search_and_list':resumed}
 return checks,{'prepared':before,'metadata_after':entries,'menus_after_helper_exit':tail,
  'scope':'Preliminary cancellation source/storage/helper/return gates; independent CRC/ACK/CAN and whole-stream/cleanup audits remain required. No successful upload or temporary-file cleanup claim.'}


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);out=p.parse_args().cohort.resolve()
 read=lambda name:json.loads((out/name).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 r=read('result.json');assert r['route']=='upload' and r['upload_cancel']
 from enigma_receive_finish_instance import from_result
 context=from_result(r);assert context
 base=read('independent-audit.json');io=read('serial-io-audit.json')
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 checks={'producer':r['passed'],'complete_bytes_and_cleanup':base['passed'],'serial_ownership':io['evidence_consistent']}
 errors=[];detail=None
 try:
  trace,timing=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes'])
  cancel=sent.index(b'\x18'*8+b'\x08'*10)
  offers=[h for h in scan(sent) if h['type']==4 and h['offset']<cancel];assert len(offers)==1
  offer=offers[0];meta=packet(sent,offer['end'],offer['format']);expected=(out/'SEND/AUDIOUP.BIN').read_bytes()
  assert metadata(meta['payload'])==('AUDIOUP.BIN',len(expected))
  data=next(h for h in scan(sent,meta['end']) if h['type']==10)
  body=packet(sent,data['end'],data['format'])
  assert body['length']>=1024 and body['payload']==expected[:body['length']] and body['end']<cancel
  when=timestamp(trace,'dos',cancel)
  ack=next(h for h in scan(display) if h['type']==3 and h['position']>=1024 and timestamp(trace,'bbs',h['end']-1)<when)
  assert not any(h['type'] in (8,11) and h['offset']<cancel for h in scan(sent))
  search=sent.index(b'S\r',cancel+18);assert b'PCXTEST.BIN\r\r' in sent[search:]
  assert not list(scan(sent,search))
  checks['CRC_source_and_ACK_before_cancel']=True
  checks['CAN_before_EOF_and_live_search_afterward']=True
  detail={'offer':offer,'first_data':{k:v for k,v in body.items() if k!='payload'},'ACK':ack,'cancel_offset':cancel,'search_offset':search,'control_timing':timing}
 except Exception as error:
  errors.append(repr(error));checks['CRC_source_and_ACK_before_cancel']=False;checks['CAN_before_EOF_and_live_search_afterward']=False
 extra,_=check(out,[json.loads(s) for s in (out/'server-session.jsonl').read_text().splitlines()],r['upload']['prepared']);checks.update(extra)
 checks['capture_hashes']=all(sha(out/n)==h for n,h in r['captures_sha256'].items())
 report={'passed':all(checks.values()),'checks':checks,'errors':errors,'protocol':detail,'server_fixture':context,
  'capture_sha256':{n:sha(out/n) for n in ['result.json','independent-audit.json','serial-io-audit.json','bbs-input.bin','bbs-output.bin','server-session.jsonl','serial-input-events.jsonl','serial-write-events.jsonl']},
  'auditor_sha256':sha(Path(__file__)),
  'scope':'Actual DOS cancellation after visible confirmed progress through V22/1200 SIP/RTP/DSP to explicitly isolated ENiGMA receiver candidate. Passive CRC/source/ACK/CAN checks, absent official installation and subsequent real keyboard search/list. No retry, server temporary cleanup, packet loss, pressure, physical or whole-application acceptance.'}
 (out/'upload-cancel-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']

if __name__=='__main__':main()
