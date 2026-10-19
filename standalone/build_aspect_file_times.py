#!/usr/bin/env python3
"""Build exact native timestamp core/parsers/helpers, reusing native decimal CRT."""
import json,subprocess
from pathlib import Path
from build_aspect_conversion_services import ROOT,UNITS,sha
OUT=ROOT/'build/aspect-file-times'
def main():
 OUT.mkdir(parents=True,exist_ok=True);fixture=ROOT/'standalone/fixtures/aspect_file_time_native_units.json';proof=json.loads(fixture.read_text());units=[]
 for unit in proof['units']:
  output=OUT/(unit['name']+'.bin')
  subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/', '-DASPECT_FILE_TIMES_FLAT','-DASPECT_FILE_TIMES_UNIT='+str(unit['unit']),str(ROOT/'src/aspect/file_times.asm'),'-o',str(output)],check=True)
  assert output.stat().st_size==unit['bytes'] and sha(output)==unit['sha256'],unit
  units.append(dict(**unit,output=str(output.relative_to(ROOT))))
 for index in (1,6):
  name,start,end,digest=UNITS[index-1];output=OUT/('crt-'+name+'.bin')
  subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/', '-DASPECT_CONVERSION_SERVICES_FLAT','-DASPECT_CONVERSION_SERVICES_UNIT='+str(index),str(ROOT/'src/aspect/conversion_services.asm'),'-o',str(output)],check=True)
  assert output.stat().st_size==end-start and sha(output)==digest
  units.append(dict(name='crt-'+name,start=start,end=end,bytes=end-start,file_start=start+0x1200,sha256=digest,output=str(output.relative_to(ROOT)),reused=True))
 obj=OUT/'file_times.obj';source=ROOT/'src/aspect/file_times.asm'
 subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',str(source.relative_to(ROOT)),'-o',str(obj)],cwd=ROOT,check=True)
 sources=[source,fixture,ROOT/'src/aspect/conversion_services.asm',ROOT/'standalone/build_aspect_conversion_services.py',Path(__file__).resolve(),ROOT/'reconstruction/uart/encodings.inc']
 report=dict(passed=True,original_inputs=[],units=units,native_bytes=sum(u['bytes'] for u in proof['units']),reused_bytes=sum(u['bytes'] for u in units if u.get('reused')),objects={str(obj.relative_to(ROOT)):sha(obj)},sources={str(p.relative_to(ROOT)):sha(p) for p in sources})
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('File times:',report['native_bytes'],'exact bytes +',report['reused_bytes'],'reused PASS')
if __name__=='__main__':main()
