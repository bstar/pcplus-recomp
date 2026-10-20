#!/usr/bin/env python3
"""Reproduce retained warmup timers using actual Node process exit times."""
import argparse,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 source=a.source.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 ledger=ROOT/'docs/validation/synthmodem-gateway.json';prior=json.loads(ledger.read_text());assert prior['passed']
 reference=ROOT/'build/bbs-lab/synthmodem-gateway-01/runtime/source'
 files=['config.js','src/logger.js','src/backends/ModemBackendPool.js']
 inputs={n:sha(source/n) for n in files}
 for n,h in inputs.items():assert h==prior['tested_inputs'][str(reference/n)]
 frozen={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'check.js',HERE/'pool.patch',ledger]}
 results={}
 for variant in ('baseline','candidate'):
  staged=out/variant
  for n in files:(staged/n).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/n,staged/n)
  if variant=='candidate':subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(HERE/'pool.patch')],cwd=staged,check=True)
  results[variant]={}
  for scenario in ('success','reject','timeout','recycle'):
   start=time.monotonic();r=subprocess.run(['node',str(HERE/'check.js'),str(staged),scenario],capture_output=True,text=True,timeout=6,check=True);elapsed=time.monotonic()-start
   report=json.loads(r.stdout);assert report['passed']
   if scenario!='timeout':assert elapsed>1.4 if variant=='baseline' else elapsed<.8,(variant,scenario,elapsed)
   else:assert 1.4<elapsed<3,(variant,elapsed)
   results[variant][scenario]={'report':report,'natural_process_exit_seconds':elapsed}
 assert all(sha(source/n)==h for n,h in inputs.items()) and all(sha(ROOT/n)==h for n,h in frozen.items())
 result={'passed':True,'reports':results,'source_inputs':inputs,'frozen_inputs':frozen,'candidate_sha256':sha(out/'candidate/src/backends/ModemBackendPool.js'),'node':subprocess.check_output(['node','--version'],text=True).strip(),
  'scope':'Actual Node pool methods and natural process exit, modeled backend startup; no VM/SIP/DSP/DOS or installed-service change.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
