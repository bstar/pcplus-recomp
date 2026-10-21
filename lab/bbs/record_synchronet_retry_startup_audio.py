#!/usr/bin/env python3
"""Seal a passing client retry without accepting stock partial-file cleanup."""
import argparse,json
from pathlib import Path
from audio_synchronet import ROOT,snapshot,message_bodies,sha
from audio_synchronet_retry_startup import AREA,payload,stored_files,names_for
from synthmodem_posttrain_validation import validate as validate_runtime
from modem import Telnet

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.cohort.resolve();target=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 read=lambda n:json.loads((out/n).read_text())
 r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json')
 NAME,RETRY=r['upload']['name'],r['retry']['name'];assert (NAME,RETRY) in {names_for(slot) for slot in range(1,10)}
 metadata=read('retry-metadata-audit.json');controls=read('retry-control-checks.json');observer=read('partial-observer.json')
 assert r['route']=='xmodem-cancel-retry' and r['peer']=='synchronet' and r['posttrain_hold'] and r['input_sequence_timeout_ms']==250
 for report in (r,base,metadata,controls):assert report['passed'] and all(report['checks'].values())
 assert io['evidence_consistent'] and all(io['checks'].values()) and not io['error_events']
 assert all(io['counters'][key]==0 for key in ('skippedBytes','pendingBytes','failedCallbackBytes'))
 assert observer['passed'] and observer['retry_metadata_at_observation'] is None
 def inputs(group):
  for name,h in group.items():
   p=Path(name);assert sha(p if p.is_absolute() else ROOT/p)==h,name
 def captures(group):
  for name,h in group.items():assert sha(out/name)==h,name
 for name in ('frozen_inputs','runtime_inputs','tool_inputs'):inputs(r[name])
 for name in ('generated_inputs','captures_sha256'):captures(r[name])
 inputs(base['audit_inputs'])
 for report in (metadata,controls,observer):inputs(report['inputs']);captures(report['captures_sha256'])
 inputs(metadata['source_authority'])
 captures(io['capture_sha256'])
 runtime=Path(next(iter(r['runtime_inputs'])))
 runtime=next(p for p in runtime.parents if (p/'source/config.js').is_file())
 if r.get('buffered_runtime_proof'):
  from synthmodem_buffered_runtime import validate as validate_buffered
  assert validate_buffered(runtime,ROOT/r['buffered_runtime_proof'])==r['runtime_inputs']
 else:assert validate_runtime(runtime)==r['runtime_inputs']
 assert snapshot()==r['server'] and message_bodies()==r['message_bodies']
 assert sha(out/'program/TERMINAL.EXE')==r['frozen_inputs']['build/terminal/TERMINAL.EXE']
 assert sha(out/'program/ASPECT.EXE')==r['frozen_inputs']['build/aspect-runner/ASPECT.EXE']
 proof=json.loads((ROOT/'build/terminal/terminal-upload-cancel-boundary.json').read_text())
 assert proof['passed'] and len(proof['cases'])==37 and proof['binary_sha256']==sha(out/'program/TERMINAL.EXE')
 startup=json.loads((ROOT/'build/terminal/terminal-upload-startup.json').read_text());assert startup['passed'] and len(startup['cases'])==43 and startup['binary_sha256']==sha(out/'program/TERMINAL.EXE')
 component_path=ROOT/r.get('startup_component_proof','docs/validation/terminal-upload-startup-fixed.json')
 component=json.loads(component_path.read_text());assert component['passed'] and component['actual_DOS_startup_accepted'] and component['binary_sha256']==sha(out/'program/TERMINAL.EXE')
 for group in ('product_inputs','checker_inputs','DOS_inputs','capture_sha256'):inputs(component[group])
 assert r['frozen_inputs'][str(component_path.relative_to(ROOT))]==sha(component_path)
 prerequisites={n:h for n,h in r['frozen_inputs'].items() if n.endswith('/result.json')};assert len(prerequisites)==4+bool(r.get('buffered_runtime_proof'))
 assert all(json.loads((ROOT/n).read_text())['passed'] for n in prerequisites)
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes());display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
 online=(out/'serial-in.bin').read_bytes();assert online.startswith(b'ATZ\rATD1\r');online=online[9:]
 offline_report=read('offline-caller.json')
 assert offline_report['checker_sha256']==r['frozen_inputs']['lab/bbs/diagnose_audio_caller.js']
 assert offline_report['capture_sha256']==sha(out/'rtp-from-caller.bin')
 assert offline_report['decoder_sha256']==sha(runtime/'source/src/dsp/protocols/V22Demodulator.js')
 offline=bytes.fromhex(''.join(c['hex'] for c in offline_report['received']));assert offline==online
 assert io['auditor_sha256']==r['frozen_inputs']['lab/bbs/audit_serial_io_evidence.py']
 assert base['auditor_sha256']==r['frozen_inputs']['lab/bbs/audit_synchronet_retry_startup_audio_dos.py']
 source=ROOT/r['upload']['source_path'];st=source.stat();assert source.read_bytes()==payload(NAME) and sha(source)==r['upload']['source_sha256']
 assert [st.st_ino,st.st_size,st.st_mtime_ns]==r['upload']['source_stat']
 partial=(AREA/NAME).read_bytes();retry=(AREA/RETRY).read_bytes();pst=(AREA/NAME).stat()
 assert partial==(out/'partial-observer/partial.bin').read_bytes()==(out/'receiver-partial.bin').read_bytes()
 assert [pst.st_ino,pst.st_size,pst.st_mtime_ns]==observer['partial_stat'] and metadata['partial_metadata']==observer['partial_metadata']
 assert len(partial)==base['protocol']['canceled_source_bytes']<len(payload(NAME)) and payload(NAME).startswith(partial)
 assert retry==(out/'receiver-retry.bin').read_bytes()==payload(NAME)+b'\x1a'*127
 files=stored_files();before=r['upload']['existing_files_before'];assert set(files)==set(before)|{NAME,RETRY}
 assert all(files[n]==h for n,h in before.items())
 cleanup=not (AREA/NAME).exists();assert not cleanup and cleanup==r['server_partial_cleanup_accepted']==base['server_partial_cleanup_accepted']==metadata['server_partial_cleanup_accepted']
 previous=ROOT/'docs/validation/synthmodem-synchronet-retry-audio-01.json';failure=json.loads(previous.read_text());assert not failure['actual_same_call_retry_accepted']
 for n,h in failure['captures_sha256'].items():assert sha(ROOT/failure['cohort']/n)==h,n
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json','offline-caller.json','server-inputs.json','SEND/RETRY.BIN','partial-observer.json','receiver-partial.bin','receiver-retry.bin','retry-metadata-audit.json','retry-control-checks.json',*observer['captures_sha256'],*metadata['captures_sha256']]))
 result=dict(passed=False,client_workflow_passed=True,actual_same_call_retry_accepted=True,actual_audio_startup_accepted=True,server_partial_cleanup_accepted=False,
  cohort=str(out.relative_to(ROOT)),route='login/CRC-ACK/native-Escape/CAN/Files/same-source-CRC-retry/EOT-NAK-ACK/Files/Main',
  check_counts=dict(producer=len(r['checks']),independent=len(base['checks']),ownership=len(io['checks']),official_metadata=len(metadata['checks']),control_counterexamples=len(controls['checks'])),
  producer_checks=r['checks'],independent_checks=base['checks'],ownership_checks=io['checks'],metadata_checks=metadata['checks'],control_checks=controls['checks'],
  partial_metadata=metadata['partial_metadata'],retry_metadata=metadata['retry_metadata'],receiver_records=metadata['receiver_records'],startup_requests=metadata['startup_requests'],data_block_errors=metadata['data_block_errors'],
  terminal_sha256=sha(out/'program/TERMINAL.EXE'),ASPECT_sha256=sha(out/'program/ASPECT.EXE'),exact_online_bytes=len(online),exact_BBS_display_bytes=len(display),
  protocol=base['protocol'],payloads=base['payloads'],hardware_snapshot=base['hardware_snapshot'],serial_counters=io['counters'],
  upload=r['upload'],retry=r['retry'],partial_observation_sha256=sha(out/'partial-observer.json'),linked_boundary_cases=37,linked_startup_cases=43,component_startup_receipt=str(component_path.relative_to(ROOT)),buffered_runtime_proof=r.get('buffered_runtime_proof'),
  failed_prior_receipt=str(previous.relative_to(ROOT)),failed_prior_receipt_sha256=sha(previous),
  server_source_commit=r['server']['source_commit'],official_server_binary_sha256=r['server']['binary_sha256'],server_archives=r['server']['archives'],
  producer_inputs=r['frozen_inputs'],runtime_inputs=r['runtime_inputs'],audit_inputs=base['audit_inputs'],metadata_inputs=metadata['inputs'],control_inputs=controls['inputs'],
  capture_sha256={n:sha(out/n) for n in names},recorder_sha256=sha(Path(__file__)),
  scope='Actual source-built DOS ordinary XMODEM same-source full retry after native Escape/CAN on one stock Synchronet SIP/RTP/V22-1200 audio connection at38400DTE. Original early-start BIOS sequence sends the second Alt-S three ticks after n; no complete-banner wait is added. The identified maintained startup adapter filters banner text and ANSI state before handing a settled control to the unchanged recovered sender. Full native data/control finish, exact frontend/guest/Telnet/offline-audio bytes, Files/Main, preserved local source and original partial, official metadata and cleanup are mandatory. Stock indexed partial remains, so overall passed and server cleanup remain false. This accepts only the captured early-start audio workflow and does not establish tolerance of arbitrarily paused plaintext handshake letters, carrier-loss/reconnect, pressure, physical Boca/SPA2102 or F01-F16 completion.')
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=False,client_workflow_passed=True,actual_same_call_retry_accepted=True,actual_audio_startup_accepted=True,server_partial_cleanup_accepted=False,check_counts=result['check_counts'],receipt=str(target))))

if __name__=='__main__':main()
