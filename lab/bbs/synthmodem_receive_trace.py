#!/usr/bin/env python3
"""Capture existing guest PCM dumps during a real DSP burst/idle diagnostic."""
import argparse,gzip,json,os,shutil,signal,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha,records,archive
from synthmodem_sparse_runtime import validate

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--dmodem',choices=['baseline','candidate','buffered']);p.add_argument('--slmodem',choices=['baseline']);p.add_argument('--network-profile',choices=['direct','buffered-release','buffered-increase'],default='direct');a=p.parse_args()
 runtime=a.runtime.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 inputs=validate(runtime)
 names=['lab/bbs/synthmodem_receive_trace.py','lab/bbs/synthmodem_receive_trace.js','lab/bbs/receive_trace_export.sh',
  'lab/bbs/qemu_trace_wrapper.py','lab/bbs/synthmodem_sparse_runtime.py','lab/bbs/synthmodem_vm_control.py',
  'docs/validation/synthmodem-gateway.json','docs/validation/synthmodem-sparse.json','nix/flake.nix','nix/flake.lock','tools/modem-dev']
 built=None;elf=None;slmodem_build=None;slmodem_elf=None
 if a.dmodem:
  names+=['nix/dmodem.nix','tools/build-dmodem','docs/validation/synthmodem-jitter-policy.json']
  accepted=json.loads((ROOT/'docs/validation/synthmodem-jitter-policy.json').read_text());assert accepted['passed']
  built=json.loads(subprocess.check_output([str(ROOT/'tools/build-dmodem'),a.dmodem,'--no-link','--json'],text=True))
  helper=Path(built[0]['outputs']['out'])/'bin/d-modem'
  if a.dmodem=='buffered':
   reference=accepted['builds']['candidate']
   source_name='share/pcplus-dmodem/d-modem.c'
   reference_source=Path(reference['build']['outputs']['out'])/source_name
   assert sha(reference_source)==reference['source_sha256']
   expected_source=reference_source.read_bytes()
   for field in ('jb_min_pre','jb_max_pre','jb_init'):
    old=f'med_cfg.{field} = 40;'.encode();assert expected_source.count(old)==1
    expected_source=expected_source.replace(old,f'med_cfg.{field} = 200;'.encode())
   assert (helper.parent.parent/source_name).read_bytes()==expected_source
  else:assert sha(helper)==accepted['builds'][a.dmodem]['executable_sha256']
  elf=helper.read_bytes();assert elf[:5]==b'\x7fELF\x01' and int.from_bytes(elf[18:20],'little')==3
  assert 'INTERP' not in subprocess.check_output(['readelf','-l',str(helper)],text=True)
 if a.slmodem:
  names+=['nix/slmodem.nix','nix/slmodem-sources.json','tools/build-slmodem','docs/validation/synthmodem-slmodem-build.json']
  accepted=json.loads((ROOT/'docs/validation/synthmodem-slmodem-build.json').read_text());assert accepted['passed']
  slmodem_build=json.loads(subprocess.check_output([str(ROOT/'tools/build-slmodem'),a.slmodem,'--no-link','--json'],text=True));binary=Path(slmodem_build[0]['outputs']['out'])/'bin/slmodemd'
  assert sha(binary)==accepted['builds'][a.slmodem]['sha256'];slmodem_elf=binary.read_bytes()
 frozen={n:sha(ROOT/n) for n in names};staged=out/'runtime';shutil.copytree(runtime,staged)
 entries=records(gzip.decompress((runtime/'candidate.cpio.gz').read_bytes()));original=[(n,list(f),b) for n,f,b in entries]
 init='etc/init.d/S99modem-pjsip';found=0
 for i,(n,f,b) in enumerate(entries):
  if n==init:
   marker=b'    echo "S99modem-pjsip: starting backend B"';assert b.count(marker)==1
   entries[i]=(n,f,b.replace(marker,b'    /bin/sh /lab-trace-export.sh &\n'+marker));found+=1
  elif n=='usr/local/bin/d-modem' and elf is not None:entries[i]=(n,f,elf)
  elif n=='usr/local/bin/slmodemd' and slmodem_elf is not None:entries[i]=(n,f,slmodem_elf)
 assert found==1
 inode=max(f[0] for _,f,_ in entries)+1;export=(ROOT/'lab/bbs/receive_trace_export.sh').read_bytes()
 entries.append(('lab-trace-export.sh',[inode,0o100755,0,0,1,0,len(export),0,0,0,0,0,0],export));entries.append(('TRAILER!!!',[0]*13,b''))
 image=staged/'candidate.cpio.gz';image.write_bytes(gzip.compress(archive(entries),mtime=0))
 rebuilt=records(gzip.decompress(image.read_bytes()));assert len(rebuilt)==len(original)+1
 for (n,f,b),(nn,ff,bb) in zip(original,rebuilt):
  assert n==nn and f[:6]+f[7:]==ff[:6]+ff[7:]
  assert n==init or (n=='usr/local/bin/d-modem' and elf is not None and bb==elf) or (n=='usr/local/bin/slmodemd' and slmodem_elf is not None and bb==slmodem_elf) or b==bb,n
 if elf is not None:assert sum(n=='usr/local/bin/d-modem' and b==elf for n,_,b in rebuilt)==1
 if slmodem_elf is not None:assert sum(n=='usr/local/bin/slmodemd' and b==slmodem_elf for n,_,b in rebuilt)==1
 assert rebuilt[-1][0]=='lab-trace-export.sh' and rebuilt[-1][2]==export
 tested={str(p):sha(p) for p in staged.rglob('*') if p.is_file()}
 with (out/'node.log').open('w') as log:
  proc=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_receive_trace.js'),str(staged),str(out),a.network_profile],stdout=log,stderr=log,start_new_session=True)
  try:proc.wait(timeout=150)
  finally:
   if proc.poll() is None:
    os.killpg(proc.pid,signal.SIGTERM)
    try:proc.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
 r=json.loads((out/'node-result.json').read_text())
 r['checks']['immutable_inputs']=all(sha(Path(n))==h for n,h in {**inputs,**tested}.items()) and all(sha(ROOT/n)==h for n,h in frozen.items())
 r.update(runtime_inputs=inputs,tested_inputs=tested,frozen_inputs=frozen,producer_exit=proc.returncode,dmodem_variant=a.dmodem,dmodem_build=built,slmodem_variant=a.slmodem,slmodem_build=slmodem_build,
  captures_sha256={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.bin','.raw','.log','.jsonl')})
 r['passed']=proc.returncode==0 and all(r['checks'].values());(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
