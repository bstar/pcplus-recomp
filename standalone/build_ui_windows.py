#!/usr/bin/env python3
"""Source-only exact cell snapshots plus separately maintained bounded windows."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/ui-windows';out.mkdir(parents=True,exist_ok=True)
proof=json.loads((ROOT/'reconstruction/ui_windows/provenance.json').read_text())
sources=[]
for unit in proof['units']:
 source=ROOT/unit['file'];sources.append(source);target=out/(source.stem+'.bin')
 subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(target)],check=True)
 assert len(target.read_bytes())==unit['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest()==unit['sha256']
sources.extend([ROOT/'reconstruction/ui_windows/bounded.asm',ROOT/'reconstruction/text/packed.asm',ROOT/'reconstruction/text/fill.asm',ROOT/'reconstruction/text/cga_sync.asm',ROOT/'standalone/ui_windows_host.asm'])
objects=[]
for i,source in enumerate(sources):
 obj=out/f'unit-{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DUI_WINDOWS_OMF','-DTEXT_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'ui_windows.map'),'name',str(out/'WINDOWS.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-recovered-text-snapshots-plus-maintained-bounds','binary_sha256':hashlib.sha256((out/'WINDOWS.EXE').read_bytes()).hexdigest(),'exact_recovered_bytes':sum(u['bytes'] for u in proof['units']),'baseline_regions':proof['units'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'limitations':['Bounded rectangular API is maintained source, not original recovery.','Caller owns buffer allocation, nonoverlap and separate cursor/terminal state.','CGA waits preserve original unbounded hardware polling.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built source-only WINDOWS.EXE;',sum(u['bytes'] for u in proof['units']),'exact recovered bytes')
