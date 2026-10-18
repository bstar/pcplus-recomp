#!/usr/bin/env python3
"""Source-only exact BDA keyboard detection and maintained preserved wrapper."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/keyboard-detection';OUT.mkdir(parents=True,exist_ok=True)
module=ROOT/'reconstruction/keyboard_detection';proof=json.loads((module/'provenance.json').read_text())
baseline=OUT/'baseline.bin';source=module/'detect.asm'
subprocess.run(['nasm','-fbin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(baseline)],check=True)
raw=baseline.read_bytes();assert len(raw)==36 and hashlib.sha256(raw).hexdigest()==proof['sha256']
objects=[];sources=[source,ROOT/'standalone/keyboard_detection_host.asm']
for path in sources:
 obj=OUT/(path.stem+'.obj');objects.append(str(obj));subprocess.run(['nasm','-fobj','-DKEYBOARD_DETECTION_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(path),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'keyboard_detection.map'),'name',str(OUT/'KBDMODE.EXE'),'file',','.join(objects)],check=True)
result={'kind':'source-only-keyboard-BDA-detection-diagnostic','binary_sha256':hashlib.sha256((OUT/'KBDMODE.EXE').read_bytes()).hexdigest(),'exact_original_bytes':36,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[module/'provenance.json']},'limitations':['Read-only physical0496 bit4 detection reproduces original; no enhancedINT16 call is probed.','A BIOS with unreliable BDA flags may require manualSTANDARD override; physical XT/AT not tested.']};(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n');print('Built KBDMODE.EXE;36 exact original bytes')
