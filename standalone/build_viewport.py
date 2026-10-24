#!/usr/bin/env python3
"""Build native viewport controls and the DS-restoring maintained variant."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out=ROOT/'build/viewport';out.mkdir(parents=True,exist_ok=True)
proof=ROOT/'reconstruction/viewport/provenance.json';p=json.loads(proof.read_text())
include=ROOT/'reconstruction/uart/encodings.inc'
for unit in p['units']:
    source=ROOT/unit['file'];dest=out/(source.stem+'.bin')
    subprocess.run(['nasm','-fbin','-I'+str(include.parent)+'/',str(source),'-o',str(dest)],check=True)
    assert dest.stat().st_size==unit['bytes']and sha(dest)==unit['sha256']
sources=[ROOT/u['file']for u in p['units']]+[ROOT/'reconstruction/ui_windows'/n for n in ['cga_blank.asm','cga_unblank.asm']]+[ROOT/'standalone/viewport_host.asm']
products={}
for variant,fixed in [('VIEWPORT',True),('CONTROL',False)]:
    objects=[]
    for index,source in enumerate(sources):
        obj=out/f'{variant}-{index}.obj';objects.append(str(obj))
        flags=['-DVIEWPORT_OMF','-DUI_WINDOWS_OMF']+(['-DVIEWPORT_PRESERVE_DS']if fixed else[])
        subprocess.run(['nasm','-fobj',*flags,'-I'+str(include.parent)+'/',str(source),'-o',str(obj)],check=True)
    subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/(variant+'.map')),
                    'name',str(out/(variant+'.EXE')),'file',','.join(objects)],check=True)
    products[variant+'.EXE']=sha(out/(variant+'.EXE'))
sources += [proof,include,Path(__file__).resolve()]
manifest=dict(original_inputs=[],products=products,sources={str(s.relative_to(ROOT)):sha(s)for s in sources},
              recovered_bytes=183,scope='Native pane-copy/switch instructions, real recovered CGA helpers and source-owned far-buffer fixture. Maintained copy restores DS before unblank; no allocator/live width integration.')
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built viewport native control and maintained DS-restoring product')
