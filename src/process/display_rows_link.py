"""Link namespaced recovered BIOS row services in an independent code bank.

This exposes the low-level owner only. No foreground key, parser or geometry
transaction may call it until the canonical screen/frame contract is integrated.
"""
import hashlib,json,re,subprocess
from pathlib import Path

def build_display_rows_bank(root,out,geometry=False,mouse=False):
 root=Path(root);out=Path(out)/'display-rows-bank';out.mkdir(parents=True,exist_ok=False)
 groups=[('display_modes',('detect','virtual_buffer','rows','fonts','font_reset','baseline')),
         ('program_display',('geometry',)),('program_ui',('scanlines','cursor_eight'))]
 inputs=[Path(__file__).resolve(),root/'src/process/native_display_rows.h',root/'reconstruction/uart/encodings.inc']
 selected=[];units=[]
 for group,names in groups:
  provenance=root/'reconstruction'/group/'provenance.json';inputs.append(provenance)
  records=json.loads(provenance.read_text())['units']
  if group=='display_modes':
   extra=root/'reconstruction/display_modes/capabilities-provenance.json';inputs.append(extra);records+=json.loads(extra.read_text())['units']
  for name in names:
   source=root/'reconstruction'/group/(name+'.asm');inputs.append(source)
   unit=next(u for u in records if Path(u.get('source',u.get('file'))).stem==name)
   selected.append((source,group));units.append(unit)
 glue=root/'src/process/native_display_rows.asm';owner=root/'src/process/native_display_rows.c';inputs+=[glue,owner]
 # Keep every native display_* code/data name private to this bank. C public
 # far entries and their _display_rows_* near-data imports remain distinct.
 symbols=set()
 for source in [*(p for p,_ in selected),glue]:
  for line in re.findall(r'^\s*(?:extern|global)\s+([^;\n]+)',source.read_text(),re.M):
   symbols.update(n.strip() for n in line.split(',') if n.strip().startswith('display_'))
 # State aliases are declared through field macro invocations, not globals.
 symbols.update(re.findall(r'^field\s+(display_\w+),',glue.read_text(),re.M))
 namespace={s:'drows_native_'+s for s in sorted(symbols)}
 aliases=['-D'+n+'='+v for n,v in namespace.items()]
 include='-I'+str(root/'reconstruction/uart')+'/'
 objects=[]
 for (source,group),unit in zip(selected,units):
  flat=out/(source.stem+'.bin');obj=out/(source.stem+'.obj')
  subprocess.run(['nasm','-fbin',include,str(source),'-o',str(flat)],check=True)
  assert flat.stat().st_size==unit['bytes'] and hashlib.sha256(flat.read_bytes()).hexdigest()==unit['sha256']
  subprocess.run(['nasm','-fobj',include,'-D'+('DISPLAY_MODES_OMF' if group=='display_modes' else 'PROGRAM_DISPLAY_OMF'),
   '-D_TEXT=DISPLAY_CODE','-DCODE=FARCODE',*aliases,str(source),'-o',str(obj)],check=True);objects.append(obj)
 obj=out/'owner-glue.obj';objects.append(obj)
 subprocess.run(['nasm','-fobj','-DDISPLAY_ROWS_BANK','-D_TEXT=DISPLAY_CODE','-DCODE=FARCODE',*aliases,str(glue),'-o',str(obj)],check=True)
 obj=out/'owner-c.obj';objects.append(obj)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-nt=DISPLAY_CODE','-nc=FARCODE',
  '-i='+str(root/'src/process'),'-fo='+str(obj),str(owner)],check=True)
 if geometry:
  source=root/'src/terminal/row_geometry.c';inputs += [source,root/'src/terminal/row_geometry.h',root/'src/terminal/status_transition.h']
  obj=out/'geometry-owner.obj';objects.append(obj)
  subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-nt=DISPLAY_CODE','-nc=FARCODE',
   *(['-dTERMINAL_ROW_MOUSE'] if mouse else []),'-i='+str(root/'src/process'),'-fo='+str(obj),str(source)],check=True)
 return dict(objects=objects,inputs=inputs,namespace=namespace,native_bytes=sum(u['bytes'] for u in units),
  scope=('Optional offline BIOS/canonical/RIS transaction with mouse suspension and rollback. No normal key/menu binding, online geometry, bridge coordination or physical acceptance.' if geometry else 'Optional low-level BIOS row bank only. Canonical terminal/RIS/frame/bridge transaction and key/menu bindings are not integrated; do not treat raw BIOS success as application geometry acceptance.'))
