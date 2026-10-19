#!/usr/bin/env python3
"""Original-free FETCH build reusing recovered DD9C/DD68 source helpers."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-fetch-native';FIXTURE=ROOT/'standalone/fixtures/aspect_fetch_native_units.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);units=json.loads(FIXTURE.read_text())['units'];sources={}
 for u in units:
  p=ROOT/u['source'];sources[u['source']]=sha(p);out=OUT/(u['name']+'.bin');u['file']=out.name
  subprocess.run(['nasm','-fbin','-Ireconstruction/uart/',*u['defines'],u['source'],'-o',str(out)],cwd=ROOT,check=True)
  assert out.stat().st_size==u['length'] and sha(out)==u['sha256'],u
 objects={}
 for source in ['fetch_command','break_cursor_read']:
  out=OUT/(source+'.obj');subprocess.run(['nasm','-fobj','-Ireconstruction/uart/','src/aspect/'+source+'.asm','-o',str(out)],cwd=ROOT,check=True);objects[out.name]=sha(out)
 for p in [FIXTURE,Path(__file__),ROOT/'reconstruction/uart/encodings.inc']:sources[str(p.relative_to(ROOT))]=sha(p)
 (OUT/'manifest.json').write_text(json.dumps(dict(original_inputs=[],native_bytes=sum(u['length'] for u in units),units=units,objects=objects,sources=sources),indent=2)+'\n');print('FETCH/helpers/cursor107exactbytes built')
if __name__=='__main__':main()
