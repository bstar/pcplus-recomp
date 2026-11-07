#!/usr/bin/env python3
"""Observe original missing-KBD behavior on isolated synthetic DOS media only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL_SHA='f079418fca6392cde318e2eb657874a1f5ee10db83616c83054d191441fb6244'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();out=args.output.resolve();original=args.original.resolve()
    assert sha(original)==ORIGINAL_SHA and not original.name.endswith('.analysis.exe')
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    watch=(ROOT/'standalone/path_dialog_watch.asm').read_text()
    begin=watch.index(' cmp word [es:806]');end=watch.index('%if WATCH_KIND',begin)
    marker=" xor di,di\n.find:\n mov bx,di\n mov si,title\n mov cx,17\n.match:\n mov al,[si]\n cmp al,[es:bx]\n jne .next\n inc si\n add bx,2\n loop .match\n jmp .found\n.next:\n add di,2\n cmp di,3966\n jbe .find\n jmp .done\n.found:\n"
    watch=(watch[:begin]+marker+watch[end:]).replace('last_sum: dw 0',"title: db 'PgUp/Dn:Terminals'\nlast_sum: dw 0").replace('D:\\PATHVIEW.BIN','C:\\PATHVIEW.BIN')
    edit='f1 p120 tab n e w enter p200 '
    cases=[('missing-exit','escape',None),('missing-save','a-s p800 escape',bytes(31284)),
           ('missing-edit-discard',edit+'escape p300 n',None),
           ('missing-edit-save',edit+'a-s p800 escape',None)]
    expected_edit=bytearray(31284);expected_edit[6*948+16*12:6*948+16*12+4]=b'new\0'
    rows=[]
    for name,keys,expected in cases:
        folder=out/name;folder.mkdir();shutil.copyfile(original,folder/'PCKEYMAP.EXE')
        (folder/'WATCH.ASM').write_text(watch)
        subprocess.run(['nasm','-fbin','-DWATCH_KIND=0',str(folder/'WATCH.ASM'),'-o',str(folder/'WATCH.COM')],check=True)
        (folder/'CHECK.BAT').write_text('@echo off\nset PCPLUS=\nWATCH T\nADDKEY p3500 '+keys+'\nPCKEYMAP 6 NEWFILE.KBD\nif errorlevel 1 goto failed\nWATCH\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\nexit\n:failed\necho FAIL>FAIL.TXT\nexit\n')
        (folder/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 30000\n[mixer]\nnosound=true\n[autoexec]\nmount c "'+str(folder)+'"\nc:\nCHECK.BAT\n')
        with (folder/'dosbox.log').open('w') as log:
            subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=20)
        assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),name
        raw=(folder/'PATHVIEW.BIN').read_bytes();magic,flags,ticks=struct.unpack_from('<3H',raw)
        assert magic==0x5044 and flags==3 and ticks and len(raw)==4071,name
        frame=raw[6:4006];text=frame[::2]
        assert b'KEYBOARD MAPPING' in text and b'PgUp/Dn:Terminals' in text,name
        target=folder/'NEWFILE.KBD'
        if name=='missing-edit-save':expected=bytes(expected_edit)
        assert target.read_bytes()==expected if expected is not None else not target.exists(),name
        assert sha(folder/'PCKEYMAP.EXE')==sha(original)==ORIGINAL_SHA
        rows.append(dict(case=name,passed=True,ready_frame_sha256=hashlib.sha256(frame).hexdigest(),
            file_created=target.exists(),file_bytes=target.stat().st_size if target.exists() else None,
            file_sha256=sha(target) if target.exists() else None,observer_unhook_verified=True))
        print('PASS original new file:',name,flush=True)
    names=['standalone/observe_keymap_newfile.py','standalone/path_dialog_watch.asm']
    result=dict(passed=True,original_sha256=ORIGINAL_SHA,cpu='8086',cases=rows,sources={n:sha(ROOT/n) for n in names},
        scope=__doc__+' Original copied only into ignored build; explicit PCPLUS environment cleared; no private files or application builds. This tests first missing-file load, explicit save, edit/discard and edit/save, not every open failure or factory-map source.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
