#!/usr/bin/env python3
"""Actual 8086 BIOS helper gates, queue-full retry, watchdog and retirement."""
import argparse,json,os,struct,subprocess,sys
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
sys.path.insert(0,str(ROOT/'standalone'))
from test_terminal import SAMPLER

PROBE=r'''bits 16
cpu 8086
org 100h
mov ax,3
int 10h
%if CASE == 3
mov cx,2d00h
call key
jmp finish
%endif
mov bx,stages
mov word [stage],0
.stage:
call clear
%if CASE == 1
cmp word [stage],4
jne .not_missing
mov si,file
call text
call quiet
.not_missing:
%endif
%if CASE == 2
cmp word [stage],11
jne .not_stale
mov si,file
call text
call quiet
.not_stale:
%endif
%if CASE == 5
cmp word [stage],0
jne .not_full
mov cx,15
.fill:
push cx
mov cx,2c7ah
mov ah,5
int 16h
pop cx
loop .fill
mov si,file
call text
mov cx,18
call pause
mov cx,15
.empty:
push cx
xor ah,ah
int 16h
cmp ax,2c7ah
jne failure
pop cx
loop .empty
.not_full:
%endif
%if CASE == 4
cmp word [stage],13
je .marker_absent
%endif
mov si,[bx]
call text
%if CASE == 4
.marker_absent:
%endif
mov si,[bx+2]
cmp word [si],0
jne .read
mov cx,12
call pause
jmp .next
.read:
mov cx,[si]
or cx,cx
jz .next
call key
add si,2
jmp .read
.next:
add bx,4
inc word [stage]
cmp word [stage],14
jb .stage
finish:
mov dx,name
xor cx,cx
mov ah,3ch
int 21h
jc failure
mov bx,ax
mov dx,received
mov cx,[used]
mov ah,40h
int 21h
jc failure
cmp ax,cx
jne failure
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
failure:
mov ax,4c01h
int 21h
key:
push bx
push cx
push si
xor ah,ah
int 16h
cmp ax,cx
jne failure
mov bx,[used]
mov [received+bx],ax
add word [used],2
pop si
pop cx
pop bx
ret
quiet:
mov cx,36
jmp pause
pause:
push ax
push bx
push cx
push dx
push si
mov si,cx
xor ah,ah
int 1ah
mov bx,dx
.wait:
%if CASE == 1 || CASE == 2
cmp si,36
jne .not_quiet
mov ah,1
int 16h
jnz failure
.not_quiet:
%endif
xor ah,ah
int 1ah
sub dx,bx
cmp dx,si
jb .wait
pop si
pop dx
pop cx
pop bx
pop ax
ret
clear:
push ax
push cx
push di
push es
mov ax,0b800h
mov es,ax
xor di,di
mov ax,0720h
mov cx,2000
rep stosw
pop es
pop di
pop cx
pop ax
ret
text:
push ax
push si
push di
push es
mov ax,0b800h
mov es,ax
mov di,1000
mov ah,7
.loop:
lodsb
or al,al
jz .done
stosw
jmp .loop
.done:
pop es
pop di
pop si
pop ax
ret
stage: dw 0
used: dw 0
received: times 26 dw 0
file: db 'File Base >> active filter:',0
menu: db 'PCPLUS  Command Menu',0
path: db 'Recording file: DOS 8.3 path',0
saved: db 'Recording saved.',0
script: db 'Script DOS 8.3 path:',0
search: db 'ESC : cancel',0
replay: db 'FILE SEARCH',0
expected0: dw 2c00h,0
expected1: dw 2e43h,0
expected2: dw 1c0dh,0
expected3: dw 1f53h,1c0dh,0
expected4: dw 011bh,0
expected5: dw 011bh,011bh,0
expected6: dw 1e41h,0
expected7: dw 1970h,2e63h,1970h,266ch,1675h,1f73h,342eh,1e61h,1f73h,1970h,1c0dh,0
expected8: dw 0
expected9: dw 2d00h,0
stages: dw file,expected0,menu,expected1,path,expected2,file,expected3,search,expected4,file,expected0,menu,expected1
dw saved,expected5,file,expected0,menu,expected6,script,expected7,replay,expected8,file,expected3,search,expected9
name: db 'KEYS.BIN',0
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    helper=ROOT/'lab/bbs/audio_recording_keys.asm'
    subprocess.run(['nasm','-fbin',str(helper),'-o',str(out/'PRODUCTION.COM')],check=True)
    cases=[]
    names=('complete','missing-search-blocks','stale-pre-replay-file-screen-blocks','initial-watchdog','final-watchdog','BIOS-queue-full-retry')
    for index,name in enumerate(names):
        folder=out/name;folder.mkdir();(folder/'probe.asm').write_text(PROBE);(folder/'sampler.asm').write_text(SAMPLER)
        subprocess.run(['nasm','-fbin','-DRECORD_KEY_TICKS=1','-DRECORD_DWELL_TICKS=2','-DRECORD_INITIAL_TICKS=2',
            '-DRECORD_WATCHDOG_TICKS='+('36' if index==3 else '300'),str(helper),'-o',str(folder/'EXITKEY.COM')],check=True)
        for source,leaf,flags in ((folder/'probe.asm','PROBE.COM',['-DCASE='+str(index)]),(folder/'sampler.asm','SNAP.COM',[]),
                (ROOT/'lab/bbs/audio_get_vector.asm','KEYVEC.COM',[])):
            subprocess.run(['nasm','-fbin',*flags,str(source),'-o',str(folder/leaf)],check=True)
        (folder/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[autoexec]
@echo off
mount c "{folder}"
mount d "{folder}"
c:
SNAP B
EXITKEY
PROBE
if errorlevel 1 goto failed
EXITKEY R
if errorlevel 1 goto failed
echo PASS>PASS.TXT
goto capture
:failed
echo FAIL>FAIL.TXT
:capture
KEYVEC
SNAP A
exit
''')
        with (folder/'dosbox.log').open('w') as capture:
            process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],stdout=capture,stderr=capture,
                env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=25)
        read=lambda n:(folder/n).read_bytes() if (folder/n).exists() else b''
        report=struct.unpack('<8H',read('RECKEY.BIN')) if len(read('RECKEY.BIN'))==16 else ()
        checks=dict(normal_exit=process.returncode==0 and bool(read('PASS.TXT')) and not read('FAIL.TXT'),
            exact_BIOS_keys=len(read('KEYS.BIN'))==(2 if index==3 else 52),
            exact_helper_outcome=bool(report) and report[0]==0x524b and report[3]==(2 if index in (3,4) else 1),
            exact_completed_phase=bool(report) and report[1]==(0 if index==3 else 13 if index==4 else 14),
            queue_full_observed=index!=5 or bool(report and report[5]),
            hardware_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),
            timer_restored=len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN'))
        cases.append(dict(name=name,passed=all(checks.values()),checks=checks,helper_report=report,
            captures_sha256={f.name:sha(f) for f in folder.iterdir() if f.is_file()}))
        print(name,cases[-1]['passed'],report,flush=True)
        assert cases[-1]['passed'],'Inspect retained actual DOS probe'
    result=dict(passed=True,cases=cases,production_helper_sha256=sha(out/'PRODUCTION.COM'),
        inputs={str(path.relative_to(ROOT)):sha(path) for path in (Path(__file__).resolve(),helper,ROOT/'lab/bbs/audio_get_vector.asm',ROOT/'standalone/test_terminal.py')},
        scope='Actual8086 DOS BIOS fixture only. Independent expected keys, missing/stale markers, queue-full retry, watchdog outcomes and full hardware/timer retirement. Test-only shortened timings; no product/serial/BBS/audio acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
