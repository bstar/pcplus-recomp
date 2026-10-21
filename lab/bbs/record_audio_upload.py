#!/usr/bin/env python3
"""Seal the complete upload02 result, including its unwaived receiver-tail gap."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def main():
 out=ROOT/'build/bbs-lab/synthmodem-audio-upload-02'
 read=lambda n:json.loads((out/n).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json')
 transfer=read('upload-audit.json');finish=read('upload-finish-diagnosis.json');verifier=read('control-timing-verifier.json')
 assert r['passed'] and base['passed'] and io['evidence_consistent']
 failed={n for n,v in transfer['checks'].items() if not v}
 assert not transfer['passed'] and failed=={'no_protocol_tail_after_helper_exit'}
 assert verifier['passed'] and verifier['protocol_only'] and not verifier['input_transfer_audit_passed']
 assert verifier['checker_sha256']==sha(ROOT/'lab/bbs/check_audio_control_timing.py')
 assert len(verifier['negative_cases'])==2 and all(v['rejected'] for v in verifier['negative_cases'])
 for report in (r,transfer,finish):
  captured=report.get('captures_sha256',report.get('capture_sha256'))
  assert captured and all(sha(out/n)==value for n,value in captured.items())
 for group in ('frozen_inputs','runtime_inputs'):
  for name,value in r[group].items():
   path=Path(name);path=path if path.is_absolute() else ROOT/path
   assert sha(path)==value,name
 serial=(out/'serial-in.bin').read_bytes();commands=b'ATZ\rATD1\r'
 assert serial.startswith(commands);online=serial[len(commands):]
 offline=bytes.fromhex(''.join(v['hex'] for v in read('offline-caller.json')['received']))
 assert online==offline and len(online)==12330
 before=r['upload']['prepared'];source=out/'SEND/AUDIOUP.BIN';target=Path(before['target_path'])
 assert source.read_bytes()==target.read_bytes() and sha(source)==before['source_sha256']
 assert [source.stat().st_ino,source.stat().st_size,source.stat().st_mtime_ns]==before['source_stat']
 peer_path=ROOT/'build/bbs-lab/sexyz-receive-finish-01/checks.json'
 peer=json.loads(peer_path.read_text());assert peer['evidence_consistent'] and peer['stock_counterexample_reproduced']
 assert peer['checker_sha256']==sha(ROOT/'lab/bbs/check_sexyz_receive_finish.py')
 assert [v['receiver_exited_while_OO_withheld'] for v in peer['cases']]==[True,False]
 assert all(v['file_sha256']==sha(source) and v['receiver_exit']==0 for v in peer['cases'])
 assert finish['receiver_ZFIN_last_byte_after_helper_exit_ms']>250
 assert finish['sender_OO_relay_after_helper_exit_ms'][0]>300
 assert not finish['late_header_controls'] and not transfer['errors']
 protocol=transfer['protocol'];assert len(protocol['files'])==1
 packets=protocol['files'][0]['packets'];assert len(packets)==12 and not any(v['replayed'] for v in packets)
 counts={'producer':len(r['checks']),'independent':len(base['checks']),
  'ownership':len(io['checks']),'protocol_file_resume':len(transfer['checks'])}
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json',
  'upload-audit.json','upload-finish-diagnosis.json','control-timing-verifier.json','offline-caller.json']))
 result={'passed':False,'cohort':str(out.relative_to(ROOT)),
  'status':'Complete exact upload and resumed BBS search; receiver retires before required OO. Full workflow acceptance remains false.',
  'checks':{'producer':True,'independent_byte_cleanup':True,'serial_ownership':True,
   'protocol_file_and_resume':False,'timing_verifier_negatives':True,
   'offline_caller_equals_complete_online_input':True,'no_late_protocol_tail':False},
  'check_counts':counts,'producer_checks':r['checks'],'independent_checks':base['checks'],
  'ownership_checks':io['checks'],'transfer_checks':transfer['checks'],
  'terminal_sha256':r['frozen_inputs']['build/terminal/TERMINAL.EXE'],
  'map_sha256':r['frozen_inputs']['build/terminal/terminal.map'],
  'producer_inputs':r['frozen_inputs'],'runtime_inputs':r['runtime_inputs'],
  'server_revision':r['server_revision'],'server_inputs':r['server_inputs'],
  'payloads':base['payloads'],'source_file_bytes':len(source.read_bytes()),
  'source_and_installed_file_sha256':sha(source),'official_metadata':transfer['official_metadata'],
  'protocol':protocol,'control_timing':transfer['control_timing'],'timing_verifier':verifier,
  'finish_diagnosis':finish,'stock_receiver_counterexample':peer,
  'serial_counters':io['counters'],'hardware_snapshot':base['hardware_snapshot'],
  'post_transfer_keyboard_hex':finish['post_protocol_keyboard_hex'],
  'gateway_errors':r['gateway']['errors'],
  'capture_sha256':{n:sha(out/n) for n in names},
  'external_evidence_sha256':{str(peer_path.relative_to(ROOT)):sha(peer_path)},
  'recorder_sha256':sha(Path(__file__)),
  'scope':'One full-size DOS upload through unchanged stock ENiGMA/SEXYZ3.6 and V22/1200 framed SIP/RTP/DSP runtime at fixed38400 DTE. All25 producer,26 independent byte/cleanup,12 ownership and18 of19 transfer gates pass; required late-tail gate fails. Exact12 packets, opposite controls, FIN/OO, installed official file, source/stat preservation, post-form search/list and normal hardware/timer cleanup are verified. Stock receiver exits before the final reply reaches DOS; reference receiver retains ownership until OO in a separate subprocess counterexample. No missing gate is waived, no peer/runtime/product changed, and no physical, arbitrary peer or F01-F16 completion is claimed.'}
 target=ROOT/'docs/validation/synthmodem-audio-upload-02.json';assert not target.exists()
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':False,'positive_checks':sum(sum(v.values()) for v in (r['checks'],base['checks'],io['checks'],transfer['checks'])),'total_checks':sum(counts.values()),'failed_gate':sorted(failed),'receipt':str(target)}))


if __name__=='__main__':main()
