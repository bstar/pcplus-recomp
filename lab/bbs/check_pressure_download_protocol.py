#!/usr/bin/env python3
"""Reject damaged copies of the real >64KiB stock ENiGMA reference exchange."""
import argparse,hashlib,json,sys
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from audio_pressure_download import report
from prepare_audio_pressure_download import NAME,SIZE,validate
from modem import Telnet
from audit_zmodem import audit_batch,audit_controls,scan
from test_transfer_dos import timestamp
sys.path.insert(0,str(ROOT/'standalone'))
from check_zmodem_wire import header


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 reference=a.reference.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 ref=report(reference)
 if ref.get('server_fixture'):
  from enigma_fixture import from_result
  from_result(dict(server_fixture=ref['server_fixture'],server_root=ref['server_root'],route='download'))
 cohort=reference.parent;source,_=validate(ROOT/ref['fixture']);expected=source.read_bytes();assert len(expected)==SIZE>65536
 sent,_=Telnet().feed((cohort/'client-wire.bin').read_bytes());display,_=Telnet().feed((cohort/'server-wire.bin').read_bytes())
 events=json.loads((cohort/'events.json').read_text());decoders={d:Telnet() for d in ('in','out')};streams={d:bytearray() for d in decoders};trace=[]
 for event in events:
  d=event['direction'];body,_=decoders[d].feed(bytes.fromhex(event['hex']));offset=len(streams[d]);streams[d].extend(body)
  if body:trace.append(dict(direction='bbs' if d=='in' else 'dos',offset=offset,size=len(body),seconds=event['time']))
 assert bytes(streams['in'])==display and bytes(streams['out'])==sent
 post=next(e['time'] for e in events if e.get('label')=='post-search')
 def audit(data,opposite=sent,times=trace,payload=expected):
  r=audit_batch(data,{NAME:payload});r['controls']=audit_controls(r,opposite,times,'bbs',post)
  for f in r['files']:assert f.pop('source')==payload
  return r
 baseline=audit(display);assert baseline==ref['protocol'];cases=[]
 def reject(name,data=display,opposite=sent,times=trace,payload=expected,reason=None):
  try:audit(data,opposite,times,payload)
  except AssertionError as exc:
   detail=str(exc);assert reason is None or reason in detail,(name,detail)
   cases.append(dict(name=name,rejected=True,failure=detail,display_sha256=hashlib.sha256(data).hexdigest(),
    opposite_sha256=hashlib.sha256(opposite).hexdigest(),expected_source_sha256=hashlib.sha256(payload).hexdigest()))
  else:raise AssertionError(('Damaged evidence accepted',name))
 first=baseline['files'][0]['packets'][0];crc=first['crc_end']-1
 bad=bytearray(display);bad[crc]^=1;reject('corrupted_packet_CRC',bytes(bad),reason='Data CRC mismatch')
 altered=bytearray(expected);altered[65536]^=1
 reject('wrong_source_byte_above64KiB',payload=bytes(altered),reason='Transferred bytes differ')
 eof=next(e for e in baseline['events'] if e['kind']=='header' and e['type']==11)
 wrapped=header(bytes([11])+(SIZE&65535).to_bytes(4,'little'),eof['format'],0)
 reject('CRC_valid_EOF_position_wrapped_to16bits',display[:eof['offset']]+wrapped+display[eof['end']:],reason='Unverified/mismatched EOF')
 reject('exact_file_but_missing_finish',display[:eof['end']],reason='Incomplete files or missing ZFIN/OO')
 end=baseline['finish']['end'];assert display[end-2:end]==b'OO'
 reject('missing_literal_OO',display[:end-1]+b'X'+display[end:])
 finishing=[h for h in scan(sent) if h['type']==8];assert finishing
 changed=bytearray(sent)
 for h in reversed(finishing):
  replacement=header(bytes([3])+h['position'].to_bytes(4,'little'),h['format'],0)
  assert len(replacement)==h['end']-h['offset'];changed[h['offset']:h['end']]=replacement
 reject('CRC_valid_ACK_instead_of_receiver_ZFIN',opposite=bytes(changed),reason='Missing opposite header')
 for name,kind,position,before in [
  ('ACK_before_complete_packet_CRC',3,first['position'],timestamp(trace,'bbs',first['crc_end']-1)-1),
  ('receiver_ZFIN_before_sender_ZFIN',8,0,timestamp(trace,'bbs',baseline['finish']['offset'])-1),
  ('completion_ZRINIT_before_EOF',1,None,timestamp(trace,'bbs',eof['end']-1)-1)]:
  selected=[h for h in scan(sent) if h['type']==kind and (position is None or h['position']==position)];assert selected
  times=[dict(e) for e in trace];moved=0
  for event in times:
   if event['direction']=='dos' and any(event['offset']<h['end'] and h['offset']<event['offset']+event['size'] for h in selected):event['seconds']=before;moved+=1
  assert moved;reject(name,times=times)
 preserved=all(sha(cohort/n)==h for n,h in ref['captures_sha256'].items());assert preserved
 r=dict(passed=True,reference=str(reference.relative_to(ROOT)),reference_sha256=sha(reference),source_bytes=SIZE,source_sha256=sha(source),
  real_reference_baseline_protocol_exact=True,baseline_opposite_controls=len(baseline['controls']),cases=cases,original_reference_captures_unchanged=preserved,
  inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'lab/bbs/audio_pressure_download.py',ROOT/'lab/bbs/prepare_audio_pressure_download.py',ROOT/'lab/bbs/audit_zmodem.py',ROOT/'lab/bbs/modem.py',ROOT/'lab/bbs/test_transfer_dos.py',ROOT/'standalone/check_zmodem_wire.py')},
  captures_sha256=ref['captures_sha256'],
  server_fixture=ref.get('server_fixture'),
  scope='Verifier controls only using copied bytes/times from the real65797-byte lrzsz/'+('isolated sender-candidate' if ref.get('server_fixture') else 'stock')+' ENiGMA TCP reference. Baseline complete source/CRC/EOF/finish/opposite controls must reproduce exactly. Nine corruptions cover CRC, source content above64KiB, EOF position wrapped to16 bits with valid CRC, missing finish/OO/receiver-ZFIN and premature ACK/ZFIN/ZRINIT. No live DOS/audio product/pressure/hardware acceptance follows; original captures are preserved.')
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'passed':True,'rejected_cases':len(cases),'source_bytes':SIZE}))


if __name__=='__main__':main()
