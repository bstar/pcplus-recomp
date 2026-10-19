#!/usr/bin/env python3
"""Build exact reverse-tab instructions from source, without original inputs."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/keyboard-reverse-tab';OUT.mkdir(parents=True,exist_ok=True)
proof=json.loads((ROOT/'reconstruction/keyboard_reverse_tab/provenance.json').read_text())
source=ROOT/proof['units'][0]['file'];binary=OUT/'reverse_tab.bin'
subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(binary)],check=True)
assert hashlib.sha256(binary.read_bytes()).hexdigest()==proof['units'][0]['sha256']
left=ROOT/'reconstruction/screen/left.asm'
subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(left),'-o',str(OUT/'left-oracle.bin')],check=True)
screen=json.loads((ROOT/'reconstruction/screen/provenance.json').read_text())
unit=next(u for u in screen['units'] if u['file']=='reconstruction/screen/left.asm')
assert hashlib.sha256((OUT/'left-oracle.bin').read_bytes()).hexdigest()==unit['sha256']
subprocess.run(['nasm','-f','obj','-DKEYBOARD_REVERSE_TAB_OMF','-I',str(ROOT/'reconstruction/uart')+'/',str(source.relative_to(ROOT)),'-o',str(OUT/'reverse_tab.obj')],cwd=ROOT,check=True)
report=dict(passed=True,bytes=len(binary.read_bytes()),binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),original_inputs=[],sources={str(source.relative_to(ROOT)):hashlib.sha256(source.read_bytes()).hexdigest(), 'reconstruction/keyboard_reverse_tab/provenance.json':hashlib.sha256((ROOT/'reconstruction/keyboard_reverse_tab/provenance.json').read_bytes()).hexdigest()},scope='Exact flat native226-byte routine and relocatable OMF object. External callbacks are unresolved imports, not implementations; no production keyboard integration.')
report['sources']['reconstruction/screen/left.asm']=hashlib.sha256(left.read_bytes()).hexdigest()
report['sources']['reconstruction/screen/provenance.json']=hashlib.sha256((ROOT/'reconstruction/screen/provenance.json').read_bytes()).hexdigest()
report['left_oracle_sha256']=unit['sha256']
(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Reverse Tab:226 exact bytes and OMF PASS')
