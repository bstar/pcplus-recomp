#!/usr/bin/env python3
"""Build recovered erase services without reading any original installation."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/erase';OUT.mkdir(parents=True,exist_ok=True)
sources=sorted((ROOT/'reconstruction/erase').glob('*.asm'))+[ROOT/'standalone/erase_host.asm']
objects=[]
for source in sources:
 obj=OUT/(source.stem+'.obj');objects.append(obj)
 subprocess.run(['nasm','-f','obj','-DERASE_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'erase.map'),'name',str(OUT/'ERASE.EXE'),'file',','.join(map(str,objects))],check=True)
manifest={'kind':'source-only-recovered-erase-diagnostic','binary_sha256':hashlib.sha256((OUT/'ERASE.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc']},'limitations':['Complex protected erase and attribute repair remain unresolved and trap in this diagnostic.','Ordinary rectangle/video operations recovered; full parser integration remains separate.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built',OUT/'ERASE.EXE',manifest['binary_sha256'])
