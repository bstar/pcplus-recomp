#!/usr/bin/env python3
"""Seal same-call retry evidence without waiving the failed minimum hold."""
import argparse,hashlib,json,re
from pathlib import Path
from enigma_receive_finish_instance import ROOT,STOCK,from_result,validate
from enigma_upload_dos import metadata


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.cohort.resolve();target=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 read=lambda n:json.loads((out/n).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json');audit=read('upload-retry-audit-v2.json');timing=read('retry-control-timing-verifier.json');finish=read('retry-finish-diagnosis.json')
 assert r['passed'] and r['upload_cancel_retry'] and all(r['checks'].values())
 assert not base['passed'] and {k for k,v in base['checks'].items() if not v}=={'single_normal_post_train_hold'}
 holds=re.findall(r'Post-train hold complete .*waited (\d+)ms, dropped (\d+) bytes\)',(out/'node.log').read_text());assert holds==[('5999','0')]
 assert io['evidence_consistent'] and all(io['checks'].values())
 assert not audit['passed'] and {k for k,v in audit['checks'].items() if not v}=={'whole_stream_and_cleanup'} and not audit['errors']
 assert timing['passed'] and timing['protocol_only'] and not timing['input_transfer_audit_passed']
 assert len(timing['negative_cases'])==2 and all(c['rejected'] for c in timing['negative_cases'])
 assert finish['sender_OO_frontend_after_helper_exit_ms']<=0 and all(v<=0 for v in finish['sender_OO_relay_after_helper_exit_ms'])
 context=from_result(r);assert context
 for d in (r,audit,timing,finish):
  hashes=d.get('captures_sha256',d.get('capture_sha256'));assert hashes
  for n,h in hashes.items():assert sha(out/n)==h,n
 for group in ('frozen_inputs','runtime_inputs','tool_inputs'):
  for n,h in r[group].items():
   path=Path(n);path=path if path.is_absolute() else ROOT/path
   assert sha(path)==h,n
 for n,h in r['generated_inputs'].items():assert sha(out/n)==h,n
 for n,h in r['server_inputs'].items():assert sha(Path(context['source'])/n)==h,n
 assert sha(out/'program/TERMINAL.EXE')==r['frozen_inputs']['build/terminal/TERMINAL.EXE']
 source=out/'SEND/AUDIOUP.BIN';before=r['upload']['prepared'];assert len(source.read_bytes())==11521 and sha(source)==before['source_sha256']
 assert [source.stat().st_ino,source.stat().st_size,source.stat().st_mtime_ns]==before['source_stat']
 entries=metadata(Path(context['source']),['AUDIOUP.BIN'])[0]['entries'];assert entries==r['upload']['metadata_after'] and len(entries)==1
 assert Path(entries[0]['filePath']).read_bytes()==source.read_bytes() and entries[0]['fileSha256']==sha(source)
 prefix=b'ATZ\rATD1\r';serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(prefix)
 offline=bytes.fromhex(''.join(c['hex'] for c in read('offline-caller.json')['received']))
 assert serial[len(prefix):]==offline and len(offline)==base['payloads']['guest_DATA_RX_bytes']
 info=validate(ROOT/context['lab']);assert metadata(STOCK,['AUDIOUP.BIN'])==info['stock_upload']
 for n,h in info['stock_server_inputs'].items():assert sha(STOCK/n)==h,n
 assert sha(STOCK.parent/'helpers/sexyz')==info['stock_helper_sha256']
 assert sha(STOCK/'file_base/pcplus_transfer/AUDIOUP.BIN')==info['stock_upload'][0]['entries'][0]['fileSha256']
 protocol=audit['retry_protocol'];assert len(protocol['files'])==1 and protocol['files'][0]['length']==11521
 assert len(protocol['files'][0]['packets'])==12 and not any(p['replayed'] for p in protocol['files'][0]['packets'])
 initial=read('upload-retry-audit.json');assert not initial['passed'] and initial['errors']==['AssertionError()']
 assert initial['auditor_sha256']==r['frozen_inputs']['lab/bbs/audio_upload_retry.py']==audit['original_auditor_sha256']
 assert audit['first_cancellation']['retry_offer_count']==2
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json','upload-retry-audit.json','upload-retry-audit-v2.json','retry-control-timing-verifier.json','retry-finish-diagnosis.json','offline-caller.json']))
 result={'passed':False,'client_retry_workflow_passed':True,'minimum_post_train_hold_passed':False,'cohort':str(out.relative_to(ROOT)),
  'server_fixture':context,'observed_hold_ms':5999,'required_minimum_hold_ms':6000,
  'check_counts':{'producer':len(r['checks']),'independent':len(base['checks']),'ownership':len(io['checks']),'retry':len(audit['checks'])},
  'producer_checks':r['checks'],'independent_checks':base['checks'],'ownership_checks':io['checks'],'retry_checks':audit['checks'],
  'terminal_sha256':sha(out/'program/TERMINAL.EXE'),'source_bytes':11521,'source_sha256':sha(source),'official_metadata':entries,
  'first_cancellation':audit['first_cancellation'],'retry_protocol':protocol,'control_timing_verifier':timing,'finish_diagnosis':finish,
  'payloads':base['payloads'],'serial_counters':io['counters'],'hardware_snapshot':base['hardware_snapshot'],
  'reaudit_reason':audit['reaudit_reason'],'original_auditor_errors':initial['errors'],
  'producer_inputs':r['frozen_inputs'],'runtime_inputs':r['runtime_inputs'],'server_inputs':r['server_inputs'],
  'capture_sha256':{n:sha(out/n) for n in names},'auditor_sha256':sha(ROOT/'lab/bbs/audit_audio_upload_retry.py'),'recorder_sha256':sha(Path(__file__)),
  'scope':'Actual DOS cancel-after-confirmed-data/ACK and full11521-byte retry in one terminal/modem/BBS connection on the explicit receiver candidate. Exact bidirectional bytes, CRC/source/storage, two helper exits1/0,12 unreplayed retry packets, required closing before retirement, real search/list and normal DOS/hardware restoration pass. Two metadata announcements are validated within one retry, not counted as extra helpers; original strict-count auditor/report retained. Overall acceptance stays false because5999ms violates unchanged6000ms hold. Timing negatives run explicitly protocol-only and cannot waive that failure. New minimum-hold runtime, temporary cleanup, pressure/loss, other peers, physical and F01-F16 requirements remain open.'}
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':False,'client_retry_workflow_passed':True,'minimum_post_train_hold_passed':False,'check_counts':result['check_counts'],'receipt':str(target)}))

if __name__=='__main__':main()
