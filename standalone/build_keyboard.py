#!/usr/bin/env python3
"""Build source-only keyboard MZ and verify original four flat region hashes."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/keyboard';out.mkdir(parents=True,exist_ok=True)
core=ROOT/'reconstruction/keyboard/core.asm'
proof=json.loads((core.parent/'provenance.json').read_text())
for i,region in enumerate(proof['ranges']):
 target=out/f'baseline-{i}.bin'
 subprocess.run(['nasm','-f','bin',f'-DKEYBOARD_REGION={i}','-I',str(ROOT/'reconstruction/uart')+'/', '-o',str(target),str(core)],check=True)
 data=target.read_bytes()
 assert len(data)==region['size'] and hashlib.sha256(data).hexdigest()==region['sha256'],region
sources=[core,ROOT/'standalone/keyboard_host.asm',ROOT/'src/keyboard/api.asm']
objects=[]
for i,source in enumerate(sources):
 obj=out/f'unit-{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DKEYBOARD_OMF','-I',str(ROOT/'reconstruction/uart')+'/', '-o',str(obj),str(source)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'keyboard.map'),'name',str(out/'KEYBOARD.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-dos-keyboard-diagnostic','binary_sha256':hashlib.sha256((out/'KEYBOARD.EXE').read_bytes()).hexdigest(),'baseline_regions':proof['ranges'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc',core.parent/'provenance.json']},'limitations':['Does not reconstruct terminal-emulation-specific outbound sequences.','Queue producer and debug callback are not recovered; host callback only counts invocations.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built build/keyboard/KEYBOARD.EXE; 231 recovered bytes match baseline hashes')
