#!/usr/bin/env python3
"""Exercise audio reconnect BIOS keys without a transport or product-memory writes."""
import argparse,json,os,subprocess
from pathlib import Path
from audio_synchronet import ROOT,sha

def run(out,watchdog,carrier_notice='RX carrier lost'):
 out.mkdir()
 phases="""mov si,hangup
call screen
call receive_keys
mov si,receiving
call screen
call quiet
mov si,partial_carrier
call screen
call quiet
mov si,carrier
call screen
mov bx,2000h
call expect
call quiet
mov si,bridge
call screen
call quiet
mov si,hangup
call screen
call receive_keys
mov si,receiving
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
cmp ax,240
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
receive_keys:
mov bx,1300h
call expect
mov si,download
call screen
mov si,filename_keys
.filename:
mov bx,[si]
add si,2
call expect
cmp word [si],0
jne .filename
ret
expect:
push si
xor ah,ah
int 16h
pop si
cmp ax,bx
jne fail
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
partial_carrier:db 'RX carrier',0
carrier:db 'RX carrier lost Hang up after transfer?',0
bridge:db 'CONNECT> ',0
hangup:db 'Hang up after transfer?',0
download:db 'Download: XMODEM',0
receiving:db 'Receiving XMODEM',0
pause_prompt:db '[Hit a key]',0
partial_files:db 'List Files in dir PCPlus Lab [Hit a key]',0
files:db 'List Files in dir PCPlus Lab',0
partial_main:db 'Read/Post Messages',0
main:db 'Read/Post Messages Main Local [2] General:',0
started:dw 0
filename_keys:dw 0x2044,0x273a,0x2b5c,0x1352,0x1245,0x2e43,0x2f56,0x2b5c,0x1f53,0x1559,0x314e,0x2e43,0x342e,0x3042,0x1749,0x314e,0x1c0d,0
passfile:db 'PASS.TXT',0
failfile:db 'FAIL.TXT',0
'''
 if carrier_notice=='Carrier lost':
  source=source.replace("partial_carrier:db 'RX carrier',0", "partial_carrier:db 'Carrier',0").replace("carrier:db 'RX carrier lost Hang up after transfer?',0", "carrier:db 'Carrier lost Hang up after transfer?',0")
 (out/'probe.asm').write_text(source)
 subprocess.run(['nasm','-fbin','-DAUDIO_SYNC_DOWNLOAD_FAST',f'-DAUDIO_SYNC_DOWNLOAD_WATCHDOG={36 if watchdog else 360}',str(ROOT/'lab/bbs/audio_synchronet_reconnect_keys.asm'),'-o',str(out/'EXITKEY.COM')],check=True)
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
  child=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,timeout=20,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
 read=lambda n:(out/n).read_bytes() if (out/n).exists() else b''
 checks=dict(normal_DOS_return=child.returncode==0,exact_BIOS_keys=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),timer_restored=len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN'))
 return dict(mode='watchdog' if watchdog else 'phases_with_partial_markers',carrier_notice=carrier_notice,passed=all(checks.values()),checks=checks,probe_sha256=sha(out/'probe.asm'))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);out=p.parse_args().output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 cases=[run(out/'RX-notice',False),run(out/'connection-notice',False,'Carrier lost'),run(out/'watchdog',True)]
 result=dict(passed=all(c['passed'] for c in cases),cases=cases,inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet_reconnect_keys.asm',ROOT/'lab/bbs/audio_get_vector.asm']},scope='Actual DOS 8086 BIOS reads: first receive then visible carrier loss triggers Alt-D; a stale hangup prompt after redial emits no key; clearing it rearms a fresh second receive and completion. Other assertions: observed fresh hangup prompt leads to Alt-R; actual filename prompt receives exact local path; receiving and completion pause lead to Space, fresh Files to Q, and complete Main/footer to Alt-X. Partial/paused menus emit no premature keys. Normal path bounded below watchdog; separate watchdog and timer restoration verified. Shortened test delays, no audio or application acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
