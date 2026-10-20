#!/usr/bin/env python3
"""Stage/verify a normal gateway image replacing only the selected d-modem."""
import argparse,gzip,hashlib,json,shutil,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha,records,archive
from synthmodem_sparse_runtime import validate as validate_sparse

LEDGER=ROOT/'docs/validation/synthmodem-jitter-policy.json'
REFERENCE=ROOT/'build/bbs-lab/synthmodem-sparse-runtime-01/runtime'

def validate(runtime,variant):
 baseline=validate_sparse(REFERENCE);r=json.loads(LEDGER.read_text());assert r['passed']
 expected={str(Path(n).relative_to(REFERENCE)):h for n,h in baseline.items()}
 assert {str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()}==set(expected)
 for n,h in expected.items():
  if n!='candidate.cpio.gz':assert sha(runtime/n)==h,n
 old=records(gzip.decompress((REFERENCE/'candidate.cpio.gz').read_bytes()));new=records(gzip.decompress((runtime/'candidate.cpio.gz').read_bytes()))
 assert len(old)==len(new);changed=[]
 for (n,f,b),(nn,ff,bb) in zip(old,new):
  assert n==nn and f[:6]+f[7:]==ff[:6]+ff[7:]
  if b!=bb:changed.append(n)
  if n=='usr/local/bin/d-modem':assert hashlib.sha256(bb).hexdigest()==r['builds'][variant]['executable_sha256']
 assert changed==['usr/local/bin/d-modem'],changed
 return {str(runtime/n):sha(runtime/n) for n in expected}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--variant',choices=['baseline','candidate'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');inputs=validate_sparse(REFERENCE)
 names=['lab/bbs/synthmodem_jitter_runtime.py','lab/bbs/synthmodem_sparse_runtime.py','lab/bbs/synthmodem_vm_control.py','docs/validation/synthmodem-gateway.json','docs/validation/synthmodem-sparse.json',str(LEDGER.relative_to(ROOT)),'nix/dmodem.nix','nix/flake.lock','tools/build-dmodem']
 frozen={n:sha(ROOT/n) for n in names}
 built=json.loads(subprocess.check_output([str(ROOT/'tools/build-dmodem'),a.variant,'--no-link','--json'],text=True));helper=Path(built[0]['outputs']['out'])/'bin/d-modem'
 assert sha(helper)==json.loads(LEDGER.read_text())['builds'][a.variant]['executable_sha256']
 out.mkdir(parents=True,exist_ok=False);runtime=out/'runtime';shutil.copytree(REFERENCE,runtime)
 entries=records(gzip.decompress((REFERENCE/'candidate.cpio.gz').read_bytes()))
 for i,(n,f,b) in enumerate(entries):
  if n=='usr/local/bin/d-modem':entries[i]=(n,f,helper.read_bytes())
 entries.append(('TRAILER!!!',[0]*13,b''));(runtime/'candidate.cpio.gz').write_bytes(gzip.compress(archive(entries),mtime=0))
 tested=validate(runtime,a.variant)
 assert all(sha(Path(n))==h for n,h in inputs.items()) and all(sha(ROOT/n)==h for n,h in frozen.items())
 r={'passed':True,'variant':a.variant,'runtime_inputs':inputs,'tested_inputs':tested,'frozen_inputs':frozen,'build':built,
  'scope':'Normal runtime staging/identity verification only. Only d-modem changes; no export daemon, alternate init, SIP/DSP execution or installed-service change.'}
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':True,'variant':a.variant,'runtime':str(runtime),'image_sha256':sha(runtime/'candidate.cpio.gz')},indent=2))
if __name__=='__main__':main()
