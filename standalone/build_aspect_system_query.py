#!/usr/bin/env python3
"""Build exact DOS system query handlers from maintained source."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-system-query'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 fixture=ROOT/'standalone/fixtures/aspect_system_query_native_units.json'
 proof=json.loads(fixture.read_text());source=ROOT/'src/aspect/system_query.asm';units=[]
 for unit in proof['units']:
  output=OUT/(unit['name']+'.bin')
  subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/', '-DASPECT_SYSTEM_QUERY_FLAT','-DASPECT_SYSTEM_QUERY_UNIT='+str(unit['unit']),str(source),'-o',str(output)],check=True)
  assert output.stat().st_size==unit['bytes'] and sha(output)==unit['sha256'],unit
  units.append(dict(**unit,output=str(output.relative_to(ROOT))))
 obj=OUT/'system_query.obj'
 subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',str(source.relative_to(ROOT)),'-o',str(obj)],cwd=ROOT,check=True)
 report=dict(passed=True,original_inputs=[],units=units,native_bytes=sum(u['bytes'] for u in units),objects={str(obj.relative_to(ROOT)):sha(obj)},sources={str(p.relative_to(ROOT)):sha(p) for p in (source,fixture,Path(__file__).resolve(),ROOT/'reconstruction/uart/encodings.inc')})
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print('ASPECT system queries:',report['native_bytes'],'exact instruction bytes PASS')
if __name__=='__main__':main()
