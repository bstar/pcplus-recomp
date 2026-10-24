#!/usr/bin/env python3
"""Build the native width adapter and an explicit reset-boundary DOS observer."""
from pathlib import Path
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out=ROOT/'build/width-request';out.mkdir(parents=True,exist_ok=True)
source=ROOT/'reconstruction/modes/width_request.asm'
proof=ROOT/'reconstruction/modes/width_request_provenance.json'
metadata=json.loads(proof.read_text())
include=ROOT/'reconstruction/uart/encodings.inc'
subprocess.run(['nasm','-fbin','-I'+str(include.parent)+'/',str(source),'-o',str(out/'baseline.bin')],check=True)
assert (out/'baseline.bin').stat().st_size==metadata['bytes']and sha(out/'baseline.bin')==metadata['sha256']
inputs=[source,ROOT/'standalone/width_request_host.asm'];objects=[]
for index,path in enumerate(inputs):
    obj=out/f'unit-{index}.obj';objects.append(str(obj))
    subprocess.run(['nasm','-fobj','-DWIDTH_REQUEST_OMF','-I'+str(include.parent)+'/',str(path),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'width.map'),
                'name',str(out/'WIDTH.EXE'),'file',','.join(objects)],check=True)
inputs += [include,proof,Path(__file__).resolve()]
result=dict(kind='native-width-request-with-explicit-reset-observer',binary_sha256=sha(out/'WIDTH.EXE'),
            original_inputs=[],baseline_sha256=metadata['sha256'],sources={str(p.relative_to(ROOT)):sha(p)for p in inputs},
            scope='34 native adapter bytes; synthetic reset observer, not live geometry or terminal integration.')
(out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print('Built source-only WIDTH.EXE; 34 native adapter bytes')
