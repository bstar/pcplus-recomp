#!/usr/bin/env python3
"""Stage a pinned menu-size proxy candidate; never change installed source/config."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
PINS={
 'src/telnet/TelnetProxy.js':'8ba4a0e1b9d4be1c51bc6d2f534e56e37528eed2d1915e58505fc2be88d99628',
 'src/telnet/TelnetCodec.js':'732b57d3134a1941e0f78f9c281d76f7b4d775ce11cf1c2cf1912804fb868f5e',
 'src/telnet/InputSequenceFramer.js':'00f00af6e692c42426f85121317117367e3ae43fae97f48f08d34252f90f850a',
 'src/logger.js':'9ce9d913744df9fb0f3c4c1573f683608c4de19e6c3e2ba475a8d91411d7f2a5',
 'COPYING':'0ed8b6028dc07428234531de5a5ec59c878ec622f599e4c353520a10be909cd9'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 runtime=a.runtime.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 inputs={str(p.relative_to(ROOT)):sha(p) for p in HERE.iterdir() if p.is_file()}
 for name,h in PINS.items():
  source=runtime/name;assert sha(source)==h,name
  for variant in ('stock','candidate'):
   dest=out/variant/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 for variant in ('stock','candidate'):shutil.copyfile(HERE/'fixture-config.js',out/variant/'config.js')
 shutil.copyfile(HERE/'WindowSizeReply.js',out/'candidate/src/telnet/WindowSizeReply.js')
 subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(HERE/'proxy.patch')],cwd=out/'candidate',check=True,capture_output=True)
 env=dict(os.environ,SYNTH_MENU_SIZE_STAGE=str(out))
 with (out/'tests.tap').open('w') as log:result=subprocess.run(['node','--test','--test-reporter=tap',str(HERE/'check.test.js')],stdout=log,stderr=subprocess.STDOUT,env=env)
 assert result.returncode==0,(out/'tests.tap').read_text()
 assert inputs=={str(p.relative_to(ROOT)):sha(p) for p in HERE.iterdir() if p.is_file()}
 assert all(sha(runtime/n)==h for n,h in PINS.items())
 report=dict(passed=True,installed_sources_unchanged=True,baseline=PINS,sources=inputs,candidate={n:sha(out/'candidate'/n) for n in ('src/telnet/TelnetProxy.js','src/telnet/WindowSizeReply.js')},test_log_sha256=sha(out/'tests.tap'),node=subprocess.check_output(['node','--version'],text=True).strip(),
  scope='Isolated actual patched proxy/reply collector and unchanged codec/framer. Deterministic socket/timer boundaries plus real loopback Telnet NAWS/data. Generic synthetic configuration only; no installed source/config/service, DOS/SIP/DSP/analog/BBS or physical acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS isolated pre-session size probe, lifecycle, NAWS and opaque data tests')
if __name__=='__main__':main()
