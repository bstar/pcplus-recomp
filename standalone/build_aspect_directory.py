#!/usr/bin/env python3
"""Build original-free exact36B directory getter component and OMF object."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-directory';SOURCE=ROOT/'src/aspect/directory_builtins.asm'
EXPECTED={1:bytes.fromhex('a182e4c3'),2:b''.join(bytes([0xb8])+p.to_bytes(2,'little')+bytes([0xc3]) for p in [0xe68d,0xe6af,0xe6a6,0xe650,0xe6b9,0xe669,0xe69b,0xe684])}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);units=[]
 for number,expected in EXPECTED.items():
  target=OUT/f'unit{number}.bin';subprocess.run(['nasm','-f','bin','-DASPECT_DIRECTORY_FLAT',f'-DASPECT_DIRECTORY_UNIT={number}',str(SOURCE),'-o',str(target)],check=True)
  assert target.read_bytes()==expected;units.append(dict(unit=number,sha256=sha(target),bytes=len(expected)))
 subprocess.run(['nasm','-f','obj',str(SOURCE),'-o',str(OUT/'directory.obj')],check=True)
 report=dict(original_inputs=[],source_sha256=sha(SOURCE),builder_sha256=sha(Path(__file__)),units=units,object_sha256=sha(OUT/'directory.obj'),bytes=36)
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built36 exact directory getter bytes + OMF')
if __name__=='__main__':main()
