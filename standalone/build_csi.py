#!/usr/bin/env python3
"""Link real escape/parameter/dispatch/attribute/cursor/report code in a DOS diagnostic."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/csi';out.mkdir(parents=True,exist_ok=True)
sources=[ROOT/'reconstruction/ansi'/name for name in ['escape.asm','parameters.asm','transition.asm','dispatch.asm']]
sources+=sorted((ROOT/'reconstruction/attributes').glob('*.asm'))
sources+=sorted((ROOT/'reconstruction/screen').glob('*.asm'))
sources+=sorted((ROOT/'reconstruction/erase').glob('*.asm'))
sources+=[ROOT/'reconstruction/reports/core.asm',ROOT/'src/reports/decimal.asm',ROOT/'src/reports/data.asm']
sources+=[ROOT/'src/ansi/decimal.asm',ROOT/'standalone/csi_host.asm']
objects=[]
for index,source in enumerate(sources):
 obj=out/f'unit-{index}.obj';objects.append(str(obj))
 options=['-DANSI_OMF'] if source.parent.name=='ansi' and source.parent.parent.name=='reconstruction' else []
 if source.parent.name=='attributes':options=['-DATTRIBUTES_OMF']
 if source.parent.name=='screen':options=['-DSCREEN_OMF']
 if source.parent.name=='erase':options=['-DERASE_OMF']
 if source.parent.name=='reports' and source.parent.parent.name=='reconstruction':options=['-DREPORTS_OMF']
 subprocess.run(['nasm','-f','obj',*options,'-I',str(ROOT/'reconstruction/uart')+'/',
                 '-I',str(ROOT/'reconstruction/ansi')+'/', '-o',str(obj),str(source)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'csi.map'),
                'name',str(out/'CSI.EXE'),'file',','.join(objects)],check=True)
inputs=sources+[ROOT/'reconstruction/uart/encodings.inc',ROOT/'reconstruction/ansi/dispatch-layout.inc']
manifest={'kind':'combined-source-only-csi-cursor-attribute-report-erase-diagnostic',
 'binary_sha256':hashlib.sha256((out/'CSI.EXE').read_bytes()).hexdigest(),
 'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
 'limitations':['Actual recovered parser/dispatcher/cursor/attribute/report/erase instructions are linked together.',
 'Unrecovered application/scroll/viewport/protected-attribute services fail fast; this is not a complete terminal.',
 'Input/output memory fixtures replace a modem and ordinary text rendering is not present.',
 'Maintained CSI-q selects the historical TECH_NET behavior; CSI-X defaults zero/omitted counts and clamps to row bounds.',
 'Reports use maintained signed-decimal/protocol data; supported primary-attribute profiles are IDs2..11.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built build/csi/CSI.EXE',manifest['binary_sha256'],flush=True)
