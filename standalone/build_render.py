#!/usr/bin/env python3
"""Link source-only render helper diagnostic; baseline hashes need no original."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/render';out.mkdir(parents=True,exist_ok=True)
proof=json.loads((ROOT/'reconstruction/render/provenance.json').read_text())
objects=[];sources=[]
for unit in proof['units']:
 source=ROOT/unit['file'];sources.append(source);target=out/(source.stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(target)],check=True)
 assert hashlib.sha256(target.read_bytes()).hexdigest()==unit['sha256'] and len(target.read_bytes())==unit['bytes']
sources+=sorted((ROOT/'reconstruction/text').glob('*.asm'))
for module in ['screen','erase','scroll']:sources+=sorted((ROOT/'reconstruction'/module).glob('*.asm'))
sources.append(ROOT/'standalone/render_host.asm')
for index,source in enumerate(sources):
 obj=out/f'unit-{index}.obj';objects.append(str(obj))
 define='-D'+source.parent.name.upper()+'_OMF'
 subprocess.run(['nasm','-f','obj',define,'-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'render.map'),'name',str(out/'RENDER.EXE'),'file',','.join(objects)],check=True)
inputs=sources+[ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/render/provenance.json']
manifest={'kind':'source-only-dos-highlevel-render-diagnostic','binary_sha256':hashlib.sha256((out/'RENDER.EXE').read_bytes()).hexdigest(),'baseline_regions':proof['units'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'limitations':['Host supplies video segment/status-port configuration; unsupported mode372c/font/complex-attribute/viewport services fail fast.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built build/render/RENDER.EXE; 646 recovered bytes match baseline hashes')
