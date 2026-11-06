#!/usr/bin/env python3
"""Seal observed CRT startup failure and reject heap settings that lose stream capacity."""
import argparse,json,re,struct
from pathlib import Path
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 def bind(path):return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))
 def load(path):return json.loads(path.read_text())
 base=ROOT/'build/bbs-lab/results/synchronet'
 failed=base/'aspect-crt-startup-message-20261106';r=load(failed/'proxy-integration.json')
 assert not r['passed'] and r['interpreter_sha256']=='23caac9350b0a4be6f5898ce4bbc52c21604a5410a5f3340feae7732e04b004f'
 raw=(failed/'ADMIT.BIN').read_bytes();assert len(raw)==102
 words=struct.unpack_from('<19H',raw)
 assert words[:2]==(0xad41,1) and words[5:9]==(5,0,0,1) and words[10:14]==(0,0,1,words[9])
 message=raw[38:].split(b'\0',1)[0]
 assert words[18]==1 and message==b'Not enough memory to allocate file structures'
 assert load(failed/'result.json')['checks']['hardware_restored']
 wrapper=ROOT/'build/admission-crt-wrapper-20261106/result.json';checked=load(wrapper)
 assert checked['passed'] and len(checked['cases'])==24
 for n,h in checked['sources'].items():assert sha(ROOT/n)==h,n
 products={}
 for policy,folder in [(512,'aspect-default-current-20261106'),(128,'aspect-heap128-20261106'),(256,'aspect-heap256-20261106')]:
  binary=ROOT/'build'/folder/'ASPECT.EXE';m=load(binary.with_name('manifest.json'))
  assert not m['original_inputs'] and not m['diagnostic_build'] and m['startup_heap_growth_bytes']==policy
  assert sha(binary)==m['binary_sha256']
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
  products[policy]=dict(binary=binary,data=binary.read_bytes(),sha256=sha(binary))
 assert products[512]['sha256']==r['interpreter_sha256']
 deltas=[]
 for policy in (128,256):
  binary=products[policy]['binary'];data=products[policy]['data'];original=products[512]['data'];assert len(data)==len(original)
  match=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})\s+__amblksiz\s*$',binary.with_name('ASPECT.map').read_text(),re.M|re.I);assert match
  at=struct.unpack_from('<H',data,8)[0]*16+int(match[1],16)*16+int(match[2],16)
  differences=[i for i,(x,y) in enumerate(zip(original,data)) if x!=y]
  assert differences and set(differences)<={at,at+1} and struct.unpack_from('<H',data,at)[0]==policy
  deltas.append(dict(policy=policy,binary_sha256=products[policy]['sha256'],changed_offsets=differences,heap_word_offset=at,all_other_bytes_identical=True))
 streams=[]
 for label,expected in [('editor128',False),('editor256',False),('reviewed128',False),('reviewed512',True)]:
  path=ROOT/f'build/heap-policy-final-{label}-20261106/result.json';s=load(path);assert s['passed']==expected
  for n,h in s['sources'].items():assert sha(ROOT/n)==h,n
  assert s['checks']['hardware_restored'] and s['checks']['actual_init_and_dial']
  assert s['checks']['all_six_streams']==expected and s['checks']['six_files']==expected
  if label.endswith('128'):assert s['checks']['four_calls'] and s['checks']['missing_and_recovered']
  streams.append(dict(label=label,accepted=expected,report=bind(path),failed_checks=[k for k,v in s['checks'].items() if not v]))
 positive=base/'aspect-heap128-sync-20261106/proxy-integration.json';positive_r=load(positive)
 assert positive_r['passed'] and positive_r['interpreter_sha256']==products[128]['sha256']
 audit=positive.with_name('screen-reference-audit.json');screen=load(audit);assert screen['passed'] and screen['matched_cells']==1920 and screen['different_cells']==0
 negative=base/'aspect-heap256-sync-20261106/proxy-integration.json';assert not load(negative)['passed']
 probe=base/'aspect-crt-open-reason-20261106';probe_words=struct.unpack('<18H',(probe/'ADMIT.BIN').read_bytes());assert probe_words[6:9]==(3,8,0)
 unit=ROOT/'build/file-open-probe-unit-final-20261106/result.json';unit_r=load(unit);assert unit_r['passed'] and len(unit_r['cases'])==2
 for n,h in unit_r['sources'].items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,application_accepted=False,deployment_changed=False,
  terminal_sha256=r['binary_sha256'],reviewed_interpreter_sha256=products[512]['sha256'],
  original_failure=bind(failed/'proxy-integration.json'),capture=bind(failed/'ADMIT.BIN'),DOS_EXEC_succeeded=True,
  CRT_startup_message=message.decode(),child_exit1_is_not_proof_of_ASPECT_RUN_OPEN=True,
  wrapper_validation=bind(wrapper),heap_variants=deltas,repeated_script_and_stream_controls=streams,
  heap128_BBS_success=bind(positive),independent_screen=bind(audit),heap256_BBS_failure=bind(negative),
  oversized_diagnostic_DOS_EXEC_error8=bind(probe/'proxy-integration.json'),file_probe_unit=bind(unit),
  default_policy_retained=512,sources={'standalone/record_crt_heap_policy.py':sha(Path(__file__))},
  limits=['Raw observed startup message establishes CRT file-structure allocation failure, not ASPECT script-open failure.',
   '128-byte growth is rejected despite full Synchronet editor success because six concurrent script streams fail in both tested parents.',
   '256-byte growth is rejected for startup failure; the default512-byte reviewed runner retains all six streams in its paired reviewed parent.',
   'Instrumented runner is too large and fails DOS EXEC; it supplies no evidence about the original fopen path.',
   'Current default source reproduces the exact reviewed interpreter; optional probes/tuning are not selected or deployed.',
   'Parent memory recovery and subsequent compatibility gates remain open; no physical acceptance.'])
 out.mkdir();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS actual CRT failure,24 observer cases,exact heap-word variants and four capacity controls; reject both variants')
if __name__=='__main__':main()
