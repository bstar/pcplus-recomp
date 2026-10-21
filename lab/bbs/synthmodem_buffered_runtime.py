#!/usr/bin/env python3
"""Stage normal post-training startup with only the 200ms d-modem candidate."""
import argparse,gzip,json,shutil,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha,records,archive
from synthmodem_posttrain_validation import validate as validate_normal
from check_buffered_dmodem_build import verify

REFERENCE=ROOT/'build/bbs-lab/synthmodem-posttrain-runtime-01/runtime'


def validate(runtime,proof):
 runtime=Path(runtime).resolve();proof=Path(proof).resolve()
 assert runtime.is_relative_to(ROOT/'build') and proof.is_relative_to(ROOT/'build')
 r=json.loads(proof.read_text());assert r['passed'] and r['stage_only']
 assert r['stager_sha256']==sha(Path(__file__))
 assert r['builder_checker_sha256']==sha(ROOT/'lab/bbs/check_buffered_dmodem_build.py')
 assert r['reference_inputs']==validate_normal(REFERENCE)
 assert r['buffered_build']==verify([r['buffered_build']['build']])
 assert {str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()}==set(r['files'])
 assert all(sha(runtime/n)==h for n,h in r['files'].items())
 return {str(runtime/n):h for n,h in r['files'].items()}


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 reference=validate_normal(REFERENCE)
 built=json.loads(subprocess.check_output([str(ROOT/'tools/build-dmodem'),'buffered','--no-link','--json'],text=True));identity=verify(built)
 helper=Path(identity['executable']);out.mkdir(parents=True);runtime=out/'runtime';shutil.copytree(REFERENCE,runtime)
 old=records(gzip.decompress((REFERENCE/'candidate.cpio.gz').read_bytes()));new=[]
 for name,fields,body in old:new.append((name,list(fields),helper.read_bytes() if name=='usr/local/bin/d-modem' else body))
 image=runtime/'candidate.cpio.gz';image.write_bytes(gzip.compress(archive(new+[('TRAILER!!!',[0]*13,b'')]),mtime=0))
 actual=records(gzip.decompress(image.read_bytes()));assert len(actual)==len(old);changed=[]
 for (name,fields,body),(other,metadata,data) in zip(old,actual):
  assert name==other and fields[:6]+fields[7:]==metadata[:6]+metadata[7:]
  if data!=body:changed.append(name);assert data==helper.read_bytes()
 assert changed==['usr/local/bin/d-modem']
 files={str(p.relative_to(runtime)):sha(p) for p in runtime.rglob('*') if p.is_file()}
 assert set(files)=={str(Path(n).relative_to(REFERENCE)) for n in reference}
 assert [n for n,h in files.items() if h!=sha(REFERENCE/n)]==['candidate.cpio.gz']
 assert reference==validate_normal(REFERENCE)
 result=dict(passed=True,stage_only=True,compatibility_accepted=False,reference_inputs=reference,buffered_build=identity,
  files=files,changed_archive_entries=changed,stager_sha256=sha(Path(__file__)),builder_checker_sha256=sha(ROOT/'lab/bbs/check_buffered_dmodem_build.py'),
  scope='Normal post-training runtime with only d-modem replaced by the source-verified200ms DISCARD_NONE build. Exact archive metadata, all other bodies, kernel, JavaScript and normal init are preserved. No PCM exporter/chardev. Stage identity only; DOS/audio/BBS/physical acceptance remains separate.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert validate(runtime,out/'result.json')
 print(json.dumps(dict(passed=True,runtime=str(runtime),changed_archive_entries=changed)))


if __name__=='__main__':main()
