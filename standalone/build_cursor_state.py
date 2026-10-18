#!/usr/bin/env python3
"""Build exact recovered save/restore with actual source-built screen services."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build/cursor-state';out.mkdir(parents=True,exist_ok=True)
core=ROOT/'reconstruction/cursor_state/core.asm';proof=json.loads((core.parent/'provenance.json').read_text())
subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(core),'-o',str(out/'baseline.bin')],check=True)
baseline=(out/'baseline.bin').read_bytes()
start=int(proof['ranges'][0]['start'],16)
for region in proof['ranges']:
 offset=int(region['start'],16)-start
 data=baseline[offset:offset+region['size']]
 assert len(data)==region['size'] and hashlib.sha256(data).hexdigest()==region['sha256']
sources=[core]+sorted((ROOT/'reconstruction/screen').glob('*.asm'))+[ROOT/'standalone/cursor_state_host.asm'];objects=[]
for i,source in enumerate(sources):
 obj=out/f'unit-{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DCURSOR_STATE_OMF','-DSCREEN_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(out/'cursor_state.map'),'name',str(out/'CSTATE.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'source-only-recovered-cursor-state-with-real-screen-services','binary_sha256':hashlib.sha256((out/'CSTATE.EXE').read_bytes()).hexdigest(),'baseline_ranges':proof['ranges'],'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'reconstruction/uart/encodings.inc',core.parent/'provenance.json']},'limitations':['Unknown live state semantics retain address-based names.','Unrecovered optional screen viewport/attribute/wrap helpers trap.','No text rendering or UART output is exercised.']}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built source-only CSTATE.EXE;144 exact recovered bytes')
