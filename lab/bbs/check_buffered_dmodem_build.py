#!/usr/bin/env python3
"""Verify the isolated 200ms, no-discard d-modem source build."""
import argparse,json,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha


def verify(built):
 ledger=ROOT/'docs/validation/synthmodem-jitter-policy.json'
 reference=json.loads(ledger.read_text())['builds']['candidate']
 normal=Path(reference['build']['outputs']['out']);out=Path(built[0]['outputs']['out'])
 source='share/pcplus-dmodem/d-modem.c';binary=out/'bin/d-modem'
 assert sha(normal/source)==reference['source_sha256'] and sha(normal/'bin/d-modem')==reference['executable_sha256']
 expected=(normal/source).read_bytes()
 for field in ('jb_min_pre','jb_max_pre','jb_init'):
  before=f'med_cfg.{field} = 40;'.encode();assert expected.count(before)==1
  expected=expected.replace(before,f'med_cfg.{field} = 200;'.encode())
 assert (out/source).read_bytes()==expected
 headers='share/pcplus-dmodem/slmodemd'
 assert {p.name:sha(p) for p in (normal/headers).iterdir()}=={p.name:sha(p) for p in (out/headers).iterdir()}
 elf=binary.read_bytes();assert elf[:5]==b'\x7fELF\x01' and int.from_bytes(elf[18:20],'little')==3
 assert 'INTERP' not in subprocess.check_output(['readelf','-l',str(binary)],text=True)
 return dict(build=built[0],executable=str(binary),executable_sha256=sha(binary),source_sha256=sha(out/source),
  reference_ledger_sha256=sha(ledger),reference_candidate=reference,ELF32_i386_static=True,
  prefetch_ms=200,discard_policy='PJMEDIA_JB_DISCARD_NONE',only_source_changes=['jb_min_pre:40->200','jb_max_pre:40->200','jb_init:40->200'])


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 built=json.loads(subprocess.check_output([str(ROOT/'tools/build-dmodem'),'buffered','--no-link','--json'],text=True))
 result=dict(passed=True,build_only=True,compatibility_accepted=False,buffered=verify(built),
  inputs={n:sha(ROOT/n) for n in ('lab/bbs/check_buffered_dmodem_build.py','nix/dmodem.nix','tools/build-dmodem','nix/flake.lock')},
  scope='Source/build identity only. Same pinned toolchain, PJSIP and no-discard candidate source except three40->200ms prefetch constants; static i386 ELF and identical modem headers. No runtime/DOS/BBS/physical acceptance or installed/default change.')
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,executable_sha256=result['buffered']['executable_sha256'])))


if __name__=='__main__':main()
