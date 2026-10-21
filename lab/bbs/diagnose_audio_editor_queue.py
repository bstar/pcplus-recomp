#!/usr/bin/env python3
"""Split accepted editor transport latency at the owned BBS relay boundary."""
import argparse,json,re
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from modem import Telnet
from audit_audio_download import frontend_trace
from diagnose_audio_download_queue import table,stamp
from diagnose_audio_editor_latency import visible,keys


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--latency-receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 receipt=a.latency_receipt.resolve();out=a.output.resolve()
 assert receipt.is_relative_to(ROOT/'docs/validation') and out.is_relative_to(ROOT/'build') and not out.exists()
 latency=json.loads(receipt.read_text());assert latency['passed'] and all(latency['checks'].values())
 accepted_path=ROOT/latency['accepted_receipt'];assert sha(accepted_path)==latency['accepted_receipt_sha256']
 accepted=json.loads(accepted_path.read_text());assert accepted['passed'] and accepted['actual_ENiGMA_editor_burst_accepted']
 for n,h in latency['inputs'].items():assert sha(ROOT/n)==h,n
 cohort=ROOT/latency['cohort'];assert latency['cohort']==accepted['cohort']
 for group in (accepted['captures_sha256'],latency['captures_sha256']):
  for n,h in group.items():assert sha(cohort/n)==h,n
 base=json.loads((cohort/'independent-audit.json').read_text());assert base['passed'] and all(base['checks'].values())
 raw={d:(cohort/n).read_bytes() for d,n in [('to_bbs','bbs-input.bin'),('from_bbs','bbs-output.bin')]}
 sent,_=Telnet().feed(raw['to_bbs']);display,_=Telnet().feed(raw['from_bbs'])
 front,provenance=frontend_trace(cohort,sent,display,base['payloads']['expected_bridge_bytes'])
 anchor=provenance['clock_anchor'];origin=int(anchor['monotonicNs'])/1e9-anchor['seconds']
 decoders={d:Telnet() for d in raw};streams={d:bytearray() for d in raw};ends={d:0 for d in raw};relay=[]
 for line in (cohort/'BBS-relay-events.jsonl').read_text().splitlines():
  e=json.loads(line);d=e['direction'];assert e['offset']==ends[d];end=e['offset']+e['count'];assert end<=len(raw[d])
  body,_=decoders[d].feed(raw[d][e['offset']:end]);ends[d]=end;offset=len(streams[d]);streams[d].extend(body)
  if body:relay.append(dict(direction='dos' if d=='to_bbs' else 'bbs',offset=offset,size=len(body),seconds=int(e['monotonic_ns'])/1e9-origin))
 assert all(ends[d]==len(raw[d]) for d in raw) and bytes(streams['to_bbs'])==sent and bytes(streams['from_bbs'])==display
 indices={(boundary,d):table(trace,d) for boundary,trace in [('frontend',front),('relay',relay)] for d in ('dos','bbs')}
 body=bytes.fromhex(base['editor']['expected_body_hex']);start=sent.index(body);assert sent.count(body)==1
 clean,offsets=visible(display);subject=clean.index(b'KEYTEST')
 matches=list(re.finditer(rb'(INS|OVR) (\d{2}),(\d{2})',clean[subject:]));key_ends=keys(body)
 assert len(matches)==len(key_ends)==len(latency['rows'])==25
 assert [[m[1].decode(),int(m[2]),int(m[3])] for m in matches]==base['editor']['positions']
 rows=[]
 for i,(end,match,prior) in enumerate(zip(key_ends,matches,latency['rows'])):
  off=offsets[subject+match.end()-1];kf=stamp(indices['frontend','dos'],start+end);kr=stamp(indices['relay','dos'],start+end)
  fr=stamp(indices['relay','bbs'],off);ff=stamp(indices['frontend','bbs'],off)
  assert kf==prior['key_last_byte_frontend_seconds'] and ff==prior['footer_last_byte_frontend_seconds']
  rows.append(dict(key=i+1,key_frontend_seconds=kf,key_relay_seconds=kr,footer_relay_seconds=fr,footer_frontend_seconds=ff,
   outbound_seconds=kr-kf,server_roundtrip_seconds=fr-kr,return_path_seconds=ff-fr,total_seconds=ff-kf))
 phases=('outbound_seconds','server_roundtrip_seconds','return_path_seconds','total_seconds')
 checks=dict(prior_latency_and_capture_hashes_exact=True,complete_frontend_and_relay_manifests=True,
  all25_keys_and_verified_footers_correspond=True,prior_frontend_measurements_reproduced=True,
  every_observed_phase_nonnegative=all(r[k]>=0 for r in rows for k in phases),
  phase_sum_matches_total=all(abs(r['total_seconds']-sum(r[k] for k in phases[:3]))<1e-9 for r in rows),
  original_captures_preserved=all(sha(cohort/n)==h for n,h in accepted['captures_sha256'].items()))
 result=dict(passed=all(checks.values()),checks=checks,latency_receipt=str(receipt.relative_to(ROOT)),latency_receipt_sha256=sha(receipt),
  accepted_receipt=latency['accepted_receipt'],accepted_receipt_sha256=sha(accepted_path),cohort=latency['cohort'],rows=rows,
  phase_ranges={k:dict(minimum=min(r[k] for r in rows),maximum=max(r[k] for r in rows)) for k in phases},clock_provenance=provenance,
  inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'lab/bbs/diagnose_audio_editor_latency.py',ROOT/'lab/bbs/diagnose_audio_download_queue.py',ROOT/'lab/bbs/audit_audio_download.py',ROOT/'lab/bbs/modem.py')},
  captures_sha256={**latency['captures_sha256'],'BBS-relay-events.jsonl':sha(cohort/'BBS-relay-events.jsonl')},
  scope='Read-only decomposition of the accepted25-key V22/1200 burst capture using exact complete streams and aligned host monotonic observations. Outbound is frontend input read to relay input read; server roundtrip includes relay forwarding, stock server processing and response socket observation; return path includes all downstream queuing, modulation, demodulation and frontend submission. No instrumentation of server internals or DOS application paint, no exclusive component cause, no performance correction/new audio run/physical14.4-kbps acceptance. Next compare supported negotiated line rates and controlled output pressure with an explicit response budget while preserving byte/cursor/cleanup gates.')
 with out.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':result['passed'],'phase_ranges':result['phase_ranges']}));assert result['passed']


if __name__=='__main__':main()
