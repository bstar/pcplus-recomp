#!/usr/bin/env python3
"""Build recovered cursor-shape services without reading any original installation."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/cursor-shape';OUT.mkdir(parents=True,exist_ok=True)
sources=sorted((ROOT/'reconstruction/cursor_shape').glob('*.asm'))+[ROOT/'standalone/cursor_shape_host.asm']
objects=[]
for source in sources:
 obj=OUT/(source.stem+'.obj');objects.append(obj)
 subprocess.run(['nasm','-f','obj','-DCURSOR_SHAPE_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'cursor-shape.map'),'name',str(OUT/'CURSOR.EXE'),'file',','.join(map(str,objects))],check=True)
manifest={'kind':'source-only-recovered-cursor-shape-diagnostic','binary_sha256':hashlib.sha256((OUT/'CURSOR.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc']},'limitations':['Actual BIOS shape and visibility code; requires valid font scanline configuration.','Physical adapter and complete terminal-mode integration remain separate.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built',OUT/'CURSOR.EXE',manifest['binary_sha256'])
