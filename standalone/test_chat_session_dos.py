#!/usr/bin/env python3
"""DOS composed Chat: incoming panes/history/log progress while TX is refused."""
import argparse
import hashlib
import json
import os
import struct
import subprocess
from pathlib import Path
from check_chat_native import execute
from chat_screen_native import NativePane
from test_chat_screen_dos import UNITS

ROOT=Path(__file__).resolve().parents[1]
NAMES=['src/chat/session.c','src/chat/session.h','src/chat/screen.c','src/chat/screen.h',
       'src/chat/bank.asm','src/terminal/chat_owner.c','src/terminal/chat_owner.h',
       'standalone/chat_session_host.c','standalone/test_chat_session_dos.py',
       'standalone/check_chat_native.py','standalone/chat_screen_native.py','standalone/test_chat_screen_dos.py',
       'reconstruction/chat/chat.asm','reconstruction/chat/provenance.json',
       'reconstruction/chat/character-provenance.json','reconstruction/screen/provenance.json',
       'reconstruction/uart/encodings.inc']+[n for n,_,_ in UNITS]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--original',type=Path);args=p.parse_args()
    out=args.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    out.mkdir();drive=out/'drive';drive.mkdir()
    sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in NAMES}
    original=args.original.read_bytes() if args.original else None
    if original:assert hashlib.sha256(original).hexdigest()=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    native={};proof=json.loads((ROOT/'reconstruction/chat/character-provenance.json').read_text())
    screen_proof=json.loads((ROOT/'reconstruction/screen/provenance.json').read_text())
    controller_proof=json.loads((ROOT/'reconstruction/chat/provenance.json').read_text())
    for name,address,size in UNITS+[('reconstruction/chat/chat.asm',0xe828,760)]:
        path=out/(Path(name).stem+'.bin')
        subprocess.run(['nasm','-fbin','-DRECON_FLAT','-I',str(ROOT/'reconstruction/uart')+'/',str(ROOT/name),'-o',str(path)],check=True)
        code=path.read_bytes();assert len(code)==size
        if address==0xe828:expected=controller_proof['sha256'];offset=controller_proof['source_file_offset']
        else:
            expected=proof['sha256'] if address==0x3d94 else proof['bios_character']['sha256'] if address==0x6c4a else next(u['sha256'] for u in screen_proof['units'] if u['file']==name)
            offset=address+0x1200
        assert hashlib.sha256(code).hexdigest()==expected,name
        if original:assert original[offset:offset+size]==code,name
        native[address]=code
    for name,obj,flags in [('standalone/chat_session_host.c','host.obj',[])]+[(n,Path(n).stem+'.obj',['-nt=CHAT_CODE','-nc=FARCODE']) for n in ('src/chat/session.c','src/chat/screen.c','src/terminal/chat_owner.c')]:
        subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-ecc','-dCHAT_BANK',*flags,'-fo='+obj,str(ROOT/name)],cwd=drive,check=True)
    subprocess.run(['nasm','-fobj',str(ROOT/'src/chat/bank.asm'),'-o','bank.obj'],cwd=drive,check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-k8192','-fe=SESSION.EXE','-fm=SESSION.MAP','bank.obj','host.obj','session.obj','screen.obj','chat_owner.obj'],cwd=drive,check=True)
    config=out/'dosbox.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[autoexec]\n@echo off\nmount c "'+str(drive)+'"\nc:\nSESSION >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
    with (out/'dosbox.log').open('w') as log:
        result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=drive,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
    assert result.returncode==0 and (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),(drive/'RESULT.TXT').read_text()
    effects=list(struct.iter_unpack('<5H',(drive/'EVENTS.BIN').read_bytes()))
    frames=(drive/'FRAMES.BIN').read_bytes();at=0;count=0;keys=[0x1e61,0x6d00,0x7800,13,ord('X'),27]
    for case in range(8):
        rows=(25,28,43,50)[case%4]
        events=execute(native[0xe828],keys,buffered=case&1,duplex=(case>>1)&1,newline=(case>>2)&1,rows=rows,key_markers=True)
        chunks=[];outgoing=[]
        for event in events:
            address=event[0]
            if address==0x64fe:chunks.append([])
            elif chunks:chunks[-1].append(event)
            if address==0xa62:outgoing.extend((1,b) for b in event[1])
            elif address==0xab0b:outgoing.append((1,event[1]&255))
            elif address==0x9b6:outgoing.append((2,event[1]))
            elif address==0x5832:outgoing.append((3,event[1]))
        assert len(chunks)==len(keys)
        actual=[(kind,value) for c,incoming,kind,value,blocked in effects if c==case and not incoming]
        assert actual==outgoing,(case,actual,outgoing)
        rx=[(kind,value) for c,incoming,kind,value,blocked in effects if c==case and incoming]
        assert rx==[(kind,240+i%16) for i in range(64) for kind in (3,2)]
        assert all(blocked for c,incoming,kind,value,blocked in effects if c==case and incoming)
        oracle=NativePane(native,rows,0x17,0x71,0x17)
        def check(tag):
            nonlocal at,count
            assert struct.unpack_from('<3H',frames,at)==(case,tag,rows);at+=6
            size=rows*160;expected=struct.pack('<'+'H'*len(oracle.frame),*oracle.frame)
            assert frames[at:at+size]==expected,(case,tag,'frame')
            at+=size
            assert struct.unpack_from('<4H',frames,at)==(*oracle.panes[0][2:],*oracle.panes[1][2:]),(case,tag,'cursor')
            at+=8;count+=1
        def paint(index):
            for e in chunks[index]:
                if e[0]==0x3d94:oracle.put(1,e[1])
        check(0)
        for index in range(4):paint(index);check(index+1)
        for i in range(64):oracle.put(0,240+i%16);check(100+i)
        paint(4);check(5);paint(5);check(6)
    assert at==len(frames)
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in sources.items())
    report=dict(passed=True,cases=8,complete_frames=count,ordered_effects=len(effects),
        rx_effects_while_tx_blocked=1024,abort_reopen_progress_points=12,context_bytes=358,
        native_reference_bytes=1422,native_original_compared=bool(original),sources=sources,
        artifacts={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},
        scope='Actual DOS8086 far-bank composed Chat with synthetic bounded sinks. Per-stream effects match native760-byte controller; full frames/cursors match native662-byte reference with modeled BIOS/scroll/UI callees. RX progresses while TX is refused. Yielding interleaving intentionally differs from native blocking timing. No live parent/UART/BBS/physical or complete native callee acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS composed Chat DOS:',count,'full frames',len(effects),'effects')


if __name__=='__main__':main()
