#!/usr/bin/env python3
"""Seal one complete unsaved multiline DOS/ENiGMA software-audio workflow."""
import argparse,json,subprocess
from pathlib import Path
import enigma
from editor_multiline_evidence import ROOT,sha,load,message_count
from synthmodem_buffered_runtime import validate as validate_runtime


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--controls',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.cohort.resolve();target=a.output.resolve();controls=a.controls.resolve()
 assert out.is_relative_to(ROOT/'build') and controls.is_relative_to(ROOT/'build')
 assert target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 read=lambda n:json.loads((out/n).read_text());r=read('result.json');base=read('independent-audit.json');io=read('serial-io-audit.json');offline=read('offline-caller.json')
 assert r['route']=='editor' and r['editor_multiline_checks'] and not r.get('editor_burst_checks')
 assert r['buffered_runtime_proof'] and r['posttrain_hold'] and r['input_sequence_timeout_ms']==250
 assert Path(r['server_root'])==enigma.SOURCE and r['server_revision']==enigma.COMMIT
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=enigma.SOURCE,text=True).strip()==enigma.COMMIT
 subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=enigma.SOURCE,check=True)
 for report in (r,base):assert report['passed'] and all(report['checks'].values())
 assert io['evidence_consistent'] and all(io['checks'].values()) and not io['error_events']
 assert all(io['counters'][n]==0 for n in ('pendingBytes','failedCallbackBytes','skippedBytes'))
 def inputs(group):
  for n,h in group.items():assert sha(ROOT/n)==h,n
 def captures(group):
  for n,h in group.items():assert sha(out/n)==h,n
 for group in ('frozen_inputs','runtime_inputs','tool_inputs'):inputs(r[group])
 for group in ('generated_inputs','captures_sha256'):captures(r[group])
 inputs(base['audit_inputs']);captures(io['capture_sha256'])
 for n,h in r['server_inputs'].items():assert sha(enigma.SOURCE/n)==h,n
 assert base['producer_sha256']==sha(out/'result.json')
 assert base['auditor_sha256']==r['frozen_inputs']['lab/bbs/audit_synthmodem_audio_dos.py']
 assert io['auditor_sha256']==r['frozen_inputs']['lab/bbs/audit_serial_io_evidence.py']
 runtime=Path(next(iter(r['runtime_inputs'])))
 runtime=next(p for p in runtime.parents if (p/'source/config.js').is_file())
 assert validate_runtime(runtime,ROOT/r['buffered_runtime_proof'])==r['runtime_inputs']
 proof,ref,expected,positions=load(ROOT/r['editor_multiline_checks'])
 assert sha(out/'program/EXITKEY.COM')==proof['production_helper_sha256']
 for name,path in [('TERMINAL.EXE','build/terminal/TERMINAL.EXE'),('ASPECT.EXE','build/aspect-runner/ASPECT.EXE')]:assert sha(out/'program'/name)==r['frozen_inputs'][path]
 assert base['editor']['positions']==[list(p) for p in positions]
 assert base['editor']['actual_DOS_body_hex']==expected.hex()
 assert r['editor']['message_count_before']==r['editor']['message_count_after']==message_count()
 prefix=b'ATZ\rATD1\r';serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(prefix);online=serial[len(prefix):]
 assert offline['checker_sha256']==r['frozen_inputs']['lab/bbs/diagnose_audio_caller.js']
 assert offline['capture_sha256']==sha(out/'rtp-from-caller.bin')
 assert offline['decoder_sha256']==sha(runtime/'source/src/dsp/protocols/V22Demodulator.js')
 assert bytes.fromhex(''.join(row['hex'] for row in offline['received']))==online
 negative=json.loads(controls.read_text());assert negative['passed'] and negative['original_TCP_captures_unchanged']
 assert len(negative['cases'])==10 and all(c['passed'] for c in negative['cases']) and all(negative['baseline_checks'].values())
 inputs(negative['inputs']);assert negative['inputs'][r['editor_multiline_checks']]==sha(ROOT/r['editor_multiline_checks'])
 assert negative['inputs']['lab/bbs/editor_multiline_evidence.py']==r['frozen_inputs']['lab/bbs/editor_multiline_evidence.py']
 names=list(dict.fromkeys([*r['captures_sha256'],'result.json','independent-audit.json','serial-io-audit.json','offline-caller.json']))
 result=dict(passed=True,actual_ENiGMA_multiline_audio_accepted=True,cohort=str(out.relative_to(ROOT)),
  check_counts=dict(producer=len(r['checks']),independent=len(base['checks']),serial=len(io['checks']),BIOS_helper=sum(len(c['checks']) for c in proof['cases']),TCP_reference=len(ref['checks']),evidence_counterexamples=len(negative['cases'])),
  producer_checks=r['checks'],independent_checks=base['checks'],serial_checks=io['checks'],editor=base['editor'],
  body_BIOS_keys=288,exact_position_responses=318,exact_online_bytes=len(online),exact_BBS_display_bytes=base['payloads']['BBS_display_bytes'],
  payloads=base['payloads'],hardware_snapshot=base['hardware_snapshot'],serial_counters=io['counters'],
  message_count_before=r['editor']['message_count_before'],message_count_after=r['editor']['message_count_after'],
  terminal_sha256=sha(out/'program/TERMINAL.EXE'),ASPECT_sha256=sha(out/'program/ASPECT.EXE'),
  server_revision=r['server_revision'],server_root=r['server_root'],server_inputs=r['server_inputs'],buffered_runtime_proof=r['buffered_runtime_proof'],
  helper_proof=r['editor_multiline_checks'],helper_proof_sha256=sha(ROOT/r['editor_multiline_checks']),TCP_reference=proof['reference'],TCP_reference_sha256=sha(ROOT/proof['reference']),
  controls_receipt=str(controls.relative_to(ROOT)),controls_receipt_sha256=sha(controls),control_inputs=negative['inputs'],
  producer_inputs=r['frozen_inputs'],runtime_inputs=r['runtime_inputs'],audit_inputs=base['audit_inputs'],tool_inputs=r['tool_inputs'],
  captures_sha256={n:sha(out/n) for n in names},recorder_sha256=sha(Path(__file__)),
  scope='One source-built DOS/ASPECT unsaved30-line draft plus newline31 on pinned stock owned ENiGMA through real software SIP/RTP/V22-1200 DSP/Telnet at38400DTE.288 actual BIOS body keys, all318 cursor/mode responses, exact authored and complete display streams, cross-line edits, three PageUp/three PageDown operations and edited-text redisplay pass. Unique TAIL/OVR31,05 DOS video precedes exit. Full byte/serial/cleanup audits and independent caller waveform match; source/runtime identity and message count preserve. This is the80x25/14-line viewport only, not sustained pressure/latency, other profiles/peers, physical Boca/SPA2102 or F01-F16 whole-application completion.')
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':True,'actual_ENiGMA_multiline_audio_accepted':True,'check_counts':result['check_counts'],'receipt':str(target)}))


if __name__=='__main__':main()
