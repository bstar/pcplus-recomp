#!/usr/bin/env python3
"""Retain the real optional-flow timing counterexample and mandatory-byte negative."""
import argparse,importlib.util,json
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from audit_zmodem import audit_batch,audit_controls,scan
from test_transfer_dos import timestamp
from prepare_audio_pressure_download import NAME,payload


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cohort',type=Path,required=True);p.add_argument('--baseline-auditor',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 cohort=a.cohort.resolve();baseline=a.baseline_auditor.resolve();out=a.output.resolve()
 assert all(q.is_relative_to(ROOT/'build') for q in (cohort,baseline,out)) and not out.exists()
 failed=json.loads((cohort/'control-timing-failure.json').read_text());assert not failed['passed'] and failed['native_status']==failed['peer_exit']==0 and failed['exact_received_source']
 assert sha(baseline)==failed['inputs']['lab/bbs/audit_zmodem.py']
 wire=(cohort/'sender.bin').read_bytes();opposite=(cohort/'receiver.bin').read_bytes();trace=json.loads((cohort/'trace.json').read_text());expected=(cohort/NAME).read_bytes();assert expected==payload()
 spec=importlib.util.spec_from_file_location('old_zmodem_audit',baseline);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 before=old.audit_batch(wire,{NAME:expected});post=max(r['seconds'] for r in trace)+1
 try:old.audit_controls(before,opposite,trace,'bbs',post)
 except AssertionError as error:old_error=str(error);assert 'Missing opposite header' in old_error
 else:raise AssertionError('Predecessor timing counterexample did not reproduce')
 after=audit_batch(wire,{NAME:expected});controls=audit_controls(after,opposite,trace,'bbs',post)
 eof=next(e for e in after['events'] if e['kind']=='header' and e['type']==11)
 assert eof['response_end']==eof['end']-1 and wire[eof['end']-1]==17
 mandatory=timestamp(trace,'bbs',eof['response_end']-1);flow=timestamp(trace,'bbs',eof['end']-1)
 reply=next(r['seconds'] for r in controls if r['type']==1)
 assert mandatory<=reply<flow
 damaged=[dict(r) for r in trace];headers=[h for h in scan(opposite) if h['type']==1];assert headers
 for row in damaged:
  if row['direction']=='dos' and any(row['offset']<h['end'] and h['offset']<row['offset']+row['size'] for h in headers):row['seconds']=mandatory-.001
 try:audit_controls(after,opposite,damaged,'bbs',post)
 except AssertionError as error:negative=str(error);assert 'Missing opposite header' in negative
 else:raise AssertionError('Accepted response before mandatory EOF bytes')
 def without_new_fields(value):
  if isinstance(value,dict):return {k:without_new_fields(v) for k,v in value.items() if k!='response_end'}
  if isinstance(value,list):return [without_new_fields(v) for v in value]
  return value
 assert without_new_fields(after)==before
 r=dict(passed=True,real_pipe_counterexample_reproduced=True,corrected_full_protocol_and_controls_pass=True,premature_mandatory_byte_reply_rejected=True,
  protocol_fields_other_than_response_end_unchanged=True,predecessor_error=old_error,negative_error=negative,mandatory_EOF_end_seconds=mandatory,completion_reply_seconds=reply,optional_XON_read_seconds=flow,
  inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'lab/bbs/audit_zmodem.py',baseline)},
  captures_sha256={str((cohort/n).relative_to(ROOT)):sha(cohort/n) for n in ('sender.bin','receiver.bin','trace.json','control-timing-failure.json',NAME)},
  scope='Verifier timing correction on retained real stock-helper/native-host pipe bytes. Predecessor rejects an actual reply after CRC-checked EOF/LF but before optional XON read; corrected auditor passes unchanged full source/CRC/EOF/ZFIN/OO/controls and rejects a copied premature-required-byte timestamp. Only parser response_end metadata is added; full stream accounting stays intact. No product/BBS/audio/pressure compatibility acceptance follows.')
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'passed':True,'real_pipe_counterexample_reproduced':True,'mandatory_before_reply_before_XON':mandatory<=reply<flow}))


if __name__=='__main__':main()
