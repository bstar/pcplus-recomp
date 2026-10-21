#!/usr/bin/env python3
"""Seal exact native Synchronet cancellation audio/DOS workflow at its tested scope."""
import argparse,hashlib,json,re
from pathlib import Path
from audio_synchronet import ROOT,snapshot,message_bodies,sha
from modem import Telnet
from synthmodem_posttrain_validation import validate as validate_runtime


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.cohort.resolve();target=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 read=lambda n:json.loads((out/n).read_text());r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json')
 assert r['peer']=='synchronet' and r['route']=='xmodem-cancel' and r['posttrain_hold'] and r['input_sequence_timeout_ms']==250
 for data in (r,base,io):assert data.get('passed',data.get('evidence_consistent')) and all(data['checks'].values())
 for group in ('frozen_inputs','runtime_inputs','tool_inputs'):
  for n,h in r[group].items():
   path=Path(n);path=path if path.is_absolute() else ROOT/path
   assert sha(path)==h,n
 for n,h in r['generated_inputs'].items():assert sha(out/n)==h,n
 for n,h in r['captures_sha256'].items():assert sha(out/n)==h,n
 assert sha(out/'program/TERMINAL.EXE')==r['frozen_inputs']['build/terminal/TERMINAL.EXE']
 assert sha(out/'program/ASPECT.EXE')==r['frozen_inputs']['build/aspect-runner/ASPECT.EXE']
 runtime=Path(next(iter(r['runtime_inputs'])))
 runtime=next(p for p in runtime.parents if (p/'source/config.js').is_file())
 if r.get('buffered_runtime_proof'):
  from synthmodem_buffered_runtime import validate as validate_buffered
  assert validate_buffered(runtime,ROOT/r['buffered_runtime_proof'])==r['runtime_inputs']
 else:assert validate_runtime(runtime)==r['runtime_inputs']
 assert snapshot()==r['server'] and message_bodies()==r['message_bodies']
 for k in ('dnloads','dnloadb','posts','email','feedback'):assert r['statistics_before']['Total'][k]==r['statistics_after']['Total'][k]
 prefix=b'ATZ\rATD1\r';serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(prefix);online=serial[len(prefix):]
 offline=bytes.fromhex(''.join(c['hex'] for c in read('offline-caller.json')['received']));assert online==offline
 raw=(out/'control-wire.bin').read_bytes();at=0;guest=bytearray()
 while at<len(raw):
  size=int.from_bytes(raw[at:at+2],'little');assert size>=1 and at+size+2<=len(raw)
  if raw[at+2]==0x15:guest.extend(raw[at+3:at+size+2])
  at+=size+2
 assert online==guest
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes());address=online.split(b'\r',1)[0]
 assert online==address+b'\r'+sent
 bridge=(b'PCPLUS DSP LAB V22 1200\r\nCONNECT> Connecting to '+address+b'...\r\r\nConnected to '+address+b'.\r\r\nIn-band menu escape disabled; remote close returns to menu. QUIT there hangs up.\r\r\n\r\r\n')
 assert (out/'caller-decoded.bin').read_bytes()==bridge+display
 holds=re.findall(r'Post-train hold complete .*waited (\d+)ms, dropped (\d+) bytes\)',(out/'node.log').read_text());assert len(holds)==1 and 6000<=int(holds[0][0])<=15500 and holds[0][1]=='0'
 prerequisites={n:h for n,h in r['frozen_inputs'].items() if n.endswith('/result.json')};assert len(prerequisites)==4+bool(r.get('buffered_runtime_proof'))
 for n in prerequisites:assert json.loads((ROOT/n).read_text())['passed']
 recipe=[json.loads((ROOT/n).read_text()) for n in prerequisites if 'recipe' in n];assert len(recipe)==1 and all(c['raw_match_possible'] for c in recipe[0]['cases'])
 timing=read('cancel-control-checks.json');assert timing['passed'] and all(timing['checks'].values())
 for n,h in timing['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in timing['captures_sha256'].items():assert sha(out/n)==h,n
 metadata=read('cancel-metadata-audit.json');assert metadata['passed'] and all(metadata['checks'].values())
 for n,h in metadata['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in metadata['captures_sha256'].items():assert sha(out/n)==h,n
 from audio_synchronet_cancel_fixed import AREA,payload,stored_files,name_for
 NAME=r['upload']['name'];assert NAME in {name_for(slot) for slot in range(1,1000)}
 source=ROOT/r['upload']['source_path'];assert source.read_bytes()==payload(NAME) and sha(source)==r['upload']['source_sha256']
 partial=(AREA/NAME).read_bytes() if (AREA/NAME).exists() else b''
 assert partial==(out/'receiver-partial.bin').read_bytes() and payload(NAME).startswith(partial) and len(partial)<11521
 assert all(stored_files().get(n)==h for n,h in r['upload']['existing_files_before'].items())
 cleanup=metadata['server_partial_cleanup_accepted'];assert cleanup==r['server_partial_cleanup_accepted']==base['server_partial_cleanup_accepted']
 diagnosis=read('cancel-boundary-diagnosis.json');assert diagnosis['passed'] and not diagnosis['cancel_splits_next_frame']
 for n,h in diagnosis['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in diagnosis['captures_sha256'].items():assert sha(out/n)==h,n
 for n,h in diagnosis['source_authority'].items():assert sha(ROOT/n)==h,n
 baseline_path=ROOT/'docs/validation/synthmodem-synchronet-cancel-audio-01.json'
 baseline=json.loads(baseline_path.read_text());assert not baseline['responsive_cancellation_accepted']
 for n,h in baseline['capture_sha256'].items():assert sha(ROOT/baseline['cohort']/n)==h,n
 assert baseline['terminal_sha256']!=r['frozen_inputs']['build/terminal/TERMINAL.EXE']
 old_delay=baseline['boundary_diagnosis']['CAN_to_remote_pause_seconds'];new_delay=diagnosis['CAN_to_remote_pause_seconds']
 rate=r['gateway']['callerInfo']['bps'];assert rate==1200
 # One conservative full1029-byte 8N1 frame at measured carrier plus6s margin.
 response_budget=__import__('math').ceil(1029*10/rate+6)
 assert new_delay<=response_budget and new_delay<old_delay/2
 proof=json.loads((ROOT/'build/terminal/terminal-upload-cancel-boundary.json').read_text())
 assert proof['passed'] and len(proof['cases'])==37 and proof['binary_sha256']==r['frozen_inputs']['build/terminal/TERMINAL.EXE']
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json','offline-caller.json','server-inputs.json',str(source.relative_to(out)),'receiver-partial.bin','cancel-control-checks.json','cancel-boundary-diagnosis.json','cancel-metadata-audit.json','metadata-after.js','metadata-after.json','metadata-after.stdout','metadata-after.stderr']))
 server=r['server'];tree_hash=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
 result={'passed':False,'client_workflow_passed':True,'eventual_client_recovery_verified':True,'responsive_cancellation_accepted':True,'actual_Synchronet_audio_accepted':False,'actual_client_cancellation_accepted':True,'server_partial_cleanup_accepted':cleanup,'cohort':str(out.relative_to(ROOT)),'route':'login/native-Escape-after-ACK/CAN/post-cancel-Files/Main',
  'check_counts':{'producer':len(r['checks']),'independent':len(base['checks']),'ownership':len(io['checks']),'official_partial_accounting':len(metadata['checks']),'negative_controls':len(timing['checks'])},'producer_checks':r['checks'],'independent_checks':base['checks'],'ownership_checks':io['checks'],'partial_accounting_checks':metadata['checks'],'metadata':metadata['metadata'],'receiver_records':metadata['receiver_records'],'server_published_partial_upload':metadata['server_published_partial_upload'],'control_checks':timing['checks'],'control_inputs':timing['inputs'],'upload':r['upload'],'protocol':base['protocol'],'boundary_diagnosis':diagnosis,'baseline_failure_receipt':str(baseline_path.relative_to(ROOT)),'baseline_failure_sha256':sha(baseline_path),'prior_peer_response_seconds':old_delay,'new_peer_response_seconds':new_delay,'peer_response_budget_seconds':response_budget,'linked_boundary_cases':37,
  'terminal_sha256':sha(out/'program/TERMINAL.EXE'),'ASPECT_sha256':sha(out/'program/ASPECT.EXE'),'observed_hold_ms':int(holds[0][0]),'exact_online_bytes':len(online),'exact_BBS_display_bytes':len(display),
  'payloads':base['payloads'],'serial_counters':io['counters'],'hardware_snapshot':base['hardware_snapshot'],'script_stages':r['script_stages'],
  'server_source_commit':server['source_commit'],'official_server_binary_sha256':server['binary_sha256'],'server_archives':server['archives'],
  'immutable_server_file_count':len(server['server_inputs']),'server_input_tree_sha256':tree_hash(server['server_inputs']),'loaded_library_sha256':server['server_libraries'],
  'statistics_before':r['statistics_before'],'statistics_after':r['statistics_after'],'prerequisite_inputs':prerequisites,'producer_inputs':r['frozen_inputs'],'runtime_inputs':r['runtime_inputs'],'buffered_runtime_proof':r.get('buffered_runtime_proof'),
  'capture_sha256':{n:sha(out/n) for n in names},'recorder_sha256':sha(Path(__file__)),
  'scope':'Actual source-built DOS/ASPECT Escape cancellation through stock Synchronet and real SIP/RTP/V22-1200 audio at38400DTE. Complete CRC/source frame and received ACK precede native CAN; exact partial-next-frame bytes, no EOF/full-source success, subsequent actual Files/Main and normal UART/IRQ/PIC/timer/SIP cleanup are independently audited. Source identity and existing files preserve. Maintained ordinary sender defers Escape through the current checksum/CRC; complete frames precede CAN. The measured stock peer response is within a conservative full-frame carrier-time budget and less than half the preserved66-second baseline. Linked37-case edge/fault/late-ACK checks pass. Responsive client cancellation is accepted only for this scoped audio workflow. Any retained/indexed partial keeps server cleanup and overall passed false; the original baseline is preserved. No retry, carrier-loss/reconnect, pressure, physical Boca/SPA2102 or F01-F16 completion.'}

 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':False,'client_workflow_passed':True,'eventual_client_recovery_verified':True,'responsive_cancellation_accepted':True,'actual_Synchronet_audio_accepted':False,'actual_client_cancellation_accepted':True,'server_partial_cleanup_accepted':cleanup,'check_counts':result['check_counts'],'online_bytes':len(online),'display_bytes':len(display),'receipt':str(target)}))

if __name__=='__main__':main()
