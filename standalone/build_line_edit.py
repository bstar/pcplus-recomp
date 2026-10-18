#!/usr/bin/env python3
"""Build recovered scroll services without reading any original installation."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/line-edit';OUT.mkdir(parents=True,exist_ok=True)
proof=json.loads((ROOT/'reconstruction/line_edit/provenance.json').read_text())
for unit in proof['units']:
 dest=OUT/(Path(unit['file']).stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/unit['file']),'-o',str(dest)],check=True)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==unit['sha256']
sources=[]
for module in ['screen','erase','scroll','line_edit']:sources+=sorted((ROOT/'reconstruction'/module).glob('*.asm'))
sources+=[ROOT/'standalone/line_edit_host.asm']
objects=[]
for source in sources:
 obj=OUT/(source.parent.name+'-'+source.stem+'.obj');objects.append(obj)
 subprocess.run(['nasm','-f','obj','-D'+source.parent.name.upper()+'_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'line_edit.map'),'name',str(OUT/'LINES.EXE'),'file',','.join(map(str,objects))],check=True)
manifest={'kind':'source-only-recovered-line-edit-diagnostic','binary_sha256':hashlib.sha256((OUT/'LINES.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc']},'limitations':['Actual insert/delete-line and wait-control-N code; UART/keyboard wait-loop fixtures explicit; complex attribute repair trapped.','Full parser/renderer integration remains separate.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built',OUT/'LINES.EXE',manifest['binary_sha256'])
