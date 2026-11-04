#!/usr/bin/env python3
"""Require the disabled application to fail the same real-CWD settings probe."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import types

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve()
 m=json.loads(binary.with_name('manifest.json').read_text());assert not m.get('experimental_cwd_identities') and sha(binary)==m['binary_sha256']
 source=ROOT/'standalone/test_cwd_identities_dos.py';text=source.read_text()
 changes={"assert manifest['experimental_cwd_identities'] and manifest['experimental_original_keys']":"assert not manifest.get('experimental_cwd_identities') and manifest['experimental_original_keys']",
  "[('startup',None),('plain','a-s'),('directory','a-p')]":"[('plain','a-s')]"}
 for old,new in changes.items():assert text.count(old)==1; text=text.replace(old,new)
 driver=types.ModuleType('disabled_cwd_probe');driver.__file__=str(source)
 exec(compile(text,str(source),'exec'),driver.__dict__)
 previous=sys.argv;sys.argv=[str(source),'--terminal',str(binary),'--output',str(out)]
 rejected=False
 try:
  try:driver.main()
  except AssertionError:rejected=True
 finally:sys.argv=previous
 report=json.loads((out/'plain.json').read_text());checks=report['checks']
 failed={name for name,value in checks.items() if not value}
 expected={'absolute_startup_PRM_argument','sibling_setup_executable','setup_in_expected_CWD','setup_read_original_PRM'}
 assert rejected and not report['passed'] and failed==expected,failed
 assert checks['actual_DOS_chdir_observed'] and checks['hardware_restored'] and checks['post_child_UART_query_replied']
 result={'passed':True,'terminal_sha256':sha(binary),'rejected_disabled_probe':True,'failed_checks':sorted(failed),
  'positive_probe_source_sha256':sha(source),'control_checker_sha256':sha(Path(__file__)),
  'scope':__doc__+' Only the enabled-flag preflight and case selection are adapted; the application, child and native probe assertions are unchanged. Expected failure is preserved in plain.json. Not physical acceptance.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS disabled CWD control: real namespace change exposes legacy settings identity failure')

if __name__=='__main__':main()
