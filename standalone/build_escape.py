#!/usr/bin/env python3
"""Assemble exact escape baseline and link an explicitly isolated callback fixture."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/escape';out.mkdir(parents=True,exist_ok=True)
core=ROOT/'reconstruction/ansi/escape.asm';proof=json.loads((core.parent/'escape-provenance.json').read_text())
subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/', '-o',str(out/'baseline.bin'),str(core)],check=True)
baseline=(out/'baseline.bin').read_bytes()
assert len(baseline)==proof['size'] and hashlib.sha256(baseline).hexdigest()==proof['sha256']
objects=[];sources=[core,ROOT/'standalone/escape_host.asm']
for i,source in enumerate(sources):
 obj=out/f'unit-{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DANSI_OMF','-I',str(ROOT/'reconstruction/uart')+'/', '-o',str(obj),str(source)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'escape.map'),'name',str(out/'ESCAPE.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'isolated-source-only-escape-control-flow-fixture','binary_sha256':hashlib.sha256((out/'ESCAPE.EXE').read_bytes()).hexdigest(),'baseline_sha256':proof['sha256'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc',core.parent/'escape-provenance.json']},'limitations':['Fixture records screen/application calls; it does not implement their behavior.','Parameter parser/transition/dispatcher return fixture tokens; this test does not prove end-to-end CSI parsing.','Original legacy loops are unchanged.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built isolated escape fixture; 477 baseline bytes match')
