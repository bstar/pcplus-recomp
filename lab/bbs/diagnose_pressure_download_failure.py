#!/usr/bin/env python3
"""Preserve failed larger-file audio facts without converting a prefix to success."""
import argparse,json
from pathlib import Path
from audio_pressure_download import PressureDownload,NAME,SIZE
from audit_audio_download import frontend_trace
from audit_zmodem import scan,packet,metadata
from diagnose_audio_download_queue import table,stamp
from modem import Telnet
from synthmodem_vm_control import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 cohort=a.cohort.resolve();out=a.output.resolve();assert cohort.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 read=lambda n:json.loads((cohort/n).read_text());r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json');offline=read('offline-caller.json')
 assert not r['passed'] and not base['passed'] and r['download_pressure_preparation']
 prep=PressureDownload(ROOT/r['download_pressure_preparation']);expected=prep.path.read_bytes()
 for group in ('frozen_inputs','runtime_inputs','tool_inputs'):
  for n,h in r[group].items():assert sha(ROOT/n)==h,n
 for group in ('generated_inputs','captures_sha256'):
  for n,h in r[group].items():assert sha(cohort/n)==h,n
 for n,h in io['capture_sha256'].items():assert sha(cohort/n)==h,n
 serial=(cohort/'serial-in.bin').read_bytes();assert serial.startswith(b'ATZ\rATD1\r');online=serial[9:]
 assert offline['checker_sha256']==r['frozen_inputs']['lab/bbs/diagnose_audio_caller.js'] and offline['capture_sha256']==sha(cohort/'rtp-from-caller.bin')
 assert bytes.fromhex(''.join(row['hex'] for row in offline['received']))==online
 sent,_=Telnet().feed((cohort/'bbs-input.bin').read_bytes());display,_=Telnet().feed((cohort/'bbs-output.bin').read_bytes())
 caller=(cohort/'caller-decoded.bin').read_bytes();bridge=base['payloads']['expected_bridge_bytes'];decoded=caller[bridge:]
 assert len(decoded)<len(display) and display.startswith(decoded)
 # This intentionally validates only the exact observed prefix. It cannot
 # satisfy the full-stream gate that the normal auditor correctly rejected.
 trace,provenance=frontend_trace(cohort,sent,decoded,bridge);front=table(trace,'bbs')
 offer=None
 for h in scan(display):
  if h['type']==4:
   p=packet(display,h['end'],h['format'])
   if metadata(p['payload'])==(NAME,SIZE):offer=h;break
 assert offer;cursor=offer['end'];p=packet(display,cursor,offer['format']);cursor=p['end'];frames=[];verified=0;closing=[];eofs=[]
 while True:
  h=next(scan(display,cursor),None)
  if not h:break
  cursor=h['end']
  if h['type']==10:
   position=h['position']
   while True:
    p=packet(display,cursor,h['format']);cursor=p['end'];body=p['payload'];assert body==expected[position:position+len(body)]
    end=position+len(body);assert end<=SIZE
    frames.append(dict(header_offset=h['offset'],offset=p['offset'],end=p['end'],length=len(body),position_start=position,position_end=end,
     replayed=bool(body) and end<=verified,CRC_source_verified=True,ending=p['ending'],sha256=p['sha256']))
    verified=max(verified,end);position=end
    if p['ending'] in (104,107):break
  elif h['type']==11:eofs.append(h)
  elif h['type'] in (7,8):closing.append(h)
  else:assert h['type'] in (0,1,3,4,6,9,13,14),h
  if closing and len(closing)>=9:break
 controls=list(scan(sent));acks=[h['position'] for h in controls if h['type']==3];requests=[h['position'] for h in controls if h['type']==9]
 repeated=[p for p in frames if p['replayed']];assert not eofs and verified==15360 and max(acks)==15360 and requests==[0]+[15360]*9
 assert len(repeated)==9 and closing and closing[0]['type']==8
 assert all(p['end']<=len(decoded) for p in frames) and closing[0]['end']<=len(decoded)
 first_group=[p for p in frames if not p['replayed']];last=first_group[-1]
 completion=stamp(front,last['end']-1);finish=stamp(front,closing[0]['end']-1)
 server_rows=[json.loads(s) for s in (cohort/'server-session.jsonl').read_text().splitlines()]
 exits=[s for s in server_rows if s.get('msg')=='Process exited'];assert len(exits)==1 and exits[0]['exitCode']==255
 before=(cohort/'BEFORE.BIN').read_bytes();after=(cohort/'AFTER.BIN').read_bytes();assert len(before)==len(after)==42 and before[:32]==after[:32] and before[36:]==after[36:]
 checks=dict(producer_frozen_inputs_and_captures_exact=True,independent_caller_equals_all394_online_bytes=len(online)==394,
  complete_decoded_prefix_exact=True,all_observed_data_CRC_and_source_verified=True,
  actual_protocol_stops_below64KiB=verified<SIZE and verified<65536,
  premature_sender_finish_without_EOF=not eofs and bool(closing),
  exact_15360_ACK_and_nine_recovery_requests=True,stock_helper_failed255=True,
  product_IRQ_UART_PIC_restored=True,only_helper_INT1C_differs=before[32:36]!=after[32:36],
  no_installed_file=not (cohort/'RECV'/NAME).exists(),official_counter_not_advanced=not r['checks']['official_download_counter_advanced'],
  serial_callbacks_accounted=io['evidence_consistent'] and all(io['counters'][k]==0 for k in ('skippedBytes','failedCallbackBytes','pendingBytes')))
 assert all(checks.values())
 result=dict(passed=False,actual_ENiGMA_larger_download_audio_accepted=False,diagnosis_checks_passed=True,checks=checks,
  cohort=str(cohort.relative_to(ROOT)),producer_failed_checks=[k for k,v in r['checks'].items() if not v],independent_failed_checks=[k for k,v in base['checks'].items() if not v],
  source_bytes=SIZE,source_sha256=sha(prep.path),observed_verified_source_extent=verified,
  online_bytes=len(online),BBS_emitted_bytes=len(display),decoded_exact_prefix_bytes=len(decoded),undecoded_suffix_bytes=len(display)-len(decoded),
  observed_packets=frames,verified_replay_packets=len(repeated),verified_replay_payload_bytes=sum(p['length'] for p in repeated),
  receiver_ACK_positions=acks,receiver_ZRPOS_positions=requests,sender_EOF_count=len(eofs),sender_closing_headers=closing,
  initial_data_group_decoded_frontend_seconds=completion,first_premature_ZFIN_decoded_frontend_seconds=finish,
  serial_counters=io['counters'],serial_errors=io['error_events'],hardware_differing_offsets=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b],
  helper_exit_code=255,download_metadata_before=r['download']['metadata_before'],download_metadata_after=r['download']['metadata_after'],
  clock_provenance=provenance,producer_inputs=r['frozen_inputs'],runtime_inputs=r['runtime_inputs'],
  inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'lab/bbs/audit_audio_download.py',ROOT/'lab/bbs/audit_zmodem.py',ROOT/'lab/bbs/audio_pressure_download.py',ROOT/'lab/bbs/diagnose_audio_download_queue.py')},
  captures_sha256={n:sha(cohort/n) for n in [*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json','offline-caller.json','download-audit.stderr']},
  scope='Failed larger-file audio run, not transfer acceptance. Every observed data packet is CRC/source verified, and the decoded display is an exact84648-byte prefix of89316 emitted bytes; all394 online bytes match independent caller decoding. Sender never emits EOF and abandons at verified extent15360 before64KiB, with nine old-data replays and exit255. Receiver ACK/recovery positions corroborate that extent. Source rejects ZFIN with an owned incomplete file; RX file error is a generic mapped fault and does not establish a disk error. Product IRQ/UART/PIC restore; only the test helper INT1C remains different. Full-stream/normal exit/file/accounting/cleanup gates remain false. Queuing/negotiation and active replay recovery need controlled investigation; no exclusive cause/fix, physical or whole-application claim.')
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':False,'diagnosis_checks_passed':True,'verified_source_extent':verified,'verified_replays':len(repeated),'decoded_exact_prefix_bytes':len(decoded)}))


if __name__=='__main__':main()
