#!/usr/bin/env python3
"""Passive actual DOS/VGA popup frames and exact screen/cursor restoration."""
import argparse,hashlib,json,os,re,struct,subprocess
from pathlib import Path
from build_meta_dialog import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('build','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();build=a.build.resolve();out=a.output.resolve();assert build.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 base=json.loads((build/'result.json').read_text());assert base['passed']
 for n,h in base['sources'].items():assert sha(ROOT/n)==h
 objects=[build/n for n in ('banks.obj','padding.obj','meta_text.obj','meta_dialog.obj')]
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/key_mapping'),'-fd=METAPOP.lnk','-fm=METAPOP.map','-fe=METAPOP.EXE',str(ROOT/'standalone/meta_dialog_demo.c'),*[str(p) for p in objects]],cwd=out,check=True)
 response=out/'METAPOP.lnk';response.write_text(response.read_text()+'\norder clname CODE clname PADCODE clname FARCODE clname FARSTATE clname BEGDATA clname DATA clname BSS clname STACK\n');subprocess.run(['wlink','@METAPOP.lnk'],cwd=out,check=True)
 listing=(out/'METAPOP.map').read_text();data=re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert data
 null=re.search(r'^_NULL\s+BEGDATA\s+DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I);assert null and data[1]==null[1]
 source=(ROOT/'standalone/path_editor_watch.asm').read_text()
 old=" cmp word [es:806],0x03b5\n jne .before\n cmp word [es:1126],0x034e\n jne .before"
 assert old in source
 source=source.replace(old," cmp word [es:1010],0x7152\n jne .before\n cmp word [es:1012],0x714f\n jne .before\n cmp word [es:2450],0x1f52\n jne .before")
 source=source.replace('D:\\EDITVIEW.BIN','C:\\EDITVIEW.BIN')
 (out/'WATCH.ASM').write_text(source);subprocess.run(['nasm','-fbin',str(out/'WATCH.ASM'),'-o',str(out/'WATCH.COM')],check=True)
 sampler='''BITS 16
CPU 8086
ORG 100h
mov ax,0xb800
mov ds,ax
xor si,si
push cs
pop es
mov di,frame
mov cx,2000
rep movsw
mov ax,0x40
mov ds,ax
mov ax,[0x50]
mov [es:geometry],ax
mov ax,[0x60]
mov [es:geometry+2],ax
push cs
pop ds
mov dx,name
mov cx,0
mov ah,0x3c
int 0x21
jc failed
mov bx,ax
mov dx,frame
mov cx,4004
mov ah,0x40
int 0x21
jc failed
cmp ax,4004
jne failed
mov ah,0x3e
int 0x21
jc failed
mov ax,0x4c00
int 0x21
failed: mov ax,0x4c01
int 0x21
name: db 'BEFORE.BIN',0
frame: times 4000 db 0
geometry: times 4 db 0
'''
 for leaf,filename in [('BEFORE','BEFORE.BIN'),('AFTER','AFTER.BIN')]:
  text=sampler.replace('BEFORE.BIN',filename);(out/(leaf+'.ASM')).write_text(text);subprocess.run(['nasm','-fbin',str(out/(leaf+'.ASM')),'-o',str(out/(leaf+'.COM'))],check=True)
 (out/'CHECK.BAT').write_text('@echo off\ncls\nBEFORE\nWATCH T\nADDKEY p900 r p700 enter p700 X p700 ins p700 escape p700 escape\nMETAPOP\nif errorlevel 1 goto failed\nAFTER\nWATCH\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{out}"\nc:\nCHECK.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=25)
 assert (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists()
 assert (out/'BEFORE.BIN').read_bytes()==(out/'AFTER.BIN').read_bytes()
 raw=(out/'EDITVIEW.BIN').read_bytes();assert len(raw)==32044
 magic,count,ticks,restored=struct.unpack_from('<4H',raw);assert magic==0x5056 and 5<=count<=8 and restored==1
 frames=[]
 for i in range(count):
  cur,shape=struct.unpack_from('<2H',raw,8+i*4004);frame=raw[12+i*4004:4012+i*4004];text=frame[::2]
  frames.append(dict(cursor=cur,shape=shape,field=text[505:555].hex(),frame_sha256=hashlib.sha256(frame).hexdigest()))
 checks=dict(overview=any(f['cursor']==0x110c for f in frames),kind_selection=any(f['cursor']==0x0611 for f in frames),text_edit=any(f['cursor']==0x0619 for f in frames),typed_text=any(bytes.fromhex(f['field']).startswith(b'XOW0') for f in frames),insert_shape=any(f['shape']==0x080f for f in frames),exact_screen_cursor_restore=True)
 # BIOS saved shape is independently sampled; use the same native end formula.
 saved_shape=struct.unpack_from('<H',(out/'BEFORE.BIN').read_bytes(),4002)[0];insert=((((saved_shape&255)//2)+1)<<8)|(saved_shape&255)
 checks['insert_shape']=any(f['shape']==insert for f in frames)
 data=(out/'RESULT.BIN').read_bytes()
 expected=b''.join(b'\x03\0ROW'+str(row).encode()+b'\0'+b'\xa5'*47 for row in range(10))
 assert len(data)==540 and data==expected
 checks['canceled_text_unchanged']=True;assert all(checks.values()),checks
 result=dict(passed=True,checks=checks,frames=frames,cpu='8086',demo_sha256=sha(out/'METAPOP.EXE'),controller_sha256=base['binary_sha256'],
  sources={n:sha(ROOT/n) for n in ('standalone/test_meta_dialog_vga.py','standalone/meta_dialog_demo.c','standalone/path_editor_watch.asm')},input_objects={str(p.relative_to(ROOT)):sha(p) for p in objects},artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()},
  scope='Actual source-built DOS8086 VGA prototype, synthetic definitions and passive timer observer. Owned window/cursor/text/shape transitions and exact screen restoration. Authored decoration, not original VGA equivalence; load/save deliberately fail without a persistence backend. No UART/live parent/physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS Meta popup actual VGA:',checks)


if __name__=='__main__':main()
