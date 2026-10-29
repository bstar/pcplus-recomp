#!/usr/bin/env python3
"""Actual directory login child changes CWD; accounting must retain its source."""
import argparse,hashlib,json,struct,sys,subprocess,tempfile
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import directory,prm
from directory_test_support import accounting_check
ROOT=harness.ROOT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--expect-counterexample',action='store_true');a=p.parse_args()
 assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
 package=a.package.resolve();manifest=json.loads((package/'manifest.json').read_text())
 assert manifest['experimental_directory_resource_owner']
 for leaf,h in manifest['files'].items():assert sha(package/'PCPLUSSE'/leaf)==h,leaf
 source='proc main\nchdir "D:\\OTHER"\nmkdir "WITNESS"\ntransmit "CWD-MOVED^M"\nendproc\n'
 script=compile_source(source)
 raw=bytearray(directory(port=3,baud=5));raw[250+0x34:250+0x3d]=b'CHDIR\0\0\0\0'
 settings=bytearray(prm(port=3,baud=5));struct.pack_into('<H',settings,0x188,5);struct.pack_into('<HH',settings,0x4e4,8,4)
 name='directory-account-identity-'+a.label;out=ROOT/'build/connection-dos'/name;assert not out.exists()
 with tempfile.TemporaryDirectory(prefix='directory-identity-observer-') as temporary:
  observer=Path(temporary)/'IDWATCH.COM';subprocess.run(['nasm','-fbin',str(ROOT/'standalone/directory_identity_watch.asm'),'-o',str(observer)],check=True);observer_bytes=observer.read_bytes()
 harness.BINARY=package/'PCPLUSSE/TERMINAL.EXE'
 result=harness.run(name,'success','p900 enter p7000 a-x',directory=bytes(raw),prm=bytes(settings),
  arguments='@D:\\TEST.PRM /E:TEST.DIR /N:1',com=3,irq=5,cpu='8086',working_drive='d',
  files={'CHDIR.ASX':script,'OTHER/TEST.DIR':bytes(raw),'IDWATCH.COM':observer_bytes},observer='IDWATCH')
 observed=(out/'IDENTITY.BIN').read_bytes();assert len(observed)==70
 magic,opens,mode=struct.unpack_from('<3H',observed);first=observed[6:].split(b'\0',1)[0]
 wire=(out/'serial.bin').read_bytes();root=(out/'TEST.DIR').read_bytes();decoy=(out/'OTHER/TEST.DIR').read_bytes()
 checks=dict(result['checks']);checks.update(initial_read_uses_frozen_absolute_path=magic==0x4944 and opens>=2 and mode in (0x3d00,0x3d80) and first==b'D:\\TEST.DIR',actual_child_transmitted=b'CWD-MOVED\r' in wire,
  actual_child_CWD_changed=(out/'OTHER/WITNESS').is_dir() and not (out/'WITNESS').exists(),
  original_source_accounted=accounting_check(raw,root,1),decoy_preserved=decoy==raw,
  no_new_recovery_files=not any((folder/leaf).exists() for folder in (out,out/'OTHER') for leaf in ('PCPSTG.$$$','PCPBAK.$$$')))
 passed=all(checks.values());counterexample=(not checks['original_source_accounted'] and root==raw and accounting_check(raw,decoy,1)
  and checks['actual_child_transmitted'] and checks['actual_child_CWD_changed'] and checks['hardware_restored'] and checks['DOS_expected_exit'])
 report=dict(passed=passed,counterexample_reproduced=counterexample,checks=checks,binary_sha256=sha(harness.BINARY),
  package_manifest_sha256=sha(package/'manifest.json'),script_source=source,script_sha256=hashlib.sha256(script).hexdigest(),
  sources={str(q.relative_to(ROOT)):sha(q) for q in [Path(__file__).resolve(),ROOT/'standalone/test_connection_dos.py',ROOT/'standalone/directory_fixtures.py',ROOT/'standalone/directory_test_support.py',ROOT/'src/aspect/compiler.py',ROOT/'standalone/directory_identity_watch.asm']},
  captures={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},
  first_content_open=dict(path=first.decode('ascii'),mode=mode,content_opens=opens),
  scope='Actual DOS8086 COM3/IRQ5 parent and ASPECT post-connect child, DOS chdir/mkdir, source and identical decoy directories, accounting, passive DOS open-path observation with checked observer vector restoration and final UART/PIC/vector restoration. Synthetic modem and owned guest drives only; no physical or full application acceptance.')
 (out/'identity-result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,counterexample_reproduced=counterexample,checks=checks),indent=2))
 assert counterexample if a.expect_counterexample else passed
if __name__=='__main__':main()
