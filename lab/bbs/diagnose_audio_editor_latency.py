#!/usr/bin/env python3
"""Measure key-to-footer transport latency in an accepted ENiGMA burst capture."""
import argparse,json,re
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from modem import Telnet
from audit_audio_download import frontend_trace
from diagnose_audio_download_queue import table,stamp


def visible(data):
 """Remove CSI sequences while retaining each visible byte's wire offset."""
 text=bytearray();offsets=[];at=0
 for match in re.finditer(rb'\x1b\[[0-?]*[ -/]*[@-~]',data):
  text.extend(data[at:match.start()]);offsets.extend(range(at,match.start()));at=match.end()
 text.extend(data[at:]);offsets.extend(range(at,len(data)))
 assert len(text)==len(offsets)
 return bytes(text),offsets


def keys(data):
 """Treat each complete ANSI key sequence as one BIOS key's serial output."""
 ends=[];at=0
 while at<len(data):
  if data[at]==27:
   match=re.match(rb'\x1b\[[0-?]*[ -/]*[@-~]',data[at:]);assert match,'Incomplete key sequence'
   at+=match.end()
  else:at+=1
  ends.append(at-1)
 return ends


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 receipt=a.receipt.resolve();out=a.output.resolve()
 assert receipt.is_relative_to(ROOT/'docs/validation') and out.is_relative_to(ROOT/'build') and not out.exists()
 accepted=json.loads(receipt.read_text());assert accepted['passed'] and accepted['actual_ENiGMA_editor_burst_accepted']
 cohort=ROOT/accepted['cohort'];hashes=accepted['captures_sha256']
 for n,h in hashes.items():assert sha(cohort/n)==h,n
 base=json.loads((cohort/'independent-audit.json').read_text());assert base['passed'] and all(base['checks'].values())
 sent,_=Telnet().feed((cohort/'bbs-input.bin').read_bytes());display,_=Telnet().feed((cohort/'bbs-output.bin').read_bytes())
 trace,provenance=frontend_trace(cohort,sent,display,base['payloads']['expected_bridge_bytes'])
 upstream=table(trace,'dos');downstream=table(trace,'bbs')
 body=bytes.fromhex(base['editor']['expected_body_hex']);start=sent.find(body);assert start>=0 and sent.count(body)==1
 ends=keys(body);clean,offsets=visible(display);subject=clean.find(b'KEYTEST');assert subject>=0
 matches=list(re.finditer(rb'(INS|OVR) (\d{2}),(\d{2})',clean[subject:]))
 positions=[[m[1].decode(),int(m[2]),int(m[3])] for m in matches]
 assert positions==base['editor']['positions'] and len(matches)==len(ends)==25
 rows=[]
 for i,(end,match,position) in enumerate(zip(ends,matches,positions)):
  key_time=stamp(upstream,start+end);footer_offset=offsets[subject+match.end()-1]
  footer_time=stamp(downstream,footer_offset)
  rows.append(dict(key=i+1,key_serial_hex=body[0 if i==0 else ends[i-1]+1:end+1].hex(),
   position=position,key_last_byte_frontend_seconds=key_time,footer_last_byte_frontend_seconds=footer_time,
   key_to_footer_transport_seconds=footer_time-key_time))
 checks=dict(accepted_capture_hashes_exact=True,accepted_independent_checks_pass=True,
  exact_full_frontend_manifests=True,all25_BIOS_keys_and_footer_effects_correspond=True,
  every_footer_follows_its_complete_key=all(r['key_to_footer_transport_seconds']>=0 for r in rows),
  original_captures_preserved=all(sha(cohort/n)==h for n,h in hashes.items()))
 result=dict(passed=all(checks.values()),checks=checks,accepted_receipt=str(receipt.relative_to(ROOT)),accepted_receipt_sha256=sha(receipt),
  cohort=accepted['cohort'],key_count=len(rows),rows=rows,
  minimum_transport_seconds=min(r['key_to_footer_transport_seconds'] for r in rows),maximum_transport_seconds=max(r['key_to_footer_transport_seconds'] for r in rows),
  body_input_span_seconds=rows[-1]['key_last_byte_frontend_seconds']-rows[0]['key_last_byte_frontend_seconds'],
  footer_output_span_seconds=rows[-1]['footer_last_byte_frontend_seconds']-rows[0]['footer_last_byte_frontend_seconds'],
  clock_provenance=provenance,inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'lab/bbs/audit_audio_download.py',ROOT/'lab/bbs/diagnose_audio_download_queue.py',ROOT/'lab/bbs/modem.py')},
  captures_sha256={n:sha(cohort/n) for n in ('independent-audit.json','bbs-input.bin','bbs-output.bin','serial-in.bin','serial-out.bin','caller-decoded.bin','serial-input-events.jsonl','serial-write-events.jsonl','node-result.json')},
  scope='Read-only measurement on the accepted25-key rapid single-line editor capture at laboratory V22/1200. Complete key bytes are paired with all independently verified ordered cursor/mode footer responses. One frontend clock measures input reads to decoded display socket-write submissions. These are transport observations, not BIOS keypress or actual DOS consumption/paint timestamps. No responsiveness budget is imposed or passed, no new audio run, no multiline/general performance or physical14.4-kbps claim.')
 with out.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ('passed','key_count','minimum_transport_seconds','maximum_transport_seconds','body_input_span_seconds','footer_output_span_seconds')}));assert result['passed']


if __name__=='__main__':main()
