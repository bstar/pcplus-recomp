#!/usr/bin/env python3
"""Build actual mode handlers with relocated tables and actual cursor services."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/modes';out.mkdir(parents=True,exist_ok=True)
core=ROOT/'reconstruction/modes/core.asm';proof=json.loads((core.parent/'provenance.json').read_text())
subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(core),'-o',str(out/'baseline.bin')],check=True)
baseline=(out/'baseline.bin').read_bytes();start=int(proof['ranges'][0]['start'],16)
for r in proof['ranges']:
 off=int(r['start'],16)-start;data=baseline[off:off+r['size']]
 assert len(data)==r['size'] and hashlib.sha256(data).hexdigest()==r['sha256']
sources=[core]+sorted((ROOT/'reconstruction/screen').glob('*.asm'))+[ROOT/'standalone/modes_host.asm'];objects=[]
for i,source in enumerate(sources):
 obj=out/f'unit-{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DMODES_OMF','-DSCREEN_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'modes.map'),'name',str(out/'MODES.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-recovered-modes-with-real-cursor-and-explicit-dependencies','binary_sha256':hashlib.sha256((out/'MODES.EXE').read_bytes()).hexdigest(),'baseline_ranges':proof['ranges'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc',core.parent/'provenance.json']},'limitations':['Unrecovered mode side-effect services trap; no silent implementations.','Original mode handlers assume validated parameter count and storage.','Ordinary mode6 links real BIOS cursor services; optional screen dependencies trap.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built source-only MODES.EXE;492 exact recovered bytes')
