#!/usr/bin/env python3
"""Build source-only DOS native-flow composition with real maintained file IO."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-file'
ASM_SOURCES=[
 ('flow','src/aspect/control_flow.asm',None),
 ('stack','src/aspect/value_stack.asm',None),
 ('copy','reconstruction/erase/move_bytes.asm','ERASE_OMF'),
 ('abort','src/aspect/abort.asm',None),
 ('setjmp','reconstruction/transfer_session/setjmp.asm','TRANSFER_SESSION_OMF'),
 ('longjmp','reconstruction/transfer_session/longjmp.asm','TRANSFER_SESSION_OMF'),
 ('fixture','standalone/aspect_file_fixture.asm',None),
]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main(owned_window=False,output=None):
 global OUT
 if output is not None:OUT=output.resolve()
 OUT.mkdir(parents=True,exist_ok=True)
 include='-I'+str(ROOT/'reconstruction/uart')+'/'
 objects=[];sources=[Path(__file__).resolve(),ROOT/'reconstruction/uart/encodings.inc',
  ROOT/'src/aspect/file_io.c',ROOT/'src/aspect/file_io.h',ROOT/'standalone/aspect_file_fixture.c']
 for name,rel,define in ASM_SOURCES:
  source=ROOT/rel;obj=OUT/(name+'.obj');sources.append(source)
  subprocess.run(['nasm','-f','obj',include]+(['-D'+define] if define else [])+
   [str(source),'-o',str(obj)],check=True);objects.append(str(obj))
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
  *(['-DASPECT_FILE_OWNED_WINDOW'] if owned_window else []),
  '-i='+str(ROOT/'src/aspect'),'-fm=FILE.map','-fe=FILE.EXE',
  str(ROOT/'standalone/aspect_file_fixture.c'),str(ROOT/'src/aspect/file_io.c'),*objects],cwd=OUT,check=True)
 report=dict(binary_sha256=sha(OUT/'FILE.EXE'),sources={str(p.relative_to(ROOT)):sha(p) for p in sources},
  original_inputs=[],owned_read_window=owned_window,scope='Native flow/read/frame/stack/abort composition backed by actual DOS stdio and maintained checked operand callbacks. Source-owned file fixture; no opcode loop or complete interpreter.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--owned-window',action='store_true');p.add_argument('--output',type=Path)
 a=p.parse_args();main(a.owned_window,a.output)
