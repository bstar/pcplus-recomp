#!/usr/bin/env python3
"""Compose the accepted pool/registrar fixes with the normal rebuilt gateway."""
import argparse,json,shutil,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from synthmodem_jitter_runtime import validate as validate_jitter

REFERENCE=ROOT/'build/bbs-lab/synthmodem-jitter-runtime-01/runtime'
POOL=ROOT/'docs/validation/synthmodem-pool.json'
REGISTRAR=ROOT/'docs/validation/synthmodem-registrar.json'

def expected():
 prior=validate_jitter(REFERENCE,'candidate');pool=json.loads(POOL.read_text());reg=json.loads(REGISTRAR.read_text());assert pool['passed'] and reg['passed']
 result={str(Path(n).relative_to(REFERENCE)):h for n,h in prior.items()}
 result['source/src/backends/ModemBackendPool.js']=pool['candidate_sha256']
 for name in ('src/tunnel/UdpTcpTunnel.js','src/sip/VmRegistrar.js'):result['source/'+name]=reg['staged_sources']['candidate'][name]
 return result,prior

def validate(runtime):
 files,_=expected();assert {str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()}==set(files)
 for n,h in files.items():assert sha(runtime/n)==h,n
 return {str(runtime/n):h for n,h in files.items()}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build')
 files,inputs=expected();patches=[ROOT/'lab/bbs/patches/synthmodem-pool/pool.patch',ROOT/'lab/bbs/patches/synthmodem-registrar/registrar.patch']
 for patch,ledger in zip(patches,(POOL,REGISTRAR)):
  prior=json.loads(ledger.read_text());assert sha(patch)==prior['frozen_inputs'][str(patch.relative_to(ROOT))]
 names=['lab/bbs/synthmodem_lifecycle_runtime.py','lab/bbs/synthmodem_jitter_runtime.py','lab/bbs/synthmodem_sparse_runtime.py','lab/bbs/synthmodem_vm_control.py','docs/validation/synthmodem-gateway.json','docs/validation/synthmodem-sparse.json','docs/validation/synthmodem-jitter-policy.json','nix/flake.lock']+[str(p.relative_to(ROOT)) for p in [POOL,REGISTRAR,*patches]]
 frozen={n:sha(ROOT/n) for n in names};out.mkdir(parents=True,exist_ok=False);runtime=out/'runtime';shutil.copytree(REFERENCE,runtime)
 for patch in patches:subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=runtime/'source',check=True)
 tested=validate(runtime);changed=[str(Path(n).relative_to(REFERENCE)) for n,h in inputs.items() if sha(runtime/Path(n).relative_to(REFERENCE))!=h]
 assert sorted(changed)==['source/src/backends/ModemBackendPool.js','source/src/sip/VmRegistrar.js','source/src/tunnel/UdpTcpTunnel.js']
 assert all(sha(Path(n))==h for n,h in inputs.items()) and all(sha(ROOT/n)==h for n,h in frozen.items())
 r={'passed':True,'runtime_inputs':inputs,'tested_inputs':tested,'frozen_inputs':frozen,'changed_files':changed,
  'scope':'Exact three-file lifecycle source composition; byte-identical accepted normal kernel/initrd. Staging verification only, no installed service or runtime acceptance.'}
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':True,'runtime':str(runtime),'changed_files':changed},indent=2))
if __name__=='__main__':main()
