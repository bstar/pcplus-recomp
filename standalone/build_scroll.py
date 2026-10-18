#!/usr/bin/env python3
"""Build recovered scroll services without reading any original installation."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/scroll';OUT.mkdir(parents=True,exist_ok=True)
sources=[]
for module in ['screen','erase','scroll']:sources+=sorted((ROOT/'reconstruction'/module).glob('*.asm'))
sources+=[ROOT/'standalone/scroll_host.asm']
objects=[]
for source in sources:
 obj=OUT/(source.parent.name+'-'+source.stem+'.obj');objects.append(obj)
 subprocess.run(['nasm','-f','obj','-D'+source.parent.name.upper()+'_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'scroll.map'),'name',str(OUT/'SCROLL.EXE'),'file',','.join(map(str,objects))],check=True)
manifest={'kind':'source-only-recovered-scroll-diagnostic','binary_sha256':hashlib.sha256((OUT/'SCROLL.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc']},'limitations':['Actual scroll/linefeed/index/reverse-index code with unresolved viewport/complex attribute services trapped.','Full parser/renderer integration remains separate.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built',OUT/'SCROLL.EXE',manifest['binary_sha256'])
