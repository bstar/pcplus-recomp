#!/usr/bin/env python3
"""Build original-free native end drain and actual mapped receive wrappers."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-end-wait-native';FIXTURE=ROOT/'standalone/fixtures/aspect_end_wait_native.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);source='src/aspect/end_wait.asm';u=json.loads(FIXTURE.read_text())['unit'];out=OUT/'end_wait.bin';u['file']=out.name
 subprocess.run(['nasm','-fbin','-Ireconstruction/uart/','-DASPECT_END_WAIT_FLAT',source,'-o',str(out)],cwd=ROOT,check=True);assert out.stat().st_size==u['length'] and sha(out)==u['sha256']
 obj=OUT/'end_wait.obj';subprocess.run(['nasm','-fobj','-Ireconstruction/uart/',source,'-o',str(obj)],cwd=ROOT,check=True)
 helpers=[]
 for unit,start,end in [(1,0x4c3c,0x4c4f),(2,0x4c74,0x4cb4)]:
  out=OUT/('receive-'+str(unit)+'.bin');subprocess.run(['nasm','-fbin','-Ireconstruction/uart/','-DASPECT_RECEIVE_POLICY_FLAT','-DASPECT_RECEIVE_POLICY_UNIT='+str(unit),'src/aspect/receive_policy.asm','-o',str(out)],cwd=ROOT,check=True)
  assert out.stat().st_size==end-start;helpers.append(dict(start=start,end=end,file=out.name,sha256=sha(out)))
 paths=[ROOT/source,FIXTURE,Path(__file__),ROOT/'src/aspect/receive_policy.asm',ROOT/'reconstruction/translation/receive.asm',ROOT/'reconstruction/uart/encodings.inc']
 (OUT/'manifest.json').write_text(json.dumps(dict(original_inputs=[],unit=u,helpers=helpers,objects={obj.name:sha(obj)},sources={str(p.relative_to(ROOT)):sha(p) for p in paths}),indent=2)+'\n');print('Built',u['length'],'nativeendwaitbytes +',sum(e['end']-e['start'] for e in helpers),'mappedreceivebytes')
if __name__=='__main__':main()
