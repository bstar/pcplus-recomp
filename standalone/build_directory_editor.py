#!/usr/bin/env python3
"""Build the maintained editor with maintained far buffers and recovered packed-cell services."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-editor';OUT.mkdir(parents=True,exist_ok=True)
sources=[ROOT/'src/terminal/directory_editor.asm',ROOT/'standalone/directory_editor_host.asm']
sources += [ROOT/'src/terminal/ui_screen_far.asm']
sources += [ROOT/'reconstruction/ui_windows'/f'{name}.asm' for name in ('save','restore','read_byte','read_packed')]
sources += [ROOT/'reconstruction/text/packed.asm',ROOT/'reconstruction/text/cga_sync.asm']
objects=[]
for i,source in enumerate(sources):
 obj=OUT/f'unit-{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DUI_WINDOWS_OMF','-DTEXT_OMF','-I',str(ROOT/'src/terminal')+'/', '-I',str(ROOT/'src/directory')+'/', '-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'editor.map'),'name',str(OUT/'EDITOR.EXE'),'file',','.join(objects)],check=True)
manifest={'kind':'maintained-source-only-DOS-record-editor-with-far-snapshots','binary_sha256':hashlib.sha256((OUT/'EDITOR.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'src/directory/directory_dos.inc']},'ABI':'terminal_directory_edit(record_DS_offset) nearcdecl caller2, AX0cancel/1accept; DS=SS DF0 BP/SI/DI/ES preserved; caller114bytes mutateonlyF10; noDOS/file/UARTIO','ownership':'Maintained UI/private114stage; Native packed cells in private far snapshots. Active80coltextmode2/3/7,screen/cursor/shape/oldsegment restored. Passwordmaskonly;date/calls/tails readonly.'}
manifest['sources']['src/terminal/trap_wait.inc']=hashlib.sha256((ROOT/'src/terminal/trap_wait.inc').read_bytes()).hexdigest()
manifest['sources']['src/terminal/ui_storage.inc']=hashlib.sha256((ROOT/'src/terminal/ui_storage.inc').read_bytes()).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built source-only EDITOR.EXE',manifest['binary_sha256'])
