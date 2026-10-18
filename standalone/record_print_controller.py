#!/usr/bin/env python3
"""Bind dedicated-print native comparisons and DOS diagnostic to exact sources."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text())
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def main():
 manifest=read('build/print_controller/manifest.json')
 checks=read('build/print_controller/checks.json')
 dos=read('build/print-controller-dos/result.json')
 digest=sha('build/print_controller/PRINTCTL.EXE')
 assert manifest['binary_sha256']==checks['binary_sha256']==dos['binary_sha256']==digest
 assert checks['passed'] and checks['linked_cases']==checks['original_cases']==28
 assert dos['passed']
 for name,want in manifest['sources'].items():assert sha(name)==want,name
 for name,want in dos['artifacts'].items():assert sha(name)==want,name
 proof=read('reconstruction/print_controller/provenance.json')
 for unit in proof['units']:
  path='build/print_controller/'+Path(unit['source']).stem+'.bin'
  assert sha(path)==unit['sha256'] and (ROOT/path).stat().st_size==unit['bytes']
 names=['standalone/build_print_controller.py','standalone/check_print_controller.py','standalone/test_print_controller_dos.py','standalone/record_print_controller.py']
 result=dict(passed=True,manifest=manifest,native_provenance=proof,CPU_checks=checks,DOS_checks=dos,
  evidence_source_sha256={name:sha(name) for name in names},
  scope='416 exact native dedicated-print controller bytes;28 linked/original instruction comparisons and actual8086 DOS selfcheck. UART, keyboard, CRT and UI are explicit fixtures. Native unchecked errors, blocking waits and quirks are evidence, not maintained policy; no live CSI5i controller or physical printer claim.')
 (ROOT/'docs/validation/print-controller-native.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded native print controller',digest)
if __name__=='__main__':main()
