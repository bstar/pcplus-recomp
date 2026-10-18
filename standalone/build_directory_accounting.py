#!/usr/bin/env python3
"""Source-only bounded accounting diagnostic and exact unlinked original units."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-accounting';OUT.mkdir(parents=True,exist_ok=True)
module=ROOT/'reconstruction/directory_accounting';proof=json.loads((module/'provenance.json').read_text())
for n,r in enumerate(proof['ranges']):
 p=OUT/f'baseline{n}.bin'
 subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(module/r['source']),'-o',str(p)],check=True)
 raw=p.read_bytes();assert len(raw)==r['size'] and hashlib.sha256(raw).hexdigest()==r['sha256'],r['source']
 subprocess.run(['nasm','-fobj','-DDIRECTORY_ACCOUNTING_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(module/r['source']),'-o',str(OUT/(Path(r['source']).stem+'-unlinked.obj'))],check=True)
sources=[module/'patch.asm',ROOT/'standalone/directory_accounting_host.asm'];objects=[]
for p in sources:
 o=OUT/(p.stem+'.obj');objects.append(str(o));subprocess.run(['nasm','-fobj',str(p),'-o',str(o)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'directory_accounting.map'),'name',str(OUT/'DIRSTATS.EXE'),'file',','.join(objects)],check=True)
result={'kind':'source-only-directory-accounting-pure-diagnostic','binary_sha256':hashlib.sha256((OUT/'DIRSTATS.EXE').read_bytes()).hexdigest(),'exact_bytes':sum(r['size'] for r in proof['ranges']),'baseline_ranges':proof['ranges'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'limitations':['No file IO or UART. Original external date formatter/cache/FILE services remain unresolved OMF dependencies; exact units are assembled unlinked.','Maintained helper fixes original year-since1900 overflow with year modulo100; validates1980..2099 Gregorian date.']}
(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built DIRSTATS.EXE;',result['exact_bytes'],'exact unlinked original bytes')
