#!/usr/bin/env python3
"""Build exact original KEY-action units with explicit diagnostic service fixtures."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'reconstruction/meta_keys';OUT=ROOT/'build/meta-keys';OUT.mkdir(parents=True,exist_ok=True)
proof=json.loads((CORE/'provenance.json').read_text())
for unit in proof['units']:
 path=ROOT/unit['file'];target=OUT/(path.stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(target)],check=True)
 assert hashlib.sha256(target.read_bytes()).hexdigest()==unit['sha256'],path
sources=sorted(CORE.glob('*.asm'))+[ROOT/'standalone/meta_keys_host.asm'];objects=[]
for i,source in enumerate(sources):
 obj=OUT/f'unit{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DMETA_KEYS_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'meta_keys.map'),'name',str(OUT/'METAKEYS.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-recovered-KEY-action-diagnostic','binary_sha256':hashlib.sha256((OUT/'METAKEYS.EXE').read_bytes()).hexdigest(),'exact_original_bytes':sum(u['bytes'] for u in proof['units']),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[CORE/'provenance.json']},'limitations':['ASPECT/program/UI fixtures only record arguments; resolver fixture returns input unchanged. No external program execution claimed.','Exact original caret and TEXT stack buffers remain unbounded; production must use separately maintained bounded/nonblocking layer.','Blocking actual BIOS tick wait and calibrated pacing preserved.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built METAKEYS.EXE;',manifest['exact_original_bytes'],'exact recovered bytes')
