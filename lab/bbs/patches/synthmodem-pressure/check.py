#!/usr/bin/env python3
"""Stage VM-writer/CallSession/proxy flow candidate; never start a VM/service."""
import argparse,hashlib,json,shutil,subprocess,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
REV='b1752e4d0039e0cff72735924e03aa99922723a8'
PINS={
 'src/backends/PjsipBackend.js':'2fcbaea78eaa91abd85cda71b4ab72de0716e60fab7aaf3fb48faa40dd12d550',
 'src/session/CallSession.js':'48364d12210aaa0fec7ed510abe2a04532f06c301a3e388dde50102b82ecbdb4',
 'vm/qemu-runner/wire.js':'756da9800874b12cd97197537671171283054a976461ced2e4928369e4baf4c3',
 'src/backends/at-result-line.js':'28d50f2744192ed21fad459a8f84ec73aaf8ea0144b82c73043a97abfa136c89',
 'src/telnet/TelnetProxy.js':'98efcb975e4fbe64303d7bb54820ccf8cf8199fe1fe8552272b00ce9c0993fd0',
 'src/logger.js':'9ce9d913744df9fb0f3c4c1573f683608c4de19e6c3e2ba475a8d91411d7f2a5',
 'config.js':'3d6d33a25b8d86cde88d02ae538846592a020e8d64063abdb231a6ba7b27d49e'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 telnet=HERE.parent/'synthmodem-telnet'
 tracked=[x for x in HERE.iterdir() if x.is_file()]+[telnet/'proxy.patch',telnet/'TelnetCodec.js',telnet/'check.js']
 inputs={str(x.relative_to(ROOT)):sha(x) for x in tracked}
 baseline=out/'baseline'
 for n,h in PINS.items():
  cache=ROOT/'build/bbs-lab/synthmodem-pressure-cache'/REV/n
  if not cache.exists():
   data=urllib.request.urlopen(f'https://raw.githubusercontent.com/synexo/synthmodem/{REV}/{n}',timeout=20).read()
   assert hashlib.sha256(data).hexdigest()==h;cache.parent.mkdir(parents=True,exist_ok=True);cache.write_bytes(data)
  assert sha(cache)==h,n
  target=baseline/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(cache,target)
 shutil.copytree(baseline,out/'stock')
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(telnet/'proxy.patch')],cwd=baseline,check=True)
 shutil.copyfile(telnet/'TelnetCodec.js',baseline/'src/telnet/TelnetCodec.js')
 ledger=json.loads((ROOT/'docs/validation/synthmodem-telnet.json').read_text())
 for n,h in ledger['candidate_sha256'].items():assert sha(baseline/n)==h,n
 candidate=out/'candidate';shutil.copytree(baseline,candidate)
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(HERE/'pressure.patch')],cwd=candidate,check=True)
 shutil.copyfile(HERE/'ControlWriter.js',candidate/'src/backends/ControlWriter.js')
 with (out/'checks.log').open('w') as log:
  run=subprocess.run(['node',str(HERE/'check.js'),str(out)],stdout=log,stderr=log,timeout=25)
 assert run.returncode==0,(out/'checks.log').read_text()
 checks=json.loads((out/'checks.json').read_text());(out/'checks.json').rename(out/'pressure-checks.json')
 with (out/'telnet-regression.log').open('w') as log:
  run=subprocess.run(['node',str(telnet/'check.js'),str(out)],stdout=log,stderr=log,timeout=25)
 assert run.returncode==0,(out/'telnet-regression.log').read_text()
 regression=json.loads((out/'checks.json').read_text());(out/'checks.json').rename(out/'telnet-checks.json')
 assert all(sha(ROOT/n)==h for n,h in inputs.items()),'Inputs changed'
 result={'passed':True,'upstream_revision':REV,'upstream_sha256':PINS,'lab_input_sha256':inputs,
  'node':subprocess.check_output(['node','--version'],text=True).strip(),
  'candidate_sha256':{str(x.relative_to(candidate)):sha(x) for x in candidate.rglob('*') if x.is_file()},
  'checks':checks,'telnet_regression':regression,
  'scope':'Actual source methods plus modeled sockets/SIP/RTP and a real loopback TCP path. No VM, DSP/audio, SIP service, DOS client or hardware.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
