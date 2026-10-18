#!/usr/bin/env python3
"""Bind recovered screen-print evidence to source and executable identities."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text())
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def main():
 manifest=read('build/print_screen/manifest.json')
 checks=read('build/print_screen/checks.json')
 dos=read('build/terminal-printer-dos/native-printscreen-8086/result.json')
 digest=sha('build/print_screen/PRINTSCR.EXE')
 assert manifest['binary_sha256']==checks['binary_sha256']==dos['binary_sha256']==digest
 assert checks['passed'] and checks['linked_cases']==checks['original_cases']==38
 assert dos['passed']
 for name,want in manifest['sources'].items():assert sha(name)==want,name
 for name,want in dos['artifacts'].items():assert sha(name)==want,name
 proof=read('reconstruction/print_screen/provenance.json')
 for unit in proof['units']:
  path='build/print_screen/'+Path(unit['source']).stem+'.bin'
  assert sha(path)==unit['sha256'] and (ROOT/path).stat().st_size==unit['bytes']
 names=['standalone/build_print_screen.py','standalone/check_print_screen.py','standalone/record_print_screen.py']
 result=dict(passed=True,manifest=manifest,native_provenance=proof,CPU_checks=checks,DOS_checks=dos,
  evidence_source_sha256={name:sha(name) for name in names},
  scope='365 exact recovered native bytes; 38 linked/original instruction comparisons and actual8086 DOS diagnostic with explicit CRT/device/cursor/UI fixtures. Native unsafe ownership and ignored errors retained for evidence. No live screen-print command or physical printer validation.')
 (ROOT/'docs/validation/print-screen-native.json').write_text(json.dumps(result,indent=2)+'\n')
 print('Recorded native screen printing',digest)
if __name__=='__main__':main()
