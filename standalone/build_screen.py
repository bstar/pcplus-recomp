#!/usr/bin/env python3
"""Build recovered cursor services without reading any original installation."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/screen';OUT.mkdir(parents=True,exist_ok=True)
sources=sorted((ROOT/'reconstruction/screen').glob('*.asm'))+[ROOT/'standalone/screen_host.asm']
objects=[]
for source in sources:
 obj=OUT/(source.stem+'.obj');objects.append(obj)
 subprocess.run(['nasm','-f','obj','-DSCREEN_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'screen.map'),'name',str(OUT/'SCREEN.EXE'),'file',','.join(map(str,objects))],check=True)
manifest={'kind':'source-only-recovered-cursor-diagnostic','binary_sha256':hashlib.sha256((OUT/'SCREEN.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc']},'limitations':['Cursor operations only; unresolved viewport/attribute-boundary/wrap services trap in this diagnostic.','Does not implement screen rendering, scrolling or all CSI commands.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built',OUT/'SCREEN.EXE',manifest['binary_sha256'])
