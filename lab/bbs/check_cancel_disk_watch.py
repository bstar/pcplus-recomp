#!/usr/bin/env python3
"""Actual8086 observer: reject7KiB/bad color, accept jump to15KiB, only once."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
from product_inputs import ROOT,sha
sys.path.insert(0,str(ROOT/'standalone'))
from zmodem_cancel_disk_watch import SAMPLER


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    (out/'SNAP.ASM').write_text(SAMPLER)
    (out/'PROBE.ASM').write_text(r'''bits 16
cpu 8086
org 100h
mov ax,0b800h
mov es,ax
mov word [es:3840],1f52h
mov word [es:3842],1f65h
mov word [es:3844],1f6dh
mov di,3680+66*2
mov ax,1f30h
mov cx,5
rep stosw
mov word [es:3680+70*2],1f37h
call no_key
mov word [es:3680+69*2],0731h
mov word [es:3680+70*2],1f35h
call no_key
mov word [es:3680+69*2],1f31h
xor ah,ah
int 16h
cmp ax,011bh
jne failure
mov [value],ax
mov word [es:3680+69*2],1f32h
mov word [es:3680+70*2],1f33h
call no_key
mov dx,filename
xor cx,cx
mov ah,3ch
int 21h
jc failure
mov bx,ax
mov dx,value
mov cx,2
mov ah,40h
int 21h
jc failure
cmp ax,2
jne failure
mov ah,3eh
int 21h
jc failure
mov ax,4c00h
int 21h
no_key:
push es
mov ax,40h
mov es,ax
mov dx,[es:6ch]
.wait:
mov ax,[es:6ch]
sub ax,dx
cmp ax,5
jb .wait
pop es
mov ah,1
int 16h
jnz failure
ret
failure:
mov ax,4c01h
int 21h
filename: db 'KEY.BIN',0
value: dw 0
''')
    for n in ('SNAP','PROBE'):subprocess.run(['nasm','-fbin',str(out/(n+'.ASM')),'-o',str(out/(n+'.COM'))],check=True)
    (out/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
mount c "{out}"
mount d "{out}"
d:
SNAP B
PROBE
if errorlevel 1 goto finish
echo PASS>PASS.TXT
:finish
SNAP S
SNAP A
exit
''')
    sources={n:sha(ROOT/n) for n in ['lab/bbs/check_cancel_disk_watch.py','lab/bbs/zmodem_cancel_disk_watch.py','lab/bbs/zmodem_cancel_watch.py','lab/bbs/zmodem_label_watch.py','standalone/test_terminal.py']}
    with (out/'dosbox.log').open('w') as log:
        r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
    assert r.returncode==0 and (out/'PASS.TXT').exists() and (out/'KEY.BIN').read_bytes()==b'\x1b\x01'
    before=(out/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(out/'AFTER.BIN').read_bytes()
    labels=(out/'LABELS.BIN').read_bytes();assert len(labels)==2566 and struct.unpack_from('<H',labels,4)[0]&0x8000
    for n,h in sources.items():assert sha(ROOT/n)==h
    result=dict(passed=True,observations=['7KiB:no key','15KiB with wrong attribute:no key','15KiB:BIOS Escape','23KiB:no second key'],
        hardware_restored=True,sources=sources,captures={str(p.relative_to(ROOT)):sha(p) for p in out.iterdir() if p.is_file()},
        scope=__doc__+' Synthetic VGA cells/actual BIOS timer/keyboard. No app/protocol/physical acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS cancel observer:7/bad-color15 ignored;15 triggers once;hardware restored')


if __name__=='__main__':main()
