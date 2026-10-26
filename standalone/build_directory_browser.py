#!/usr/bin/env python3
"""Build the maintained chooser with maintained far buffers and recovered packed-cell services and DOS reader."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-browser';OUT.mkdir(parents=True,exist_ok=True)
sources=[ROOT/'src/terminal/directory_browser.asm',ROOT/'standalone/directory_browser_host.asm',ROOT/'src/terminal/directory_editor.asm',ROOT/'src/terminal/directory_edit_save.asm',ROOT/'reconstruction/directory_accounting/patch.asm']
sources += [ROOT/'src/terminal/ui_screen_far.asm']
sources += [ROOT/'reconstruction/ui_windows'/f'{name}.asm' for name in ('save','restore','read_byte','read_packed')]
sources += [ROOT/'reconstruction/text/packed.asm',ROOT/'reconstruction/text/cga_sync.asm']
objects=[]
for i,source in enumerate(sources):
 obj=OUT/f'unit-{i}.obj';objects.append(str(obj))
 subprocess.run(['nasm','-f','obj','-DUI_WINDOWS_OMF','-DTEXT_OMF','-I',str(ROOT/'src/terminal')+'/', '-I',str(ROOT/'src/directory')+'/', '-I',str(ROOT/'reconstruction/uart')+'/',str(source),'-o',str(obj)],check=True)
c_sources=[ROOT/'src/directory'/name for name in ('directory_dos.c','directory_actions.c','directory_replace.c','directory_replace_fs.c')]
for source in c_sources:
 obj=OUT/(source.stem+'.obj');objects.append(str(obj))
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-i='+str(ROOT/'src/directory'),'-fo='+str(obj),str(source)],cwd=OUT,check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'browser.map'),'name',str(OUT/'BROWSER.EXE'),'file',','.join(objects),'library',str(Path(os.environ['WATCOM'])/'lib286/dos/clibs.lib')],check=True)
manifest={'kind':'source-only-maintained-directory-browser-with-real-DOS-reader-and-far-snapshots','binary_sha256':hashlib.sha256((OUT/'BROWSER.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+c_sources+sorted((ROOT/'src/directory').glob('*.h'))+sorted((ROOT/'src/directory').glob('*.inc'))},'ABI':{'terminal_directory_choose':'AX0 selected/1cancel/2IOorvideoerror; DS=SS,DF0; BP/SI/DI/ES preserved; noUART; selectioncommitsonlyEnter','video':'80columntext modes2/3/7; activepageoffset readfromBDA004e; screen,cursor,shape,previousvideo_segmentrestored','display':'10rowpages; boundedname24/number20; control0..31+127sanitize; highCP437preserved; neverpassword/script/KEY/META'},'limitations':['Maintained browser/editor UI, not original modal window reconstruction.','Page reads are read-only. Explicit editor acceptance can replace the selected DIR through validated staging and backup; no configurations or defaults are created.','Dialing and live record compatibility checks occur later in the caller. Replacement does not guarantee crash atomicity or concurrent-writer exclusion.']}
manifest['sources']['src/terminal/trap_wait.inc']=hashlib.sha256((ROOT/'src/terminal/trap_wait.inc').read_bytes()).hexdigest()
manifest['sources']['src/terminal/ui_storage.inc']=hashlib.sha256((ROOT/'src/terminal/ui_storage.inc').read_bytes()).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built source-only BROWSER.EXE',manifest['binary_sha256'])
