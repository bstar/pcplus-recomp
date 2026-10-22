#!/usr/bin/env python3
"""Seal a complete larger-file explicitly identified ENiGMA audio download."""
import argparse,json,subprocess
from pathlib import Path
import enigma
from modem import Telnet
from audio_pressure_download import PressureDownload,NAME,SIZE,report
from audit_audio_download import frontend_trace
from test_transfer_dos import timestamp
from synthmodem_buffered_runtime import validate as validate_runtime
from synthmodem_vm_control import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--protocol-controls',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.cohort.resolve();target=a.output.resolve();controls=a.protocol_controls.resolve()
 assert out.is_relative_to(ROOT/'build') and controls.is_relative_to(ROOT/'build')
 assert target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 read=lambda n:json.loads((out/n).read_text())
 r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json');transfer=read('download-audit.json');offline=read('offline-caller.json');timing=read('control-timing-verifier.json')
 from enigma_fixture import from_result
 server_fixture=from_result(r)
 entrypoint=ROOT/'lab/bbs/audit_audio_download_bound.py'
 failed_entry=out/'download-audit-direct-entry-failure.json'
 entrypoint_failure=None
 if failed_entry.exists():
  previous=json.loads(failed_entry.read_text())
  assert not previous['passed']
  assert {k for k,v in previous['checks'].items() if not v}=={'real_owned_helper','official_file_and_counter'}
  assert {k:v for k,v in previous.items() if k not in ('passed','checks')}=={k:v for k,v in transfer.items() if k not in ('passed','checks')}
  entrypoint_failure=dict(capture=failed_entry.name,sha256=sha(failed_entry),
   failed_checks=[k for k,v in previous['checks'].items() if not v],
   cause='Direct __main__ namespace retained stock storage/helper globals; canonical module receives fixture rebinding. All other audit fields are identical.')
 assert r['route']=='download' and r['download_pressure_preparation'] and r['download']['pressure']
 assert r['buffered_runtime_proof'] and r['posttrain_hold'] and r['input_sequence_timeout_ms']==250
 assert Path(r['server_root'])==enigma.SOURCE and r['server_revision']==enigma.COMMIT
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=enigma.SOURCE,text=True).strip()==enigma.COMMIT
 subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=enigma.SOURCE,check=True)
 rows=[json.loads(line) for line in (out/'server-session.jsonl').read_text().splitlines() if line.strip()]
 authenticated={row['sessionId'] for row in rows if row.get('msg')=='User "loclab" successfully logged in'}
 assert len(authenticated)==1;session_id=next(iter(authenticated))
 executions=[i for i,row in enumerate(rows) if row.get('msg')=='Executing external protocol']
 exits=[i for i,row in enumerate(rows) if row.get('msg')=='Process exited' and row.get('exitCode')==0]
 assert len(executions)==len(exits)==1 and executions[0]<exits[0]
 assert rows[executions[0]]['sessionId']==rows[exits[0]]['sessionId']==session_id
 own_tail=[row.get('menuName') for row in rows[exits[0]+1:] if row.get('sessionId')==session_id and row.get('menuName')]
 first=own_tail.index('fileBaseMainMenu');search=own_tail.index('fileBaseSearch',first+1);own_tail.index('fileBaseListEntries',search+1)
 for result in (r,base,transfer):assert result['passed'] and all(result['checks'].values())
 assert not transfer['errors'] and transfer['source_bytes']==SIZE
 assert io['evidence_consistent'] and all(io['checks'].values()) and not io['error_events']
 assert all(io['counters'][n]==0 for n in ('pendingBytes','failedCallbackBytes','skippedBytes'))
 def inputs(group):
  for n,h in group.items():assert sha(ROOT/n)==h,n
 def captures(group):
  for n,h in group.items():assert sha(out/n)==h,n
 for group in ('frozen_inputs','runtime_inputs','tool_inputs'):inputs(r[group])
 for group in ('generated_inputs','captures_sha256'):captures(r[group])
 start=read('run-start.json');exits_recorded=read('exit-status.json')
 assert exits_recorded==dict(DOS=0,node=0)
 for group in ('frozen_inputs','runtime_inputs','tool_inputs','generated_inputs','server_inputs'):
  assert start[group]==r[group],group
 assert start['server_fixture']==server_fixture and start['download_metadata_before']==r['download']['metadata_before']
 assert start['profile_sha256']==sha(out/'MODEM.PRM')
 journal=read('server-log-capture/result.json');assert journal['passed']
 assert journal['boundary']==read('server-log-boundary.json') and journal['boundary_sha256']==sha(out/'server-log-boundary.json')
 journal_rows=[]
 for segment in journal['segments']:
  path=out/'server-log-capture'/segment['capture'];body=path.read_bytes()
  assert sha(path)==segment['sha256'] and len(body)==segment['end']-segment['start']
  journal_rows.extend(json.loads(line) for line in body.splitlines() if line.strip())
 assert len(journal_rows)==journal['records']
 assert [row for row in journal_rows if row.get('sessionId')==session_id]==rows
 inputs(base['audit_inputs']);captures(io['capture_sha256']);captures(transfer['capture_sha256'])
 for n,h in r['server_inputs'].items():assert sha(enigma.SOURCE/n)==h,n
 assert base['producer_sha256']==sha(out/'result.json')
 assert base['auditor_sha256']==r['frozen_inputs']['lab/bbs/audit_synthmodem_audio_dos.py']
 assert io['auditor_sha256']==r['frozen_inputs']['lab/bbs/audit_serial_io_evidence.py']
 assert transfer['auditor_sha256']==r['frozen_inputs']['lab/bbs/audit_audio_download.py']
 assert transfer['protocol_auditor_sha256']==r['frozen_inputs']['lab/bbs/audit_zmodem.py']
 first=Path(next(iter(r['runtime_inputs'])));runtime=next(p for p in first.parents if (p/'source/config.js').is_file())
 assert validate_runtime(runtime,ROOT/r['buffered_runtime_proof'])==r['runtime_inputs']
 prep=PressureDownload(ROOT/r['download_pressure_preparation']);source=prep.path
 assert prep.server_fixture==server_fixture
 assert sha(out/'program/EXITKEY.COM')==prep.production_helper_sha256
 for name,path in [('TERMINAL.EXE','build/terminal/TERMINAL.EXE'),('ASPECT.EXE','build/aspect-runner/ASPECT.EXE')]:assert sha(out/'program'/name)==r['frozen_inputs'][path]
 assert (out/'RECV'/NAME).read_bytes()==source.read_bytes() and source.stat().st_size==SIZE>65536
 assert transfer['source_sha256']==transfer['received_sha256']==sha(source)
 assert transfer['official_metadata']==r['download']['metadata_after']
 before=r['download']['metadata_before'];after=r['download']['metadata_after'];assert len(before)==len(after)==1
 assert after[0]['meta'].get('dl_count',0)==before[0]['meta'].get('dl_count',0)+1
 prefix=b'ATZ\rATD1\r';serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(prefix);online=serial[len(prefix):]
 assert offline['checker_sha256']==r['frozen_inputs']['lab/bbs/diagnose_audio_caller.js']
 assert offline['capture_sha256']==sha(out/'rtp-from-caller.bin')
 assert offline['decoder_sha256']==sha(runtime/'source/src/dsp/protocols/V22Demodulator.js')
 assert bytes.fromhex(''.join(row['hex'] for row in offline['received']))==online
 assert timing['passed'] and not timing['protocol_only'] and timing['input_transfer_audit_passed']
 assert len(timing['negative_cases'])==2 and all(c['rejected'] for c in timing['negative_cases'])
 assert timing['checker_sha256']==sha(ROOT/'lab/bbs/check_audio_control_timing.py')
 assert timing['auditor_sha256']==transfer['auditor_sha256'] and timing['protocol_auditor_sha256']==transfer['protocol_auditor_sha256']
 captures(timing['capture_sha256'])
 negative=json.loads(controls.read_text());assert negative['passed'] and negative['original_reference_captures_unchanged']
 assert negative['real_reference_baseline_protocol_exact'] and len(negative['cases'])==9 and all(c['rejected'] for c in negative['cases'])
 assert negative['source_bytes']==SIZE and negative['source_sha256']==sha(source)
 assert ROOT/negative['reference']==prep.reference and negative['reference_sha256']==sha(prep.reference)
 inputs(negative['inputs']);reference=report(prep.reference)
 for n,h in negative['captures_sha256'].items():assert sha(prep.reference.parent/n)==h,n
 protocol=transfer['protocol'];assert len(protocol['files'])==1 and protocol['files'][0]['name']==NAME
 f=protocol['files'][0];assert f['length']==SIZE and f['sha256']==sha(source)
 max_packet=max(p['length'] for p in f['packets']);max_group=group=0
 for packet in f['packets']:
  group+=packet['length']
  if packet['ending'] in (104,107):max_group=max(max_group,group);group=0
 assert group==0
 if server_fixture:
  assert server_fixture['kind']=='sexyz-send-credit-eof-candidate' and r['zmodem_receive_credit']==256
  assert transfer['server_fixture']==server_fixture and negative['server_fixture']==server_fixture
  assert max_packet<=256 and max_group<=256
  assert 'TERMINAL @D:\\MODEM.PRM /E:D:\\CALL.DIR /N:1 /Z:256\n' in (out/'dosbox.conf').read_text()
 for n,h in r['frozen_inputs'].items():assert sha(out/'frozen-source'/n)==h,n
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 trace,_=frontend_trace(out,sent,display,base['payloads']['expected_bridge_bytes'])
 start=timestamp(trace,'bbs',protocol['start']);finish=timestamp(trace,'bbs',protocol['end']-1);assert finish>start
 replay=[p for p in f['packets'] if p['replayed']];after_eof=[p for p in replay if p['after_eof']]
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json','offline-caller.json','download-audit.json','control-timing-verifier.json','RECV/'+NAME]))
 if entrypoint_failure:names.append(failed_entry.name)
 result=dict(passed=True,actual_ENiGMA_larger_download_audio_accepted=True,cohort=str(out.relative_to(ROOT)),server_fixture=server_fixture,
  download_audit_entrypoint=dict(path=str(entrypoint.relative_to(ROOT)),sha256=sha(entrypoint)),
  preserved_direct_entry_audit_failure=entrypoint_failure,
  authenticated_session_id=session_id,helper_and_posttransfer_menus_owned_by_authenticated_session=True,
  durable_run_manifest_and_exit_status_verified=True,exact_journal_ranges_verified=True,journal_segments=len(journal['segments']),
  unrelated_server_log_rows=sum(row.get('sessionId') not in (None,session_id) for row in rows),
  zmodem_receive_credit=r.get('zmodem_receive_credit'),max_packet_payload=max_packet,max_synchronous_group_payload=max_group,
  check_counts=dict(producer=len(r['checks']),independent=len(base['checks']),serial=len(io['checks']),download=len(transfer['checks']),actual_control_timing_counterexamples=2,TCP_protocol_counterexamples=9),
  producer_checks=r['checks'],independent_checks=base['checks'],serial_checks=io['checks'],download_checks=transfer['checks'],
  source_bytes=SIZE,source_sha256=sha(source),received_sha256=sha(out/'RECV'/NAME),
  exact_online_bytes=len(online),exact_BBS_display_bytes=len(display),payloads=base['payloads'],serial_counters=io['counters'],hardware_snapshot=base['hardware_snapshot'],
  protocol=protocol,verified_retransmissions=len(replay),verified_retransmitted_payload_bytes=sum(p['length'] for p in replay),
  verified_post_EOF_retransmissions=len(after_eof),verified_post_EOF_retransmitted_payload_bytes=sum(p['length'] for p in after_eof),
  protocol_frontend_start_seconds=start,protocol_frontend_finish_seconds=finish,protocol_observed_seconds=finish-start,effective_payload_bytes_per_second=SIZE/(finish-start),
  download_count_before=before[0]['meta'].get('dl_count',0),download_count_after=after[0]['meta'].get('dl_count',0),
  terminal_sha256=sha(out/'program/TERMINAL.EXE'),ASPECT_sha256=sha(out/'program/ASPECT.EXE'),server_revision=r['server_revision'],server_inputs=r['server_inputs'],
  preparation=r['download_pressure_preparation'],preparation_sha256=sha(ROOT/r['download_pressure_preparation']),buffered_runtime_proof=r['buffered_runtime_proof'],
  protocol_controls=str(controls.relative_to(ROOT)),protocol_controls_sha256=sha(controls),control_inputs=negative['inputs'],
  producer_inputs=r['frozen_inputs'],runtime_inputs=r['runtime_inputs'],tool_inputs=r['tool_inputs'],audit_inputs=base['audit_inputs'],
  captures_sha256={n:sha(out/n) for n in names},recorder_sha256=sha(Path(__file__)),
  scope='One65797-byte source-built DOS automatic ZMODEM download from pinned '+('isolated sender-candidate' if server_fixture else 'stock owned')+' ENiGMA through software SIP/RTP/V22-1200 DSP/Telnet with normal200ms runtime. Full online/display/caller identity, CRC/source/position/EOF/ZFIN/OO/opposite controls, checked installed file above64KiB, official accounting, actual post-helper Search/List and normal DOS/hardware cleanup are required. Transfer duration is frontend-observed ZFILE-through-OO, not application paint or protocol-free line throughput. Retransmissions remain explicit; no arbitrary-duration/sustained-session/efficiency/latency budget, other directions/profiles/protocols, physical Boca/SPA2102 or F01-F16 whole-application completion is claimed.')
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':True,'actual_ENiGMA_larger_download_audio_accepted':True,'check_counts':result['check_counts'],'protocol_seconds':finish-start,'verified_retransmissions':len(replay)}))


if __name__=='__main__':main()
