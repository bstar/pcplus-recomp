#!/usr/bin/env python3
"""Actual DOS far-bank Chat frames versus recovered native renderer effects."""
import argparse
import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path
from chat_screen_native import NativePane

ROOT=Path(__file__).resolve().parents[1]
UNITS=[('reconstruction/chat/character.asm',0x3d94,272),('reconstruction/chat/bios_character.asm',0x6c4a,20),
       ('reconstruction/screen/left.asm',0x1e30,111),('reconstruction/screen/set_cursor.asm',0x1bbe,168),
       ('reconstruction/screen/cursor_pack.asm',0x6e66,17),('reconstruction/screen/cursor_output.asm',0x6e78,74)]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--original',type=Path)
    args=p.parse_args();out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir();drive=out/'drive';drive.mkdir()
    names=['src/chat/screen.c','src/chat/screen.h','src/chat/bank.asm','src/terminal/chat_owner.h',
           'standalone/chat_screen_host.c','standalone/test_chat_screen_dos.py','standalone/chat_screen_native.py',
           'reconstruction/uart/encodings.inc','reconstruction/chat/character-provenance.json','reconstruction/screen/provenance.json']+[n for n,_,_ in UNITS]
    sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}
    original=args.original.read_bytes() if args.original else None
    if original:assert hashlib.sha256(original).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    native={};screen_proof=json.loads((ROOT/'reconstruction/screen/provenance.json').read_text())
    chat_proof=json.loads((ROOT/'reconstruction/chat/character-provenance.json').read_text())
    for n,address,size in UNITS:
        path=out/(Path(n).stem+'.bin')
        subprocess.run(['nasm','-fbin','-DRECON_FLAT','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/n),'-o',str(path)],check=True)
        code=path.read_bytes();assert len(code)==size
        digest=hashlib.sha256(code).hexdigest()
        expected=chat_proof['sha256'] if address==0x3d94 else chat_proof['bios_character']['sha256'] if address==0x6c4a else next(u['sha256'] for u in screen_proof['units'] if u['file']==n)
        assert digest==expected,n
        if original:assert code==original[address+0x1200:address+0x1200+size],n
        native[address]=code
    for n in ('reconstruction/chat/character.asm','reconstruction/chat/bios_character.asm'):
        subprocess.run(['nasm','-fobj','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/n),'-o',str(out/(Path(n).stem+'.obj'))],check=True)
    for n,obj,flags in [('src/chat/screen.c','screen.obj',['-nt=CHAT_CODE','-nc=FARCODE']),('standalone/chat_screen_host.c','host.obj',[])]:
        subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_BANK',*flags,'-fo='+obj,str(ROOT/n)],cwd=drive,check=True)
    subprocess.run(['nasm','-fobj',str(ROOT/'src/chat/bank.asm'),'-o','bank.obj'],cwd=drive,check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-k8192','-fe=SCREEN.EXE','-fm=SCREEN.MAP','bank.obj','host.obj','screen.obj'],cwd=drive,check=True)
    scenarios=[]
    for rows in (25,28,43,50):
        sequence=[]
        for kind in (0,1):sequence.extend((kind,0xa500+b,0,0,0) for b in range(256))
        sequence.extend((3,b,0,0,0) for b in range(256))
        sequence.extend((4,b,0,0,0) for b in (0,1,8,9,10,13,27,128,255))
        divider=33 if rows>28 else 19
        for which,first,last in ((0,1,divider-1),(1,divider+1,rows-2)):
            for row in (first,last):
                for col in (0,1,7,8,72,78,79):
                    sequence.extend((which,b,1,row,col) for b in (8,9,10,13,65,255))
        # Sustained wraps and pane scrolling, interleaved local/remote traffic.
        sequence.extend((i%2,65+i%26,0,0,0) for i in range(200))
        sequence.extend((2,b,0,0,0) for b in b'\x00END\r\n\t\x08')
        scenarios.append((rows,0x17,0x71,0x17,sequence))
    scenarios.append((25,0x8e,0x4f,0x07,[(i%2,b,0,0,0) for i,b in enumerate(b'COLOR\r\n\t\x08\x80\xff'*20)]))
    operations=0
    with (drive/'ORACLE.BIN').open('wb') as f:
        f.write(struct.pack('<H',len(scenarios)))
        for rows,attr,bar,clear,sequence in scenarios:
            oracle=NativePane(native,rows,attr,bar,clear)
            f.write(struct.pack('<5H',rows,attr,bar,clear,len(sequence)))
            def snapshot():
                f.write(struct.pack('<'+'H'*len(oracle.frame),*oracle.frame))
                f.write(struct.pack('<4H',*oracle.panes[0][2:],*oracle.panes[1][2:]))
            snapshot()
            for kind,value,position,row,col in sequence:
                which=int(kind==1)
                if position:oracle.panes[which][2:]=[row,col]
                f.write(struct.pack('<5H',kind,value,position,row,col))
                if kind<2:oracle.put(kind,value)
                elif kind!=4:
                    b=(value*37+1)&255 if kind==3 else value
                    if b:oracle.put(0,b)
                snapshot();operations+=1
    config=out/'dosbox.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nSCREEN >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=drive,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=120)
    assert result.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),(drive/'RESULT.TXT').read_text()
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in sources.items())
    report=dict(passed=True,cases=len(scenarios),complete_frames=operations+len(scenarios),native_bytes=662,
                native_original_compared=bool(original),context_bytes=30,cpu='8086',rows=[25,28,43,50],sources=sources,
                artifacts={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},
                scope='DOS8086 far-bank renderer and far frame/state versus native662-byte CPU reference. BIOS09/02 and scroll2530 are explicit narrow/single-width modeled boundaries. Full cells and both pane cursors compare after every operation. Layout is based on original static contract, not an original screenshot. No live parent/serial/BBS/physical or viewport/double-width/reverse-wrap equivalence.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS Chat screen DOS:',operations+len(scenarios),'complete frames')


if __name__=='__main__':main()
