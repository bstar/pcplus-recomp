#!/usr/bin/env python3
"""Actual BIOS-only test of the download probe's post-receive key phases."""
import argparse,json,os,struct,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    out=p.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    source='''bits 16
cpu 8086
org 100h
mov ax,3
int 10h
mov si,first
call screen
mov ax,40h
mov es,ax
mov dx,[es:6ch]
.wait_start:
mov ax,[es:6ch]
sub ax,dx
cmp ax,5
jb .wait_start
mov ah,1
int 16h
jnz fail
mov si,second
call screen
mov cx,2
call keys
mov si,third
call screen
mov cx,13
call keys
mov si,fourth
call screen
mov cx,1
call keys
mov ah,3ch
xor cx,cx
mov dx,filename
int 21h
jc fail
mov bx,ax
mov ah,40h
mov cx,32
mov dx,values
int 21h
cmp ax,32
jne fail
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
fail: mov ax,4c01h
int 21h
keys:
xor ah,ah
int 16h
mov bx,[key_cursor]
mov [bx],ax
add word [key_cursor],2
loop keys
ret
screen:
mov ax,0b800h
mov es,ax
xor di,di
mov ax,0720h
mov cx,2000
rep stosw
xor di,di
.text:
lodsb
or al,al
jz .done
mov ah,7
stosw
jmp .text
.done: ret
first: db 'Receiving ZMODEM',0
second: db 'File Base ...cmd:',0
third: db 'FILE SEARCH ESC : cancel',0
fourth: db 'QUEUED PCXTEST.BIN',0
key_cursor: dw values
values: times32 db0
filename: db 'KEYS.BIN',0
'''.replace('times32 db0','times 32 db 0')
    (out/'probe.asm').write_text(source)
    for flags,asm,leaf in [(['-DAUDIO_DOWNLOAD_FAST_TEST=1'],ROOT/'lab/bbs/audio_download_keys.asm','EXITKEY.COM'),([],out/'probe.asm','PROBE.COM'),([],ROOT/'lab/bbs/audio_get_vector.asm','KEYVEC.COM')]:
        subprocess.run(['nasm','-fbin',*flags,str(asm),'-o',str(out/leaf)],check=True)
    (out/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
c:
EXITKEY
PROBE
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
KEYVEC
exit
''')
    with (out/'dosbox.log').open('w') as log:
        run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,timeout=15,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
    read=lambda n:(out/n).read_bytes() if (out/n).exists() else b''
    expected=[0x1f53,0x1c0d,0x1950,0x2e43,0x2d58,0x1454,0x1245,0x1f53,0x1454,0x342e,0x3042,0x1749,0x314e,0x1c0d,0x1c0d,0x2d00]
    checks={'normal_DOS_exit':run.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
            'exact_phased_BIOS_keys':read('KEYS.BIN')==struct.pack('<16H',*expected),
            'timer_vector_restored':len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN')}
    r={'passed':all(checks.values()),'checks':checks,'inputs':{str(n.relative_to(ROOT)):sha(n) for n in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_download_keys.asm',ROOT/'lab/bbs/audio_get_vector.asm']},
       'scope':'Actual DOS BIOS helper test with independent synthetic video phases and shortened test-only delays. No keys during the receive phase; exact post-menu/search/exit keys and INT1C restoration. No product-state, real transfer, serial or BBS acceptance claim.'}
    (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']


if __name__=='__main__':main()
