#!/usr/bin/env python3
"""Compare retained ZMODEM retries at bridge entry and decoded frontend output."""
import argparse,bisect,hashlib,json
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from modem import Telnet
from audit_audio_download import frontend_trace
from audit_zmodem import audit_batch,scan


def table(rows,direction):
 rows=sorted((r for r in rows if r['direction']==direction),key=lambda r:r['offset']);at=0
 for r in rows:assert r['offset']==at and r['size']>0;at+=r['size']
 return [r['offset'] for r in rows],rows


def stamp(index,offset):
 starts,rows=index;at=bisect.bisect_right(starts,offset)-1;assert at>=0
 r=rows[at];assert r['offset']<=offset<r['offset']+r['size'];return r['seconds']


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 receipt=a.receipt.resolve();out=a.output.resolve();assert receipt.is_relative_to(ROOT/'docs/validation') and out.is_relative_to(ROOT/'build') and not out.exists()
 accepted=json.loads(receipt.read_text());assert accepted['passed'] and accepted['actual_ENiGMA_download_accepted']
 cohort=ROOT/accepted['cohort'];hashes=accepted['captures_sha256']
 for n,h in hashes.items():assert sha(cohort/n)==h,n
 run=json.loads((cohort/'result.json').read_text());base=json.loads((cohort/'independent-audit.json').read_text())
 raw={'to_bbs':(cohort/'bbs-input.bin').read_bytes(),'from_bbs':(cohort/'bbs-output.bin').read_bytes()}
 sent,_=Telnet().feed(raw['to_bbs']);display,_=Telnet().feed(raw['from_bbs'])
 expected=Path(run['download']['expected_path']).read_bytes();assert hashlib.sha256(expected).hexdigest()==accepted['source_sha256']
 protocol=audit_batch(display,{'PCXTEST.BIN':expected})
 # audit_batch retains source bytes for callers; the published passive audit
 # removes only that binary field before JSON serialization.
 for file in protocol['files']:assert file.pop('source')==expected
 assert protocol['events']==accepted['protocol']['events'] and protocol['files']==accepted['protocol']['files']
 front,provenance=frontend_trace(cohort,sent,display,base['payloads']['expected_bridge_bytes']);anchor=provenance['clock_anchor']
 origin=int(anchor['monotonicNs'])/1e9-anchor['seconds']
 decoders={d:Telnet() for d in raw};streams={d:bytearray() for d in raw};ends={d:0 for d in raw};relay=[]
 for line in (cohort/'BBS-relay-events.jsonl').read_text().splitlines():
  e=json.loads(line);d=e['direction'];assert e['offset']==ends[d];end=e['offset']+e['count'];assert end<=len(raw[d])
  body,_=decoders[d].feed(raw[d][e['offset']:end]);ends[d]=end;offset=len(streams[d]);streams[d].extend(body)
  if body:relay.append(dict(direction='bbs' if d=='from_bbs' else 'dos',offset=offset,size=len(body),seconds=int(e['monotonic_ns'])/1e9-origin))
 assert all(ends[d]==len(raw[d]) for d in raw) and bytes(streams['to_bbs'])==sent and bytes(streams['from_bbs'])==display
 before=table(relay,'bbs');after=table(front,'bbs');up=table(front,'dos')
 eof=next(e for e in protocol['events'] if e['kind']=='header' and e['type']==11);eof_entry=stamp(before,eof['end']-1);eof_front=stamp(after,eof['end']-1)
 replay=[p for f in protocol['files'] for p in f['packets'] if p['after_eof']]
 rows=[dict(bytes=p['length'],position=p['position'],packet_sha256=p['sha256'],bridge_entry_first_seconds=stamp(before,p['offset']),bridge_entry_last_seconds=stamp(before,p['end']-1),decoded_frontend_first_seconds=stamp(after,p['offset']),decoded_frontend_last_seconds=stamp(after,p['end']-1)) for p in replay]
 positions=[dict(type=h['type'],position=h['position'],seconds=stamp(up,h['end']-1)) for h in scan(sent) if h['type']==9]
 cadence=[b['bridge_entry_first_seconds']-a['bridge_entry_first_seconds'] for a,b in zip(rows,rows[1:])]
 checks=dict(original_CRC_source_protocol_reproduced=True,exact_full_relay_and_frontend_manifests=True,
  eight_source_verified_replays=len(rows)==8 and all(p['replayed'] for p in replay),replayed_payload_bytes_match_receipt=sum(p['length'] for p in replay)==accepted['verified_post_EOF_retransmitted_bytes']==8320,
  every_replay_enters_before_first_EOF_decoded=all(r['bridge_entry_last_seconds']<eof_front for r in rows),
  every_replay_decoded_after_first_EOF=all(r['decoded_frontend_first_seconds']>eof_front for r in rows),
  only_initial_zero_position_request=len(positions)==1 and positions[0]['position']==0,
  original_captures_preserved=all(sha(cohort/n)==h for n,h in hashes.items()))
 result=dict(passed=all(checks.values()),checks=checks,accepted_receipt=str(receipt.relative_to(ROOT)),accepted_receipt_sha256=sha(receipt),cohort=accepted['cohort'],
  first_EOF_bridge_entry_seconds=eof_entry,first_EOF_decoded_frontend_seconds=eof_front,first_EOF_queue_seconds=eof_front-eof_entry,
  replay_packets=rows,replay_payload_bytes=sum(p['length'] for p in replay),replay_entry_intervals_seconds=cadence,opposite_ZRPOS=positions,clock_provenance=provenance,
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audit_audio_download.py',ROOT/'lab/bbs/audit_zmodem.py',ROOT/'lab/bbs/modem.py']},
  captures_sha256={n:sha(cohort/n) for n in ('result.json','independent-audit.json','bbs-input.bin','bbs-output.bin','BBS-relay-events.jsonl','serial-input-events.jsonl','serial-write-events.jsonl','serial-in.bin','serial-out.bin','caller-decoded.bin','node-result.json')},
  scope='Read-only timing diagnosis of the previously accepted source/CRC-verified download. Absolute host monotonic bridge observations are aligned to the frontend clock. All eight replay packets enter the bridge before the first EOF is decoded at the frontend; their roughly11-second entry cadence and90-second EOF backlog are observations. No DOS application-consumption timestamps, exclusive timeout cause, correction, new BBS/audio run or physical hardware claim. Next compare bounded receive credit/acknowledgment timing on the same slow audio path while preserving full integrity/finish/storage/cleanup gates.')
 with out.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':result['passed'],'checks':checks,'EOF_queue_seconds':eof_front-eof_entry,'replay_entry_intervals_seconds':cadence}));assert result['passed']


if __name__=='__main__':main()
