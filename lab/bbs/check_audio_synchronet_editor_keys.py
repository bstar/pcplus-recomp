#!/usr/bin/env python3
"""Exercise the Synchronet editor helper with actual DOS BIOS reads."""
import argparse,json,os,subprocess
from pathlib import Path
from audio_synchronet import ROOT,sha

def run(out,watchdog):
 out.mkdir()
 keys=[0x1519,0x1e41,0x3042,0x2e43,0x2044,0x1245,0x4700,0x2348,0x4f00,0x1245,
  0x4b00,0x5300,0x5200,0x2c5a,0x0f09,0x1454,0x4900,0x5100,0x1519,
  0x1655,0x314e,0x1f53,0x1e41,0x2f56,0x1245,0x2044,0x1011,0x3920,0x2d00]
 phases='' if watchdog else '''mov si,subject
call screen
call quiet
mov si,footer
call screen
call quiet
mov si,both
call screen
'''
 source='''bits 16
cpu 8086
org 100h
mov ax,3
int 10h
'''+phases+'''mov si,expected
.read:
xor ah,ah
int 16h
cmp ax,[si]
jne fail
add si,2
cmp word [si],0
jne .read
mov ah,1
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
subject:db 'Subj: KEYTEST',0
footer:db 'FSEditor Insert Mode',0
both:db 'Subj: KEYTEST FSEditor Insert Mode',0
passfile:db 'PASS.TXT',0
failfile:db 'FAIL.TXT',0
expected:dw '''+','.join(hex(k) for k in ([0x2d00] if watchdog else keys))+',0\n'
 (out/'probe.asm').write_text(source)
 subprocess.run(['nasm','-fbin','-DAUDIO_SYNC_EDITOR_SETTLE=4','-DAUDIO_SYNC_EDITOR_KEY_WAIT=2','-DAUDIO_SYNC_EDITOR_FINAL_WAIT=4',f'-DAUDIO_SYNC_EDITOR_WATCHDOG_TICKS={36 if watchdog else 180}',str(ROOT/'lab/bbs/audio_synchronet_editor_keys.asm'),'-o',str(out/'EXITKEY.COM')],check=True)
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
 return dict(mode='watchdog' if watchdog else 'phases_with_partial_markers',passed=all(checks.values()),checks=checks,probe_sha256=sha(out/'probe.asm'))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);out=p.parse_args().output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 cases=[run(out/name,flag) for name,flag in [('phases',False),('watchdog',True)]]
 result=dict(passed=all(c['passed'] for c in cases),cases=cases,inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet_editor_keys.asm',ROOT/'lab/bbs/audio_get_vector.asm']},scope='Actual DOS 8086 BIOS reads: neither marker alone starts input; both markers emit the exact clear/body/edit/abort/Space/Alt-X sequence once. Watchdog only emits Alt-X. Shortened test delays; no audio or application acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']
