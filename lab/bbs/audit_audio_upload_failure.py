#!/usr/bin/env python3
"""Record upload01's failed audio run without weakening transfer acceptance."""
import hashlib,json,re,struct
from pathlib import Path
from modem import Telnet
from audio_upload import metadata

ROOT=Path(__file__).resolve().parents[2]


def main():
 out=ROOT/'build/bbs-lab/synthmodem-audio-upload-01'
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 load=lambda n:json.loads((out/n).read_text())
 r=load('result.json');base=load('independent-audit.json')
 io=load('serial-io-audit.json');upload=load('upload-audit.json')
 assert r['route']=='upload' and not r['passed'] and not base['passed'] and not upload['passed'] and io['evidence_consistent']
 assert all(sha(out/n)==v for n,v in r['captures_sha256'].items())
 serial=(out/'serial-in.bin').read_bytes();prefix=b'ATZ\rATD1\r'
 assert serial.startswith(prefix);native=serial[len(prefix):]
 target=native.split(b'\r',1)[0]+b'\r'
 # The call addresses the owned relay's ephemeral port, not the BBS port.
 assert re.fullmatch(rb'127\.0\.0\.1:\d+\r',target)
 wire=(out/'control-wire.bin').read_bytes();guest=bytearray();at=0
 while at<len(wire):
  size,kind=struct.unpack_from('<HB',wire,at)
  assert 1<=size<=4094 and at+size+2<=len(wire)
  if kind==0x15:guest.extend(wire[at+3:at+size+2])
  at+=size+2
 assert base['payloads']['pre_proxy_training_tail_bytes']==0
 caller=bytes.fromhex(''.join(v['hex'] for v in load('offline-caller.json')['received']))
 sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes())
 streams={'offline_caller':caller,'guest_DATA_RX':bytes(guest),'target_plus_BBS_application_input':target+sent}
 prefixes={k:{'bytes':len(v),'exact_native_prefix':native.startswith(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in streams.items()}
 assert all(v['exact_native_prefix'] for v in prefixes.values())
 assert len(native)==21775 and [len(caller),len(guest),len(target+sent)]==[6085,6082,6080]
 source=out/'SEND/AUDIOUP.BIN';expected=source.read_bytes();assert len(expected)==11521
 assert sha(source)==r['upload']['prepared']['source_sha256']
 assert [source.stat().st_ino,source.stat().st_size,source.stat().st_mtime_ns]==r['upload']['prepared']['source_stat']
 entries=metadata();assert entries==[]
 assert not Path(r['upload']['prepared']['target_path']).exists()
 rows=[json.loads(v) for v in (out/'server-retirement.jsonl').read_text().splitlines()]
 exits=[v for v in rows if v.get('msg')=='Process exited']
 assert len(exits)==1 and exits[0]['exitCode']==255 and exits[0]['signal']==0
 execution=next(v for v in rows if v.get('msg')=='Executing external protocol')
 partial=Path(execution['tempDir'])/'AUDIOUP.BIN';body=partial.read_bytes()
 assert body==expected[:1024]
 backup=out/'receiver-partial-AUDIOUP.BIN'
 if backup.exists():assert backup.read_bytes()==body
 else:
  with backup.open('xb') as f:f.write(body)
 regression=json.loads((ROOT/'build/terminal/zmodem-upload-response-counterexample.json').read_text())
 assert regression['counterexample_reproduced'] and regression['binary_sha256']==r['frozen_inputs']['build/terminal/TERMINAL.EXE']
 receipt={'passed':False,'cohort':out.name,
  'diagnosis':'Native fixed-DTE sender replays before a valid slow-link ACK. Queued upstream bytes remain at client termination; observed exact prefixes do not demonstrate line corruption.',
  'producer_checks':r['checks'],'byte_cleanup_checks':base['checks'],
  'frontend_ownership_checks':io['checks'],'upload_checks':upload['checks'],
  'source_bytes':len(expected),'source_sha256':sha(source),'native_online_bytes':len(native),
  'upstream_prefix_diagnosis':prefixes,'response_timing':load('response-timing.json'),
  'official_metadata_after_retirement':entries,'official_target_absent':True,
  'receiver_retirement':{k:exits[0][k] for k in ('sessionId','time','exitCode','signal')},
  'receiver_partial':{'bytes':len(body),'exact_source_prefix':True,'sha256':sha(backup),'preserved_as':str(backup.relative_to(ROOT))},
  'linked_regression_receipt':'docs/validation/zmodem-upload-response-counterexample.json',
  'frozen_inputs':r['frozen_inputs'],'runtime_inputs':r['runtime_inputs'],
  'server_inputs':r['server_inputs'],'generated_inputs':r['generated_inputs'],
  'capture_sha256':{n:sha(out/n) for n in ['result.json','independent-audit.json','serial-io-audit.json','upload-audit.json','response-timing.json','server-retirement.jsonl','offline-caller.json','receiver-partial-AUDIOUP.BIN',*r['captures_sha256']]},
  'auditor_sha256':sha(Path(__file__)),
  'scope':'First actual DOS/ENiGMA V22/1200 software-modem upload fails. Original capture hashes verified; source data/stat and native cleanup survive. No installed file, CRC/finish acceptance or resumed search. Late receiver error and partial are separately preserved evidence. Linked modeled delayed ACK reproduces premature output. No physical or full-application acceptance.'}
 (ROOT/'docs/validation/synthmodem-audio-upload-01.json').write_text(json.dumps(receipt,indent=2)+'\n')
 (ROOT/'docs/validation/zmodem-upload-response-counterexample.json').write_text(json.dumps(regression,indent=2)+'\n')
 print(json.dumps({'recorded_failed_cohort':out.name,'upstream_prefixes':prefixes,'receiver_exit':255,'receiver_partial_bytes':len(body)},indent=2))


if __name__=='__main__':main()
