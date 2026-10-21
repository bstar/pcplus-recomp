#!/usr/bin/env python3
"""Actual DOS/BIOS burst-helper keys, final-screen guards and timer retirement."""
import argparse,json,os,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
import sys
sys.path.insert(0,str(ROOT/'standalone'))
from test_terminal import SAMPLER

PROBE=r'''bits 16
cpu 8086
org 100h
mov ax,3
int 10h
%if CASE != 3
mov si,subject
mov di,320
call text
mov si,initial
mov di,640
call text
mov si,keys
mov di,received
mov cx,25
.read:
xor ah,ah
int 16h
cmp ax,[si]
jne failure
mov [di],ax
add si,2
add di,2
loop .read
%if CASE == 0 || CASE == 1
mov si,final_text
mov di,960
call text
%endif
%if CASE == 0 || CASE == 2
mov si,final_footer
mov di,1280
call text
%endif
%if CASE == 1 || CASE == 2
xor ah,ah
int 1ah
mov [begin],dx
.blocked:
mov ah,1
int 16h
jnz failure
xor ah,ah
int 1ah
sub dx,[begin]
cmp dx,36
jb .blocked
%if CASE == 1
mov si,final_footer
mov di,1280
%else
mov si,final_text
mov di,960
%endif
call text
%endif
%endif
xor ah,ah
int 1ah
mov [begin],dx
.final:
mov ah,1
int 16h
jnz .ready
xor ah,ah
int 1ah
sub dx,[begin]
cmp dx,54
jb .final
jmp failure
.ready:
xor ah,ah
int 16h
cmp ax,2d00h
jne failure
%if CASE == 3
mov [received],ax
%else
mov [received+50],ax
%endif
mov dx,filename
xor cx,cx
mov ah,3ch
int 21h
jc failure
mov bx,ax
mov dx,received
%if CASE == 3
mov cx,2
%else
mov cx,52
%endif
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
text:
push ax
push si
push di
push es
mov ax,0b800h
mov es,ax
mov ah,7
.next:
lodsb
or al,al
jz .done
stosw
jmp .next
.done:
pop es
pop di
pop si
pop ax
ret
begin: dw 0
received: times 26 dw 0
keys: dw 1e41h,3042h,2e43h,2044h,1245h,4700h,2348h,4f00h,1245h
      dw 4b00h,5300h,5200h,2c5ah,0f09h,1454h,4900h,5100h,1519h
      dw 1655h,314eh,1f53h,1e41h,2f56h,1245h,2044h
subject: db 'KEYTEST',0
initial: db 'INS 01,01',0
final_text: db 'UNSAVED',0
final_footer: db 'OVR 01,08',0
filename: db 'KEYS.BIN',0
'''


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 helper=ROOT/'lab/bbs/audio_editor_keys.asm';baseline=ROOT/'build/bbs-lab/current-enigma-editor-audio-01/program/EXITKEY.COM'
 subprocess.run(['nasm','-fbin',str(helper),'-o',str(out/'DEFAULT.COM')],check=True)
 assert (out/'DEFAULT.COM').read_bytes()==baseline.read_bytes()
 cases=[]
 for index,name in enumerate(('complete-final-screen','text-only-blocks-exit','cursor-only-blocks-exit','prerequisite-watchdog','final-screen-watchdog')):
  folder=out/name;folder.mkdir();(folder/'probe.asm').write_text(PROBE);(folder/'sampler.asm').write_text(SAMPLER)
  subprocess.run(['nasm','-fbin','-DAUDIO_EDITOR_BURST=1','-DAUDIO_EDITOR_KEY_TICKS=1','-DAUDIO_EDITOR_INITIAL_TICKS=4','-DAUDIO_EDITOR_WATCHDOG_TICKS='+('36' if index==3 else '72' if index==4 else '180'),str(helper),'-o',str(folder/'EXITKEY.COM')],check=True)
  for source,leaf,flags in ((folder/'probe.asm','PROBE.COM',['-DCASE='+str(index)]),(folder/'sampler.asm','SNAP.COM',[]),(ROOT/'lab/bbs/audio_get_vector.asm','KEYVEC.COM',[])):
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
echo PASS>PASS.TXT
goto capture
:failed
echo FAIL>FAIL.TXT
:capture
KEYVEC
SNAP A
exit
''')
  with (folder/'dosbox.log').open('w') as log:process=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],stdout=log,stderr=log,timeout=18,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
  read=lambda n:(folder/n).read_bytes() if (folder/n).exists() else b''
  checks=dict(actual_BIOS_sequence_and_final_guard=read('PASS.TXT') and not read('FAIL.TXT') and len(read('KEYS.BIN'))==(2 if index==3 else 52),normal_DOS_exit=process.returncode==0,hardware_and_timer_restored=len(read('BEFORE.BIN'))==42 and read('BEFORE.BIN')==read('AFTER.BIN'),original_INT1C_restored=len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN'))
  cases.append(dict(mode=name,checks={k:bool(v) for k,v in checks.items()},captures_sha256={n:sha(folder/n) for n in ('KEYS.BIN','BEFORE.BIN','AFTER.BIN','KEYOLD.BIN','KEYNEW.BIN')} if read('KEYS.BIN') else {}))
 r=dict(passed=all(v for c in cases for v in c['checks'].values()),default_helper_binary_exact=True,default_helper_sha256=sha(out/'DEFAULT.COM'),cases=cases,
  inputs={n:sha(ROOT/n) for n in ('lab/bbs/check_audio_editor_burst_keys.py','lab/bbs/audio_editor_keys.asm','lab/bbs/audio_get_vector.asm','standalone/test_terminal.py')},
  scope='Actual8086 DOS/BIOS probe only. One-tick key delivery; either missing final-screen marker blocks exit for36 ticks, both markers release before watchdog, prerequisite or final-screen failure exits via the bounded watchdog. All hardware/vector state restores. Default paced helper is byte-identical to the accepted editor helper. Test-only initial wait reduced to4 ticks; no product/serial/BBS burst acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=r['passed'],cases=len(cases),default_helper_binary_exact=True)));assert r['passed']


if __name__=='__main__':main()
