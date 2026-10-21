#!/usr/bin/env python3
"""Actual DOS observer phases, stale-main rejection, watchdog and restoration."""
import argparse,json,os,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha


def run(out,watchdog):
 out.mkdir()
 phases='' if watchdog else '''mov si,main
call screen
call quiet
mov si,files
call screen
call quiet
mov si,messages
call screen
call quiet
mov si,main
call screen
'''
 source='''bits16
cpu 8086
org100h
mov ax,3
int10h
'''.replace('bits16','bits 16').replace('org100h','org 100h').replace('int10h','int 10h')+phases+'''xor ah,ah
int 16h
cmp ax,2d00h
jne fail
mov ah,3ch
xor cx,cx
mov dx,filename
int 21h
jc fail
mov bx,ax
mov dx,key
mov cx,2
mov ah,40h
int 21h
cmp ax,2
jne fail
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
fail:mov ax,4c01h
int 21h
quiet:
mov ax,40h
mov es,ax
mov dx,[es:6ch]
.wait:
mov ax,[es:6ch]
sub ax,dx
cmp ax,6
jb .wait
mov ah,1
int 16h
jnz fail
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
.done:ret
main:db 'Read/Post Messages [1] Local [2] General:',0
files:db 'List Files in dir',0
messages:db 'Read/Post Messages [1] Local [2] General: No messages have been posted on Local General',0
filename:db 'KEY.BIN',0
key:dw 2d00h
'''
 (out/'probe.asm').write_text(source)
 subprocess.run(['nasm','-fbin','-DAUDIO_SYNCHRONET_FINAL_WAIT=4',f'-DAUDIO_SYNCHRONET_WATCHDOG={36 if watchdog else 180}',str(ROOT/'lab/bbs/audio_synchronet_keys.asm'),'-o',str(out/'EXITKEY.COM')],check=True)
 for src,leaf in [(out/'probe.asm','PROBE.COM'),(ROOT/'lab/bbs/audio_get_vector.asm','KEYVEC.COM')]:subprocess.run(['nasm','-fbin',str(src),'-o',str(out/leaf)],check=True)
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
  p=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,timeout=15,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
 read=lambda n:(out/n).read_bytes() if (out/n).exists() else b''
 checks={'normal_DOS_return':p.returncode==0 and bool(read('PASS.TXT')) and not read('FAIL.TXT'),'actual_BIOS_Alt_X':read('KEY.BIN')==b'\0\x2d','timer_restored':len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN')}
 return {'mode':'watchdog' if watchdog else 'phases_with_stale_main','passed':all(checks.values()),'checks':checks,'probe_sha256':sha(out/'probe.asm')}


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);out=p.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 cases=[run(out/name,flag) for name,flag in [('phases',False),('watchdog',True)]]
 result={'passed':all(c['passed'] for c in cases),'cases':cases,'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet_keys.asm',ROOT/'lab/bbs/audio_get_vector.asm']},'scope':'Actual DOS BIOS observer probe. Initial main and file phases emit no keys; retained main behind message pause must not trigger exit; fresh main emits one Alt-X. Independent watchdog path and timer restoration verified. Synthetic visible phases and shortened delays only; no real BBS/audio or physical acceptance.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']

if __name__=='__main__':main()
