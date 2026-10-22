#!/usr/bin/env python3
"""Replay retained stock-sender audio bytes through a verified cached C receiver.

This is a timing-free counterexample, not a fresh DOS/audio/BBS acceptance test.
Transport and checked storage are host fixtures; captured peer bytes are fixed.
"""
import argparse, ctypes as C, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from check_zmodem import Fixture,P,U
from audit_zmodem import scan,packet,metadata

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

class Replay(Fixture):
 def abort(self,context):
  self.aborted=bytes(self.stage or b'')
  return super().abort(context)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--cohort',type=Path,required=True)
 p.add_argument('--library-proof',type=Path,required=True)
 p.add_argument('--campaign-library-proof',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 cohort=a.cohort.resolve();proof=a.library_proof.resolve();output=a.output.resolve();oldproof=a.campaign_library_proof.resolve()
 assert all(q.is_relative_to(ROOT/'build') for q in (cohort,proof,oldproof,output)) and not output.exists()
 producer=json.loads((cohort/'result.json').read_text());receipt=json.loads(proof.read_text())
 assert not producer['passed'] and receipt['passed']
 library=proof.parent/'session.so';assert sha(library)==receipt['library_sha256']
 oldreceipt=json.loads(oldproof.read_text());oldlibrary=oldproof.parent/'session.so'
 assert oldreceipt['passed'] and sha(oldlibrary)==oldreceipt['library_sha256']
 dependencies=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c','zmodem.h','zmodem_wire.h','zmodem_name.h','batch_header.h')]
 dependencies += [ROOT/'standalone/check_zmodem.py',ROOT/'standalone/check_zmodem_wire.py']
 for source in dependencies:
  name=str(source.relative_to(ROOT));assert sha(source)==receipt['inputs'][name],name
  if name in ('src/transfer/zmodem.c','src/transfer/zmodem_wire.c','src/transfer/zmodem.h','src/transfer/zmodem_wire.h'):
   assert producer['frozen_inputs'][name]==oldreceipt['inputs'][name],name
  elif name.startswith('src/'):
   assert oldreceipt['inputs'][name]==receipt['inputs'][name],name
 captures=['caller-decoded.bin','serial-in.bin','serial-out.bin']
 for name in captures:assert sha(cohort/name)==producer['captures_sha256'][name],name
 wire=(cohort/'caller-decoded.bin').read_bytes();candidates=[]
 for header in scan(wire):
  if header['type']!=4:continue
  try:frame=packet(wire,header['end'],header['format']);identity=metadata(frame['payload'])
  except (AssertionError,ValueError):continue
  if identity==('PCPRESS.BIN',65797):candidates.append(header)
 assert len(candidates)==1
 start=candidates[0]['offset'];lib=C.CDLL(str(library));lib.zm_run.argtypes=[P,P,P,U]
 f=Replay(lib,wire[start:]);status=f.run()
 oldlib=C.CDLL(str(oldlibrary));oldlib.zm_run.argtypes=[P,P,P,U]
 previous=Replay(oldlib,wire[start:]);oldstatus=previous.run()
 source=bytes((i*73+(i>>8)*19+37)&255 for i in range(65797))
 assert hashlib.sha256(source).hexdigest()==producer['download']['expected_sha256']
 checks=dict(cached_libraries_verified_and_campaign_core_codec_inputs_match=True,
  current_and_campaign_core_same_failure_and_response=status==oldstatus and f.tx==previous.tx and f.events==previous.events and f.aborted==previous.aborted,
  retained_capture_hashes_exact=True,unique_expected_ZFILE=True,
  protocol_failure_reproduced=status==6,
  verified_extent_15360=f.session.position==15360,
  staged_prefix_exact=f.aborted==source[:15360],
  exact_original_packet_write_lengths=[e[1] for e in f.events if e[0]=='append']==[1024,2048,4096,8192],
  no_commit_or_installed_file=not f.received and not any(e[0]=='commit' for e in f.events),
  single_checked_abort=sum(e[0]=='abort' for e in f.events)==1,
  callback_errors_absent=not f.errors)
 headers=[dict(type=h['type'],position=h['position']) for h in scan(bytes(f.tx))]
 recovery=[h for h in headers if h['type']==9 and h['position']==15360]
 checks['nine_recovery_requests_at_verified_position']=len(recovery)==9
 assert all(checks.values()),checks
 dependencies += [Path(__file__).resolve(),ROOT/'lab/bbs/audit_zmodem.py']
 result=dict(passed=True,counterexample_reproduced=True,transfer_accepted=False,checks=checks,
  cohort=str(cohort.relative_to(ROOT)),producer_sha256=sha(cohort/'result.json'),
  library_proof=str(proof.relative_to(ROOT)),library_proof_sha256=sha(proof),library_sha256=sha(library),
  campaign_library_proof=str(oldproof.relative_to(ROOT)),campaign_library_proof_sha256=sha(oldproof),campaign_library_sha256=sha(oldlibrary),
  source_bytes=len(source),source_sha256=hashlib.sha256(source).hexdigest(),
  normalized_input_offset=start,replayed_bytes=len(wire)-start-len(f.rx),unread_bytes=len(f.rx),
  status=status,verified_position=f.session.position,retries=f.session.retries,events=f.events,
  response_headers=headers,response_sha256=hashlib.sha256(f.tx).hexdigest(),
  staged_prefix_sha256=hashlib.sha256(f.aborted).hexdigest(),
  capture_sha256={name:sha(cohort/name) for name in captures},
  inputs={str(q.relative_to(ROOT)):sha(q) for q in dependencies},scope=__doc__,
  limitations=['No elapsed-time model or new peer response; this does not reproduce sender scheduling.',
   'Campaign freezes core/codec C and headers, not name/metadata sources; the latter match both cached library manifests and current files.',
   'Core failure with identical byte input does not prove complete DOS/UI failure causality.',
   'No recovery fix, unmodified-server compatibility or physical hardware acceptance.'])
 output.parent.mkdir(parents=True,exist_ok=True)
 with output.open('x') as out:out.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,counterexample_reproduced=True,status=status,verified_position=f.session.position,checks=len(checks))))

if __name__=='__main__':main()
