#!/usr/bin/env python3
"""Seal actual client cancellation recovery while retaining server cleanup failure."""
import argparse,datetime,hashlib,json
from pathlib import Path
from enigma_receive_finish_instance import ROOT,STOCK,from_result,validate
from enigma_upload_dos import metadata


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.cohort.resolve();target=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 read=lambda n:json.loads((out/n).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json');transfer=read('upload-cancel-audit.json');timing=read('cancel-timing-verifier.json')
 assert r['upload_cancel'] and r['route']=='upload'
 context=from_result(r);assert context
 for d in (r,base,io,transfer):
  assert d.get('passed',d.get('evidence_consistent')) and all(d['checks'].values())
 assert timing['passed'] and timing['input_transfer_audit_passed'] and len(timing['negative_cases'])==4
 assert all(c['rejected'] for c in timing['negative_cases']) and not transfer['errors']
 for d in (r,transfer,timing):
  hashes=d.get('captures_sha256',d.get('capture_sha256'));assert hashes
  for n,h in hashes.items():assert sha(out/n)==h,n
 for group in ('frozen_inputs','runtime_inputs','tool_inputs'):
  for n,h in r[group].items():
   path=Path(n);path=path if path.is_absolute() else ROOT/path
   assert sha(path)==h,n
 for n,h in r['generated_inputs'].items():assert sha(out/n)==h,n
 assert sha(out/'program/TERMINAL.EXE')==r['frozen_inputs']['build/terminal/TERMINAL.EXE']
 for n,h in r['server_inputs'].items():assert sha(Path(context['source'])/n)==h,n
 prefix=b'ATZ\rATD1\r';serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(prefix)
 offline=bytes.fromhex(''.join(c['hex'] for c in read('offline-caller.json')['received']))
 assert offline==serial[len(prefix):] and len(offline)==base['payloads']['guest_DATA_RX_bytes']
 source=out/'SEND/AUDIOUP.BIN';before=r['upload']['prepared'];assert len(source.read_bytes())==11521 and sha(source)==before['source_sha256']
 assert [source.stat().st_ino,source.stat().st_size,source.stat().st_mtime_ns]==before['source_stat']
 assert not metadata(Path(context['source']),['AUDIOUP.BIN'])[0]['entries']
 assert not Path(before['target_path']).exists()
 info=validate(ROOT/context['lab']);assert metadata(STOCK,['AUDIOUP.BIN'])==info['stock_upload']
 for n,h in info['stock_server_inputs'].items():assert sha(STOCK/n)==h,n
 assert sha(STOCK.parent/'helpers/sexyz')==info['stock_helper_sha256']
 assert sha(STOCK/'file_base/pcplus_transfer/AUDIOUP.BIN')==info['stock_upload'][0]['entries'][0]['fileSha256']
 temp=read('receiver-temp-observation.json');backup=ROOT/temp['preserved_copy']
 assert temp['observed_after_helper_exit'] and temp['directory_exists'] and temp['partial_matches_source_prefix']
 assert backup.read_bytes()==source.read_bytes()[:1024] and sha(backup)==temp['preserved_sha256']
 assert len(temp['files'])==1 and temp['files'][0]['bytes']==1024 and temp['files'][0]['sha256']==sha(backup)
 rows=[json.loads(s) for s in (out/'server-session.jsonl').read_text().splitlines()]
 execution=next(c for c in rows if c.get('msg')=='Executing external protocol')
 exits=[c for c in rows if c.get('msg')=='Process exited'];assert len(exits)==1 and exits[0]['exitCode']==1 and exits[0]['signal']==0
 assert Path(execution['tempDir'])==Path(temp['tempDir'])
 assert datetime.datetime.fromisoformat(temp['observation_time'])>datetime.datetime.fromisoformat(exits[0]['time'].replace('Z','+00:00'))
 original_temp=Path(temp['files'][0]['path']);assert original_temp.parent==Path(temp['tempDir'])
 if original_temp.exists():assert original_temp.read_bytes()==backup.read_bytes()
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json','upload-cancel-audit.json','cancel-timing-verifier.json','offline-caller.json','receiver-temp-observation.json']))
 result={'passed':False,'client_cancellation_workflow_passed':True,'receiver_temporary_cleanup_passed':False,
  'cohort':str(out.relative_to(ROOT)),'server_fixture':context,
  'checks':{'producer':True,'complete_bytes_and_cleanup':True,'serial_ownership':True,'CRC_source_ACK_CAN_and_resumed_input':True,
   'control_causality_and_four_negative_mutants':True,'complete_offline_caller_identity':True,'source_bytes_and_stat_preserved':True,
   'no_official_installation':True,'stock_server_helper_upload_preserved':True,'receiver_temporary_data_removed':False},
  'check_counts':{'producer':len(r['checks']),'independent':len(base['checks']),'ownership':len(io['checks']),'cancellation':len(transfer['checks'])},
  'producer_checks':r['checks'],'independent_checks':base['checks'],'ownership_checks':io['checks'],'cancellation_checks':transfer['checks'],
  'terminal_sha256':sha(out/'program/TERMINAL.EXE'),'source_bytes':11521,'source_sha256':sha(source),
  'payloads':base['payloads'],'serial_counters':io['counters'],'hardware_snapshot':base['hardware_snapshot'],
  'protocol':transfer['protocol'],'control_timing_verifier':timing,'receiver_exit':exits[0],
  'retained_temporary':temp,'producer_inputs':r['frozen_inputs'],'runtime_inputs':r['runtime_inputs'],'server_inputs':r['server_inputs'],
  'capture_sha256':{n:sha(out/n) for n in names},'recorder_sha256':sha(Path(__file__)),
  'scope':'One actual DOS progress-triggered upload cancellation on the explicitly isolated ENiGMA receiver candidate through V22/1200 SIP/RTP/DSP at38400 DTE. Client recovery passes all75 producer/byte/ownership/cancellation gates, four control-time negative mutants, exact offline decode, real search/list and normal DOS/hardware restoration. Overall cancellation acceptance remains false: receiver-owned1024-byte source prefix remains after helper exit1 and is preserved without deletion. Stock state is unchanged. Retry, pressure/loss, other peers, physical Boca/SPA2102 and all F01-F16 requirements remain open.'}
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':False,'client_cancellation_workflow_passed':True,'receiver_temporary_cleanup_passed':False,'check_counts':result['check_counts'],'receipt':str(target)}))

if __name__=='__main__':main()
