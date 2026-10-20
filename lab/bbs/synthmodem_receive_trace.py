#!/usr/bin/env python3
"""Capture existing guest PCM dumps during a real DSP burst/idle diagnostic."""
import argparse,gzip,json,os,shutil,signal,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha,records,archive
from synthmodem_sparse_runtime import validate

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 runtime=a.runtime.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 inputs=validate(runtime)
 names=['lab/bbs/synthmodem_receive_trace.py','lab/bbs/synthmodem_receive_trace.js','lab/bbs/receive_trace_export.sh',
  'lab/bbs/qemu_trace_wrapper.py','lab/bbs/synthmodem_sparse_runtime.py','lab/bbs/synthmodem_vm_control.py',
  'docs/validation/synthmodem-gateway.json','docs/validation/synthmodem-sparse.json','nix/flake.nix','nix/flake.lock','tools/modem-dev']
 frozen={n:sha(ROOT/n) for n in names};staged=out/'runtime';shutil.copytree(runtime,staged)
 entries=records(gzip.decompress((runtime/'candidate.cpio.gz').read_bytes()));original=[(n,list(f),b) for n,f,b in entries]
 init='etc/init.d/S99modem-pjsip';found=0
 for i,(n,f,b) in enumerate(entries):
  if n==init:
   marker=b'    echo "S99modem-pjsip: starting backend B"';assert b.count(marker)==1
   entries[i]=(n,f,b.replace(marker,b'    /bin/sh /lab-trace-export.sh &\n'+marker));found+=1
 assert found==1
 inode=max(f[0] for _,f,_ in entries)+1;export=(ROOT/'lab/bbs/receive_trace_export.sh').read_bytes()
 entries.append(('lab-trace-export.sh',[inode,0o100755,0,0,1,0,len(export),0,0,0,0,0,0],export));entries.append(('TRAILER!!!',[0]*13,b''))
 image=staged/'candidate.cpio.gz';image.write_bytes(gzip.compress(archive(entries),mtime=0))
 rebuilt=records(gzip.decompress(image.read_bytes()));assert len(rebuilt)==len(original)+1
 for (n,f,b),(nn,ff,bb) in zip(original,rebuilt):
  assert n==nn and f[:6]+f[7:]==ff[:6]+ff[7:]
  assert n==init or b==bb,n
 assert rebuilt[-1][0]=='lab-trace-export.sh' and rebuilt[-1][2]==export
 tested={str(p):sha(p) for p in staged.rglob('*') if p.is_file()}
 with (out/'node.log').open('w') as log:
  proc=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_receive_trace.js'),str(staged),str(out)],stdout=log,stderr=log,start_new_session=True)
  try:proc.wait(timeout=150)
  finally:
   if proc.poll() is None:
    os.killpg(proc.pid,signal.SIGTERM)
    try:proc.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
 r=json.loads((out/'node-result.json').read_text())
 r['checks']['immutable_inputs']=all(sha(Path(n))==h for n,h in {**inputs,**tested}.items()) and all(sha(ROOT/n)==h for n,h in frozen.items())
 r.update(runtime_inputs=inputs,tested_inputs=tested,frozen_inputs=frozen,producer_exit=proc.returncode,
  captures_sha256={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.bin','.raw','.log','.jsonl')})
 r['passed']=proc.returncode==0 and all(r['checks'].values());(out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
