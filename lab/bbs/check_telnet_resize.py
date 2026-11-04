#!/usr/bin/env python3
"""Apply the staged codec patch in ignored storage; never alter the installed bridge."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
BASELINE='732b57d3134a1941e0f78f9c281d76f7b4d775ce11cf1c2cf1912804fb868f5e'

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 source=a.runtime.resolve()/'src/telnet/TelnetCodec.js';assert sha(source)==BASELINE,'Installed codec changed; review and rebase the patch before testing'
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 target=out/'src/telnet/TelnetCodec.js';target.parent.mkdir(parents=True);target.write_bytes(source.read_bytes())
 baseline=out/'baseline.js';baseline.write_bytes(source.read_bytes())
 patch=ROOT/'lab/bbs/patches/synthmodem-window-size/codec.patch'
 command=['git','apply','--directory='+str(out.relative_to(ROOT)),str(patch)]
 subprocess.run([*command[:2],'--check',*command[2:]],cwd=ROOT,check=True);subprocess.run(command,cwd=ROOT,check=True)
 assert sha(source)==BASELINE and sha(target)!=BASELINE
 env=dict(os.environ,SYNTHMODEM_CODEC_UNDER_TEST=str(target),SYNTHMODEM_CODEC_BASELINE=str(baseline))
 log=out/'tests.tap'
 with log.open('w') as f:result=subprocess.run(['node','--test',str(ROOT/'lab/bbs/check_telnet_resize.test.js')],env=env,stdout=f,stderr=subprocess.STDOUT)
 assert result.returncode==0,log.read_text()
 assert sha(source)==BASELINE
 record=dict(passed=True,installed_source_unchanged=True,installed_codec_sha256=BASELINE,patched_codec_sha256=sha(target),patch_sha256=sha(patch),test_log_sha256=sha(log),
  sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__).resolve(),ROOT/'lab/bbs/check_telnet_resize.test.js',patch)},
  scope='Isolated Telnet-only resize API; actual patched codec instructions and Node built-in tests. No serial payload scan, installed source/configuration/service change, PCPlus control/online integration, BBS/SIP/DSP/analog or physical acceptance. NAWS writes are advisory and are not BBS application acknowledgments.')
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS isolated NAWS resize, negotiation/refusal, FF escaping and binary/default-path regressions')
if __name__=='__main__':main()
