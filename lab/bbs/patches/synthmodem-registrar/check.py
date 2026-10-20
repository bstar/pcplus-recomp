#!/usr/bin/env python3
"""Exercise actual registrar/UAC/tunnel routing over loopback TCP and UDP."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 source=a.source.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 ledger=ROOT/'docs/validation/synthmodem-gateway.json';prior=json.loads(ledger.read_text());assert prior['passed']
 reference=ROOT/'build/bbs-lab/synthmodem-gateway-01/runtime/source'
 files=['config.js','src/logger.js','src/tunnel/UdpTcpTunnel.js','src/sip/VmRegistrar.js','src/sip/SipParser.js','src/sip/SipUacInternal.js']
 inputs={n:sha(source/n) for n in files}
 for n,h in inputs.items():assert h==prior['tested_inputs'][str(reference/n)]
 frozen={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),HERE/'check.js',HERE/'registrar.patch',ledger]}
 results={};sources={}
 for variant in ('baseline','candidate'):
  staged=out/variant
  for n in files:(staged/n).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/n,staged/n)
  if variant=='candidate':subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(HERE/'registrar.patch')],cwd=staged,check=True)
  run=subprocess.run(['node',str(HERE/'check.js'),str(staged),variant],capture_output=True,text=True,timeout=15)
  assert run.returncode==0,(variant,run.stdout,run.stderr)
  results[variant]=json.loads(run.stdout);assert results[variant]['passed'] and all(results[variant]['checks'].values())
  sources[variant]={n:sha(staged/n) for n in files}
 assert all(sha(source/n)==h for n,h in inputs.items()) and all(sha(ROOT/n)==h for n,h in frozen.items())
 result={'passed':True,'reports':results,'source_inputs':inputs,'staged_sources':sources,'frozen_inputs':frozen,'node':subprocess.check_output(['node','--version'],text=True).strip(),
  'scope':'Actual tunnel TCP/UDP, SIP parser, registrar and UAC methods; VM-originated packets are fixtures. No QEMU, DSP, DOS, installed services or physical hardware.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
