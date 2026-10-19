#!/usr/bin/env python3
"""Build exact native BREAK/setting/UI source units without original inputs."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-break-native'
FIXTURE=ROOT/'standalone/fixtures/aspect_break_native_units.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);units=json.loads(FIXTURE.read_text())['units'];source=ROOT/'src/aspect/break_commands.asm'
 for u in units:
  output=OUT/(u['name']+'.bin')
  subprocess.run(['nasm','-fbin','-Ireconstruction/uart/','-DASPECT_BREAK_FLAT','-DASPECT_BREAK_UNIT='+str(u['unit']),str(source.relative_to(ROOT)),'-o',str(output)],cwd=ROOT,check=True)
  assert output.stat().st_size==u['length'] and sha(output)==u['sha256'],(u,output.read_bytes().hex())
  u['file']=output.name
 obj=OUT/'break_commands.obj';subprocess.run(['nasm','-fobj','-Ireconstruction/uart/',str(source.relative_to(ROOT)),'-o',str(obj)],cwd=ROOT,check=True)
 inputs=[source,FIXTURE,Path(__file__),ROOT/'reconstruction/uart/encodings.inc']
 report=dict(original_inputs=[],units=units,native_bytes=sum(u['length'] for u in units),objects={obj.name:sha(obj)},sources={str(p.relative_to(ROOT)):sha(p) for p in inputs})
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Native BREAK exact source bytes:',report['native_bytes'])
if __name__=='__main__':main()
