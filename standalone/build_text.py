#!/usr/bin/env python3
"""Link source-only text helper diagnostic; baseline hashes need no original."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/text';out.mkdir(parents=True,exist_ok=True)
proof=json.loads((ROOT/'reconstruction/text/provenance.json').read_text())
objects=[];sources=[]
for unit in proof['units']:
 source=ROOT/unit['file'];sources.append(source);target=out/(source.stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(target)],check=True)
 assert hashlib.sha256(target.read_bytes()).hexdigest()==unit['sha256'] and len(target.read_bytes())==unit['bytes']
sources.extend([ROOT/'src/text/api.asm',ROOT/'standalone/text_host.asm'])
for index,source in enumerate(sources):
 obj=out/f'unit-{index}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DTEXT_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'text.map'),'name',str(out/'TEXT.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-dos-text-diagnostic','binary_sha256':hashlib.sha256((out/'TEXT.EXE').read_bytes()).hexdigest(),'baseline_regions':proof['units'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'limitations':['Host supplies video segment/status-port configuration; complete high-level character path not linked.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built build/text/TEXT.EXE; 201 recovered bytes match baseline hashes')
