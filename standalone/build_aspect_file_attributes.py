#!/usr/bin/env python3
"""Exact attribute commands/helpers plus reused native attribute parser/formatter."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-file-attributes'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);fixture=ROOT/'standalone/fixtures/aspect_file_attributes_native_units.json';proof=json.loads(fixture.read_text());units=[]
 shared=ROOT/'standalone/fixtures/aspect_enumeration_native_units.json'
 reused=[u for u in json.loads(shared.read_text())['units'] if u['unit'] in (3,4)]
 for unit in proof['units']+reused:
  reuse=unit in reused;source=ROOT/'src/aspect'/('enumeration.asm' if reuse else 'file_attributes.asm');prefix='ASPECT_ENUM' if reuse else 'ASPECT_FILE_ATTRIBUTES'
  output=OUT/(('reused-' if reuse else '')+unit['name']+'.bin')
  subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/', '-D'+prefix+'_FLAT','-D'+prefix+'_UNIT='+str(unit['unit']),str(source),'-o',str(output)],check=True)
  assert output.stat().st_size==unit['bytes'] and sha(output)==unit['sha256'],unit
  units.append(dict(**unit,output=str(output.relative_to(ROOT)),reused=reuse))
 obj=OUT/'file_attributes.obj';source=ROOT/'src/aspect/file_attributes.asm'
 subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',str(source.relative_to(ROOT)),'-o',str(obj)],cwd=ROOT,check=True)
 report=dict(passed=True,original_inputs=[],units=units,native_bytes=sum(u['bytes'] for u in proof['units']),reused_bytes=sum(u['bytes'] for u in reused),objects={str(obj.relative_to(ROOT)):sha(obj)},sources={str(p.relative_to(ROOT)):sha(p) for p in (source,fixture,shared,ROOT/'src/aspect/enumeration.asm',Path(__file__).resolve(),ROOT/'reconstruction/uart/encodings.inc')})
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('File attributes:',report['native_bytes'],'exact bytes +',report['reused_bytes'],'reused PASS')
if __name__=='__main__':main()
