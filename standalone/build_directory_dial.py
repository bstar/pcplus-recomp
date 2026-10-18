#!/usr/bin/env python3
"""Source-only original quickdial and maintained bounded number helper diagnostic."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-dial';OUT.mkdir(parents=True,exist_ok=True);module=ROOT/'reconstruction/directory_dial';proof=json.loads((module/'provenance.json').read_text())
for n,r in enumerate(proof['ranges']):
 p=OUT/f'baseline{n}.bin';subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(module/r['source']),'-o',str(p)],check=True);b=p.read_bytes();assert len(b)==r['size'] and hashlib.sha256(b).hexdigest()==r['sha256']
linked=[module/x for x in ['expand_original.asm','uppercase.asm','length.asm','integer.asm','append.asm','bounded.asm']]+[ROOT/'standalone/directory_dial_host.asm'];objects=[]
for n,p in enumerate(linked):
 o=OUT/f'unit{n}.obj';objects.append(str(o));subprocess.run(['nasm','-fobj','-DDIRECTORY_DIAL_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(p),'-o',str(o)],check=True)
subprocess.run(['nasm','-fobj','-DDIRECTORY_DIAL_OMF',str(module/'apply_fragment.asm'),'-o',str(OUT/'apply-unlinked.obj')],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'directory_dial.map'),'name',str(OUT/'DIRDIAL.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-directory-dial-expansion-diagnostic','binary_sha256':hashlib.sha256((OUT/'DIRDIAL.EXE').read_bytes()).hexdigest(),'baseline_ranges':proof['ranges'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in linked+[module/'apply_fragment.asm',module/'provenance.json',ROOT/'reconstruction/uart/encodings.inc']},'limitations':['No live directory/PRM, UART or settings mutation. Original quickdial uses explicit synthetic in-memory record reader.','Field-apply original fragment is assembled unlinked; requires actual port services.','Maintained pure number helper rejects overflow instead of original60-byte truncation.']};(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built DIRDIAL.EXE;',sum(x['size'] for x in proof['ranges']),'exact baseline bytes')
