#!/usr/bin/env python3
"""Seal the ESC-restart correction without extending historical audio claims."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();target=a.output.resolve()
 assert target.is_relative_to(ROOT/'docs/validation') and not target.exists()
 baseline=ROOT/'docs/validation/upload-startup-ESC-restart-baseline.json';old=load(baseline)
 assert not old['passed'] and len(old['cases'])==6 and sum(not c['passed'] for c in old['cases'])==5
 assert sha(ROOT/old['baseline_capture'])==old['baseline_capture_sha256']
 captures={str(baseline.relative_to(ROOT)):sha(baseline),old['baseline_capture']:old['baseline_capture_sha256']}
 builds={}
 for name in ('terminal','terminal-mouse','terminal-mouse-process','terminal-traps-mouse'):
  out=ROOT/'build'/name;m=load(out/'manifest.json');guard=load(out/'terminal-transfer-ui-bank.json');binary=sha(out/'TERMINAL.EXE')
  assert m['binary_sha256']==guard['binary_sha256']==binary and guard['passed'] and len(guard['cases'])==19
  assert m['memory_layout']['transfer_ui_far_entries_verified']==4 and m['memory_layout']['transfer_ui_resident_callbacks_verified']==3
  for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
  for n,h in guard['inputs'].items():assert sha(ROOT/n)==h,n
  builds[name]=dict(binary_sha256=binary,resident_spare=m['memory_layout']['resident_code_spare_bytes'],data_stack_bytes=m['data_stack_bytes'])
  for p in (out/'manifest.json',out/'terminal.map',out/'terminal-transfer-ui-bank.json'):captures[str(p.relative_to(ROOT))]=sha(p)
 current=builds['terminal']['binary_sha256'];fixed=load(ROOT/'build/terminal/terminal-upload-startup-restart.json')
 assert fixed['passed'] and len(fixed['cases'])==6 and fixed['binary_sha256']==current and current!=old['binary_sha256']
 assert all(c['passed'] and c['handshake_offered'] and c['elapsed_ticks']>=60 for c in fixed['cases'])
 for report in (old,fixed):
  for n,h in report['inputs'].items():assert sha(ROOT/n)==h,n
 linked={}
 for name,count in [('terminal-upload-startup-restart.json',6),('terminal-upload-startup.json',43),('terminal-upload-live-checks.json',54),('terminal-upload-cancel-boundary.json',37),('terminal-transfer-live-checks.json',44)]:
  p=ROOT/'build/terminal'/name;r=load(p);assert r['passed'] and r['binary_sha256']==current
  assert (r['inputs'] if isinstance(r.get('inputs'),int) else len(r['cases']))==count
  linked[name]=count;captures[str(p.relative_to(ROOT))]=sha(p)
 folder=ROOT/'build/terminal-upload-dos'/a.label;actual=load(folder/'restart-checks.json')
 assert actual['passed'] and actual['binary_sha256']==current and len(actual['cases'])==6
 for c in actual['cases']:
  assert c['passed'] and all(c['checks'].values()) and c['checks']['no_packet_during_banner'] and c['checks']['required_complete_EOT']
 for n,h in actual['inputs'].items():assert sha(ROOT/n)==h,n
 for p in folder.rglob('*'):
  if p.is_file():captures[str(p.relative_to(ROOT))]=sha(p)
 paths=['src/terminal/upload_startup.asm','standalone/check_upload_startup_restart.py','standalone/test_upload_startup_restart_dos.py','standalone/record_upload_startup_restart.py','Makefile']
 result=dict(passed=True,component_ESC_restart_accepted=True,actual_DOS_ESC_restart_accepted=True,actual_audio_accepted=False,
  baseline_receipt=str(baseline.relative_to(ROOT)),baseline_sha256=sha(baseline),baseline_binary_sha256=old['binary_sha256'],builds=builds,
  linked_cases=linked,ESC_restart_cases=fixed['cases'],actual_DOS=actual['cases'],inputs={n:sha(ROOT/n) for n in paths},capture_sha256=captures,recorder_sha256=sha(Path(__file__)),
  scope='Fresh ESC restarts incomplete ESC/CSI/charset states; OSC/DCS string ESC/ST ownership stays intact. Five premature-handshake failures reproduce in six linked baseline cases; all six now wait for the independent60tick handshake, then complete. Six actual DOS scenarios with real held receiver handshake and exact source/CRC/checksum/EOT/recovery/hardware gates pass.43 ordinary startup and135 upload/receive/boundary regressions plus all four build/bridge validations pass. Historical audio acceptance remains bound to3b; these new binaries are not declared audio-validated. Arbitrarily paused plaintext handshake ambiguity, receiver partial cleanup, physical hardware and F01-F16 remain open.')
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,linked_cases=sum(linked.values()),actual_DOS_cases=6,builds=len(builds),receipt=str(target))))

if __name__=='__main__':main()
