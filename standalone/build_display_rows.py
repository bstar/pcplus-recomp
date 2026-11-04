#!/usr/bin/env python3
"""Build recovered BIOS row/font services and their maintained bounded owner."""
import argparse, hashlib, json, subprocess
from pathlib import Path
from omf_imports import records as omf_records,externals
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 groups=[('display_modes',('detect','virtual_buffer','rows','fonts','font_reset','baseline')),
         ('program_display',('geometry',)),('program_ui',('scanlines','cursor_eight'))]
 objects=[];sources=[Path(__file__).resolve(),ROOT/'standalone/omf_imports.py',ROOT/'reconstruction/uart/encodings.inc'];units=[]
 include='-I'+str(ROOT/'reconstruction/uart')+'/'
 for group,names in groups:
  provenance=ROOT/'reconstruction'/group/'provenance.json'
  records=json.loads(provenance.read_text())['units'];sources.append(provenance)
  if group=='display_modes':
   extra=ROOT/'reconstruction/display_modes/capabilities-provenance.json';records+=json.loads(extra.read_text())['units'];sources.append(extra)
  for name in names:
   source=ROOT/'reconstruction'/group/(name+'.asm');sources.append(source)
   unit=next(u for u in records if Path(u.get('source',u.get('file'))).stem==name);units.append(unit)
   flat=out/(name+'.bin');obj=out/(name+'.obj')
   subprocess.run(['nasm','-fbin',include,str(source),'-o',str(flat)],check=True)
   assert flat.stat().st_size==unit['bytes'] and sha(flat)==unit['sha256'],name
   subprocess.run(['nasm','-fobj',include,'-D'+('DISPLAY_MODES_OMF' if group=='display_modes' else 'PROGRAM_DISPLAY_OMF'),str(source),'-o',str(obj)],check=True);objects.append(str(obj))
 for relative in ['src/process/native_display_rows.asm','standalone/display_rows_observer.asm']:
  source=ROOT/relative;sources.append(source);obj=out/(source.stem+'.obj')
  subprocess.run(['nasm','-fobj',str(source),'-o',str(obj)],check=True);objects.append(str(obj))
 c_sources=[ROOT/'src/process/native_display_rows.c',ROOT/'standalone/display_rows_diagnostic.c']
 sources+=c_sources+[ROOT/'src/process/native_display_rows.h']
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k4096','-i='+str(ROOT/'src/process'),
  '-fm=ROWS.map','-fe=ROWS.EXE',*[str(s) for s in c_sources],*objects],cwd=out,check=True)
 owner_imports=[n.decode('ascii') for kind,payload,_ in omf_records((out/'native_display_rows.o').read_bytes()) if kind==0x8c for n,_ in externals(payload)]
 assert all(n.startswith('_display_rows_') or n in ('_native_display_rows_probe','_small_code_') for n in owner_imports),owner_imports
 report=dict(passed=True,original_inputs=[],binary_sha256=sha(out/'ROWS.EXE'),native_bytes=sum(u['bytes'] for u in units),
  sources={str(s.relative_to(ROOT)):sha(s) for s in sources},units=units,owner_imports=owner_imports,
  scope='Standalone recovered native capability/geometry/row/font component with maintained bounded API. Diagnostic INT10 observer can refuse one font request. No terminal/parser/reset/frame/bridge integration, deployed package or physical acceptance.')
 (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built ROWS.EXE:',report['native_bytes'],'recovered bytes')
if __name__=='__main__':main()
