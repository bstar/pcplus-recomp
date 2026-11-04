#!/usr/bin/env python3
"""Actual8086 BIOS queue backpressure, ordered keys and INT1C restoration."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
from product_inputs import ROOT,sha
from paced_bios_keys import source


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    recipe='p100 '+'A '*28+'enter escape c-y a-x'
    expected=[0x1e41]*28+[0x1c0d,0x011b,0x1519,0x2d00]
    (out/'PACED.ASM').write_text(source(recipe))
    probe=r'''bits 16
cpu 8086
org 100h
cmp byte [82h],'B'
je before
mov ax,40h
mov es,ax
mov dx,[es:6ch]
.wait:
mov ax,[es:6ch]
sub ax,dx
cmp ax,55
jb .wait
mov ax,[es:1ch]
sub ax,[es:1ah]
and ax,31
shr ax,1
mov [values],ax
cmp ax,15
jne failure
mov di,values+2
mov si,expected
mov cx,32
.keys:
xor ah,ah
int 16h
cmp ax,[si]
jne failure
mov [di],ax
add si,2
add di,2
loop .keys
mov dx,vector_file
mov ax,3d00h
int 21h
jc failure
mov bx,ax
mov dx,vector
mov cx,4
mov ah,3fh
int 21h
jc failure
cmp ax,4
jne failure
mov ah,3eh
int 21h
jc failure
xor ax,ax
mov es,ax
mov ax,[es:70h]
cmp ax,[vector]
jne failure
mov ax,[es:72h]
cmp ax,[vector+2]
jne failure
mov dx,keys_file
mov cx,66
mov si,values
call write
mov ax,4c00h
int 21h
before:
xor ax,ax
mov es,ax
mov ax,[es:70h]
mov [vector],ax
mov ax,[es:72h]
mov [vector+2],ax
mov dx,vector_file
mov cx,4
mov si,vector
call write
mov ax,4c00h
int 21h
write:
push cx
xor cx,cx
mov ah,3ch
int 21h
jc failure
mov bx,ax
pop cx
mov dx,si
mov ah,40h
int 21h
jc failure
cmp ax,cx
jne failure
mov ah,3eh
int 21h
jc failure
ret
failure:
mov ax,4c01h
int 21h
vector_file: db 'VECTOR.BIN',0
keys_file: db 'KEYS.BIN',0
vector: dd 0
values: times 66 db 0
expected:
'''+''.join('dw '+str(w)+'\n' for w in expected)
    (out/'PROBE.ASM').write_text(probe)
    for name in ('PACED','PROBE'):subprocess.run(['nasm','-fbin',str(out/(name+'.ASM')),'-o',str(out/(name+'.COM'))],check=True)
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
c:
PROBE B
if errorlevel 1 goto done
PACED
if errorlevel 1 goto done
PROBE
:done
exit
''')
    frozen={str((ROOT/n).relative_to(ROOT)):sha(ROOT/n) for n in ['lab/bbs/paced_bios_keys.py','lab/bbs/check_paced_bios_keys.py']}
    with (out/'dosbox.log').open('w') as log:
        r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
            env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
    assert r.returncode==0
    words=list(struct.unpack('<33H',(out/'KEYS.BIN').read_bytes()))
    assert words==[15]+expected and len((out/'VECTOR.BIN').read_bytes())==4
    for n,h in frozen.items():assert sha(ROOT/n)==h
    result=dict(passed=True,BIOS_words=32,full_queue_entries=15,ordered_after_backpressure=True,
        INT1C_restored=True,sources=frozen,captures={str(f.relative_to(ROOT)):sha(f) for f in out.iterdir() if f.is_file()},
        scope=__doc__+' Source-built BIOS probe; no PCPlus/protocol acceptance. Literal expected key words include Ctrl-Y scan15h/ASCII19h; independent from table generator.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS paced BIOS:32 ordered keys after full queue; INT1C restored')


if __name__=='__main__':main()
