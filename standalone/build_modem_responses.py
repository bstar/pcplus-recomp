#!/usr/bin/env python3
"""Source-only matcher diagnostic;138 matcher +576 unlinked attempt baseline bytes."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'build/modem-responses';out.mkdir(parents=True,exist_ok=True)
module=ROOT/'reconstruction/modem_responses';proof=json.loads((module/'provenance.json').read_text());core=module/'match.asm'
for index,r in enumerate(proof['ranges']):
 source=module/r['source'];flat=out/f'baseline-{index}.bin'
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(flat)],check=True)
 b=flat.read_bytes();assert len(b)==r['size'] and hashlib.sha256(b).hexdigest()==r['sha256']
# Preserve real attempt instructions as a relocatable object with explicit imports.
# No fake UI/serial implementations are linked merely to satisfy those imports.
subprocess.run(['nasm','-f','obj','-DMODEM_RESPONSES_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(module/'attempt.asm'),'-o',str(out/'attempt-unlinked.obj')],check=True)
sources=[core,module/'bounded.asm',module/'classify.asm',module/'state.asm',ROOT/'standalone/modem_responses_host.asm'];objects=[]
for i,p in enumerate(sources):
 obj=out/f'unit{i}.obj';objects.append(str(obj));subprocess.run(['nasm','-f','obj','-DMODEM_RESPONSES_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(p),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'modem_responses.map'),'name',str(out/'MODEMRSP.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-modem-response-match-diagnostic','binary_sha256':hashlib.sha256((out/'MODEMRSP.EXE').read_bytes()).hexdigest(),'baseline_ranges':proof['ranges'],'unlinked_sources':['reconstruction/modem_responses/attempt.asm'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[module/'attempt.asm',module/'provenance.json',ROOT/'reconstruction/uart/encodings.inc']},'limitations':['Response matcher and bounded byte feed only; no serial, timeout or complete dialing subsystem.','Raw recovered near ABI remains unsafe for malformed input; caller should use bounded wrapper.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built MODEMRSP.EXE;138 matcher +576 unlinked attempt baseline bytes exact')
