#!/usr/bin/env python3
"""Bind native startup fix, failing baseline, linked cases and actual DOS probes."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--dos',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 baseline=a.baseline.resolve();dos=a.dos.resolve();target=a.output.resolve();build=ROOT/'build/terminal'
 assert baseline.is_relative_to(ROOT/'build') and dos.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 old=json.loads(baseline.read_text());fixed_path=build/'terminal-upload-startup.json';fixed=json.loads(fixed_path.read_text());actual=json.loads(dos.read_text());manifest=json.loads((build/'manifest.json').read_text());binary=sha(build/'TERMINAL.EXE')
 assert not old['passed'] and len(old['cases'])==16 and len(fixed['cases'])==43
 assert fixed['passed'] and actual['passed'] and len(actual['cases'])==3
 assert fixed['binary_sha256']==actual['binary_sha256']==manifest['binary_sha256']==binary
 for report in (old,fixed,actual):
  for n,h in report['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in fixed['product_inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 indexed={c['label']:c for c in fixed['cases']};failures=[c['label'] for c in old['cases'] if not c['passed']]
 assert {'plain_CRC','ANSI_cursor_CRC','plain_checksum'}<=set(failures)
 assert all(indexed[c['label']]['passed'] for c in old['cases'])
 regressions={}
 for name,count in [('terminal-upload-live-checks.json',54),('terminal-upload-cancel-boundary.json',37),('terminal-transfer-live-checks.json',44)]:
  path=build/name;r=json.loads(path.read_text());assert r['passed'] and r['binary_sha256']==binary
  got=len(r['cases']) if name=='terminal-upload-cancel-boundary.json' else sum(c['inputs'] for c in r['cases'])
  assert got==count;regressions[name]=dict(cases=count,sha256=sha(path))
 original={}
 provenance=json.loads((ROOT/'reconstruction/transfer_send/provenance.json').read_text())
 for leaf in ('session','cancel'):
  unit=next(u for u in provenance['units'] if u['source']==leaf+'.asm');flat=build/'native-sender'/('transfer_send_'+leaf+'.bin')
  assert sha(flat)==unit['sha256'] and flat.stat().st_size==unit['bytes'];original[leaf]=unit['sha256']
 listing=(build/'terminal.map').read_text();text=re.search(r'^_TEXT\s+CODE\s+\S+\s+\S+\s+([0-9a-f]+)',listing,re.M|re.I);assert text
 near_code=int(text[1],16);assert near_code<=65536 and manifest['data_stack_bytes']<=65536
 captures={str(baseline.relative_to(ROOT)):sha(baseline),str(dos.relative_to(ROOT)):sha(dos),str(fixed_path.relative_to(ROOT)):sha(fixed_path),str((build/'manifest.json').relative_to(ROOT)):sha(build/'manifest.json'),str((build/'terminal.map').relative_to(ROOT)):sha(build/'terminal.map')}
 for row in actual['cases']:
  folder=dos.parent/row['case']
  for path in folder.iterdir():
   if path.is_file():captures[str(path.relative_to(ROOT))]=sha(path)
 result=dict(passed=True,component_startup_accepted=True,actual_DOS_startup_accepted=True,actual_audio_startup_accepted=False,
  binary_sha256=binary,baseline_binary_sha256=old['binary_sha256'],baseline_source_checkpoint='9537481ddfaf557a7a71115bc2ffa6347449817c',baseline_failures=failures,
  linked_cases=43,actual_DOS_cases=3,linked_checks=fixed['cases'],actual_DOS_checks=actual['cases'],regressions=regressions,unchanged_native_flat_sha256=original,
  near_code_bytes=near_code,near_code_spare_bytes=65536-near_code,data_stack_bytes=manifest['data_stack_bytes'],product_inputs=fixed['product_inputs'],checker_inputs=fixed['inputs'],DOS_inputs=actual['inputs'],capture_sha256=captures,
  recorder_sha256=sha(Path(__file__)),
  scope='Maintained initial-handshake adapter only, identified by native send_at_df9a return IP. Exact recovered sender/cancel flat instructions are unchanged. Two quiet BIOS ticks distinguish uninterrupted banner letters from raw C/G/U/W; ANSI CSI/strings/charset state persists across bounded reads and retires at notice. NAK/CAN remain immediate; normal ACK/EOT read paths and watchdogs retain their policy.43 linked cases,54 upload/37 boundary/44 receive regressions and3 actual DOS independent-peer startup/transfer/recovery cases pass. Retry-counter fixture advances time through startup, then freezes only after first physical packet to retain15-attempt isolation. Audio, physical hardware and full application completion are not accepted by this component receipt. Arbitrarily paused plain-text handshake letters remain ambiguous on the unframed startup channel.')
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,linked_cases=43,actual_DOS_cases=3,regressions=135,receipt=str(target))))

if __name__=='__main__':main()
