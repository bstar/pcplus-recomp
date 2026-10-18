#!/usr/bin/env python3
"""Optional original-required audit, never an input to the source-only build."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
image=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
manifest=json.loads((ROOT/'reconstruction/scroll/provenance.json').read_text())
assert hashlib.sha256(image).hexdigest()==manifest['source_sha256']
with tempfile.TemporaryDirectory() as directory:
 for unit in manifest['units']:
  output=Path(directory)/(Path(unit['file']).stem+'.bin')
  subprocess.run(['nasm','-f','bin','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/unit['file']),'-o',str(output)],check=True)
  assert output.read_bytes()==image[unit['source_file_offset']:unit['source_file_offset']+unit['bytes']],unit['file']
  assert hashlib.sha256(output.read_bytes()).hexdigest()==unit['sha256']
  print(unit['file'],unit['bytes'],'bytes exact')
print('Verified',sum(u['bytes'] for u in manifest['units']),'original bytes')
