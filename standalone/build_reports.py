#!/usr/bin/env python3
"""Build recovered reports and maintained formatter with explicit output capture."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/reports';out.mkdir(parents=True,exist_ok=True)
core=ROOT/'reconstruction/reports/core.asm';proof=json.loads((core.parent/'provenance.json').read_text())
for i,r in enumerate(proof['ranges']):
 dest=out/f'baseline-{i}.bin'
 subprocess.run(['nasm','-f','bin',f'-DREPORTS_REGION={i}','-I',str(ROOT/'reconstruction/uart')+'/', '-o',str(dest),str(core)],check=True)
 data=dest.read_bytes();assert len(data)==r['size'] and hashlib.sha256(data).hexdigest()==r['sha256']
objects=[];sources=[core,ROOT/'src/reports/decimal.asm',ROOT/'src/reports/data.asm',ROOT/'standalone/reports_host.asm']
for i,source in enumerate(sources):
 obj=out/f'unit-{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DREPORTS_OMF','-I',str(ROOT/'reconstruction/uart')+'/', '-o',str(obj),str(source)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'reports.map'),'name',str(out/'REPORTS.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-recovered-reports-with-maintained-decimal-and-captured-output','binary_sha256':hashlib.sha256((out/'REPORTS.EXE').read_bytes()).hexdigest(),'baseline_ranges':proof['ranges'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc',core.parent/'provenance.json']},'limitations':['Output capture is a fixture; these tests do not exercise live serial transmission.','Signed decimal and protocol resource layout are maintained sources, not original runtime source.','DA terminal IDs2..11 supported;0/1 empty placeholders, higher IDs invalid.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built recovered reporting fixture;176 baseline bytes match')
