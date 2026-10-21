#!/usr/bin/env python3
"""Exercise the Synchronet cancel helper with actual DOS BIOS reads."""
import argparse,json,os,subprocess
from pathlib import Path
from audio_synchronet import ROOT,sha

def run(out,watchdog,slot=3):
 out.mkdir()
 phases="""mov si,hangup
call screen
mov bx,1f00h
call expect
mov si,download
call screen
mov si,filename_keys
call sequence
mov si,receiving
call screen
call quiet
mov ax,0b800h
mov es,ax
mov word [es:3680+70*2],1f31h
mov bx,011bh
call expect
mov si,cancel_notice
call screen
call quiet
mov si,pause_prompt
call screen
mov bx,3920h
call expect
mov si,partial_files
call screen
call quiet
mov si,files
call screen
mov bx,1655h
call expect
mov si,remote_filename
call screen
mov si,remote_name_keys
call sequence
mov si,confirm
call screen
mov bx,1579h
call expect
mov si,description
call screen
mov si,description_keys
call sequence
mov si,protocol
call screen
mov bx,0231h
call expect
mov si,hangup
call screen
mov bx,316eh
call expect
mov bx,1f00h
call expect
mov si,download
call screen
mov si,filename_keys
call sequence
mov si,receiving
call screen
mov ax,0b800h
mov es,ax
mov word [es:3680+70*2],1f31h
call quiet
mov si,pause_prompt
call screen
mov bx,3920h
call expect
mov si,files
call screen
mov bx,1051h
call expect
mov si,partial_main
call screen
call quiet
mov si,main
call screen
mov bx,2d00h
call expect
mov ax,40h
mov es,ax
mov ax,[es:6ch]
sub ax,[started]
cmp ax,360
jae fail
""" if not watchdog else 'mov bx,2d00h\ncall expect\n'
 source='''bits 16
cpu 8086
org 100h
mov ax,3
int 10h
mov ax,40h
mov es,ax
mov ax,[es:6ch]
mov [started],ax
'''+phases+'''mov ah,1
int 16h
jnz fail
mov dx,passfile
jmp write
fail:mov dx,failfile
write:
mov ah,3ch
xor cx,cx
int 21h
jc exit
mov bx,ax
mov ah,3eh
int 21h
exit:mov ax,4c00h
int 21h
expect:
push si
xor ah,ah
int 16h
pop si
cmp ax,bx
jne fail
ret
sequence:
mov bx,[si]
add si,2
call expect
cmp word [si],0
jne sequence
ret
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
hangup:db 'Hang up after transfer?',0
download:db 'Upload: XMODEM/1K',0
receiving:db 'Sending XMODEM/1K',0
cancel_notice:db 'TX canceled',0
pause_prompt:db '[Hit a key]',0
partial_files:db 'List Files in dir PCPlus Lab [Hit a key]',0
files:db 'List Files in dir PCPlus Lab',0
partial_main:db 'Read/Post Messages',0
main:db 'Read/Post Messages Main Local [2] General:',0
remote_filename:db 'Filename:',0
confirm:db 'to Main PCPlus Lab? SXRUP003.BIN',0
description:db 'Enter a description now.',0
protocol:db 'Protocol, XMODEM-1K/CRC',0
started:dw 0
filename_keys:dw 0x2044,0x273a,0x2b5c,0x1f53,0x1245,0x314e,0x2044,0x2b5c,0x1352,0x1245,0x1454,0x1352,0x1559,0x342e,0x3042,0x1749,0x314e,0x1c0d,0x0
remote_name_keys:dw 0x1f53,0x2d58,0x1352,0x1655,0x1950,0xb30,0xb30,0x433,0x342e,0x3042,0x1749,0x314e,0x1c0d,0x0
description_keys:dw 0x1f53,0x1579,0x316e,0x1474,0x2368,0x1265,0x1474,0x1769,0x2e63,0x3920,0x1950,0x2e43,0x1950,0x266c,0x1675,0x1f73,0x3920,0x1e61,0x1675,0x2064,0x1769,0x186f,0x3920,0x1372,0x1265,0x1474,0x1372,0x1579,0x1c0d,0x0
passfile:db 'PASS.TXT',0
failfile:db 'FAIL.TXT',0
'''
 from audio_synchronet_retry_startup import names_for
 retry=names_for(slot)[1]
 source=source.replace('SXRUP003.BIN',retry).replace('0xb30,0xb30,0x433,','0xb30,0xb30,'+hex(((slot+1)<<8)+ord('0')+slot)+',')
 (out/'probe.asm').write_text(source)
 subprocess.run(['nasm','-fbin','-DAUDIO_SYNC_RETRY_FAST',f'-DAUDIO_SYNC_RETRY_SLOT={slot}',f'-DAUDIO_SYNC_RETRY_WATCHDOG={36 if watchdog else 720}',str(ROOT/'lab/bbs/audio_synchronet_retry_startup_keys.asm'),'-o',str(out/'EXITKEY.COM')],check=True)
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
KEYVEC
exit
''')
 with (out/'dosbox.log').open('w') as log:
  child=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,timeout=35,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
 read=lambda n:(out/n).read_bytes() if (out/n).exists() else b''
 checks=dict(normal_DOS_return=child.returncode==0,exact_BIOS_keys=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),timer_restored=len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN'))
 return dict(mode='watchdog' if watchdog else 'phases_with_partial_markers',passed=all(checks.values()),checks=checks,probe_sha256=sha(out/'probe.asm'))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--slot',type=int,choices=range(1,10),default=3);a=p.parse_args();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 cases=[run(out/name,flag,a.slot) for name,flag in [('phases',False),('watchdog',True)]]
 result=dict(passed=all(c['passed'] for c in cases),cases=cases,slot=a.slot,inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet_retry_startup_keys.asm',ROOT/'lab/bbs/audio_get_vector.asm',ROOT/'lab/bbs/audio_synchronet_retry_startup.py']},scope='Actual DOS 8086 BIOS key reads: cancel only after visible ACKed progress, require TX canceled and actual pause/fresh Files; type a second filename/confirmation/description/protocol, start ordinary sender again with the same local path, and do not Escape at retry progress. Completion pause/Files/Main/footer precede Alt-X. Partial menus emit no premature keys; independent watchdog and timer restoration. Normal path must finish before360ticks, below720tick watchdog; shortened test delays only, no audio or application acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
