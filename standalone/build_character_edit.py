#!/usr/bin/env python3
"""Build recovered scroll services without reading any original installation."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/character-edit';OUT.mkdir(parents=True,exist_ok=True)
proof=json.loads((ROOT/'reconstruction/character_edit/provenance.json').read_text())
for unit in proof['units']:
 dest=OUT/(Path(unit['file']).stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/unit['file']),'-o',str(dest)],check=True)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==unit['sha256']
sources=[]
for module in ['screen','erase','scroll','text','character_edit']:sources+=sorted((ROOT/'reconstruction'/module).glob('*.asm'))
sources+=[ROOT/'standalone/character_edit_host.asm']
objects=[]
for source in sources:
 obj=OUT/(source.parent.name+'-'+source.stem+'.obj');objects.append(obj)
 subprocess.run(['nasm','-f','obj','-D'+source.parent.name.upper()+'_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'character_edit.map'),'name',str(OUT/'CHAREDIT.EXE'),'file',','.join(map(str,objects))],check=True)
manifest={'kind':'source-only-recovered-character-edit-diagnostic','binary_sha256':hashlib.sha256((OUT/'CHAREDIT.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc']},'limitations':['Actual insert/delete-character and tab-stop code; complex attribute repair explicitly trapped.','Full parser/renderer integration remains separate.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built',OUT/'CHAREDIT.EXE',manifest['binary_sha256'])
