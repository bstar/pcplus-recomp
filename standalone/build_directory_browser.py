#!/usr/bin/env python3
"""Build the maintained chooser with real recovered snapshots and DOS reader."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-browser';OUT.mkdir(parents=True,exist_ok=True)
sources=[ROOT/'src/terminal/directory_browser.asm',ROOT/'standalone/directory_browser_host.asm']
sources += [ROOT/'reconstruction/ui_windows'/f'{name}.asm' for name in ('save','restore','read_byte','read_packed')]
sources += [ROOT/'reconstruction/text/packed.asm',ROOT/'reconstruction/text/cga_sync.asm']
objects=[]
for i,source in enumerate(sources):
 obj=OUT/f'unit-{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DUI_WINDOWS_OMF','-DTEXT_OMF','-I',str(ROOT/'src/directory')+'/', '-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
source=ROOT/'src/directory/directory_dos.c';obj=OUT/'reader.obj';objects.append(str(obj))
subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-i='+str(ROOT/'src/directory'),'-fo='+str(obj),str(source)],cwd=OUT,check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'browser.map'),'name',str(OUT/'BROWSER.EXE'),'file',','.join(objects),'library',str(Path(os.environ['WATCOM'])/'lib286/dos/clibs.lib')],check=True)
manifest={'kind':'source-only-maintained-directory-browser-with-real-DOS-reader-and-recovered-snapshots','binary_sha256':hashlib.sha256((OUT/'BROWSER.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[source,ROOT/'src/directory/directory_dos.inc',ROOT/'src/directory/directory_dos.h']},'ABI':{'terminal_directory_choose':'AX0 selected/1cancel/2IOorvideoerror; DS=SS,DF0; BP/SI/DI/ES preserved; noUART; selectioncommitsonlyEnter','video':'80columntext modes2/3/7; activepageoffset readfromBDA004e; screen,cursor,shape,previousvideo_segmentrestored','display':'10rowpages; boundedname24/number20; control0..31+127sanitize; highCP437preserved; neverpassword/script/KEY/META'},'limitations':['Maintained UI, not original modal window reconstruction.','Reader opens explicitly selectedfile read-only; no configurations or defaults created.','Record semantics and dialing occur later in caller.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built source-only BROWSER.EXE',manifest['binary_sha256'])
