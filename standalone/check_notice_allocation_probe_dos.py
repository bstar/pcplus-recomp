#!/usr/bin/env python3
"""Verify actual DOS allocation observer preserves caller IF and DOS carry."""
import argparse,json,os,struct,subprocess
from pathlib import Path
from build_path_session import ROOT,sha
from notice_allocation_probe import instrument,read,BYTES


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--legacy-if',action='store_true',help='Negative control: reproduce the observer-entry IF leak in the emulator only')
 p.add_argument('--unobserved',action='store_true',help='DOS baseline with no installed allocation observer')
 a=p.parse_args()
 assert not (a.legacy_if and a.unobserved)
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir()
 source=r'''BITS 16
CPU 8086
ORG 100h
jmp start
sample:
observed: times 3 dw 0
sample_end:
old21: dw 0,0
nip_seen: dw 1
exec_done: dw 0
hp_stage: dw 1
nip_child_psp: dw 0
block: dw 0
name: db 'CONTROL.BIN',0
%macro save 0
pushf
push ax
push bx
push cx
push dx
push si
push di
push bp
push ds
push es
%endmacro
%macro restore 0
pop es
pop ds
pop bp
pop di
pop si
pop dx
pop cx
pop bx
pop ax
popf
%endmacro
handler:
 save
 cld
 mov bp,sp
 restore
 jmp far [cs:old21]
resident_end:
start:
cli
mov ax,cs
mov ss,ax
mov sp,1ff0h
sti
mov bx,512
mov ah,4ah
int 21h
mov [nip_child_psp],cs
mov ax,3521h
int 21h
mov [old21],bx
mov [old21+2],es
mov dx,handler
mov ax,2521h
int 21h
mov bx,1
mov ah,48h
int 21h
pushf
pop word [observed]
mov [block],ax
mov es,ax
mov ah,49h
int 21h
mov bx,0ffffh
mov ah,48h
int 21h
pushf
pop word [observed+2]
push cs
pop es
mov bx,512
mov ah,4ah
int 21h
pushf
pop word [observed+4]
push ds
mov dx,[old21]
mov ds,[old21+2]
mov ax,2521h
int 21h
pop ds
mov dx,name
xor cx,cx
mov ah,3ch
int 21h
mov bx,ax
mov dx,sample
mov cx,sample_end-sample
mov ah,40h
int 21h
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
'''
 # Metadata reads are deliberately unused in this tiny COM control. The fake
 # map only supplies harmless readable PSP-relative addresses for the adapter.
 (out/'control.map').write_text('0000:0010 _runtime_error\n0000:0000 __curbrk\n0000:0002 ___nheapbeg\n')
 generated=instrument(source,out/'control.map')
 if a.unobserved:
  old='mov dx,handler\nmov ax,2521h\nint 21h\n'
  assert generated.count(old)==1;generated=generated.replace(old,'')
 if a.legacy_if:
  old=' mov dx,[ss:bp+24]\n and dx,0x0200\n and ax,0xfdff\n or ax,dx\n'
  assert generated.count(old)==1;generated=generated.replace(old,'')
 (out/'control.asm').write_text(generated)
 subprocess.run(['nasm','-fbin','control.asm','-o','CONTROL.COM'],cwd=out,check=True)
 (out/'dosbox.conf').write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nCONTROL\nexit\n')
 with (out/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=20,check=True)
 raw=(out/'CONTROL.BIN').read_bytes();assert len(raw)==6+BYTES
 flags=struct.unpack_from('<3H',raw);telemetry=read(raw[6:]);rows=telemetry['records']
 checks=dict(observed_call_count=len(rows)==(0 if a.unobserved else 3),caller_IF_expected=all(not f&512 for f in flags) if a.legacy_if else all(f&512 for f in flags),
  DOS_carry=[f&1 for f in flags]==[0,1,0],correct_services=[r['request_ah'] for r in rows]==([] if a.unobserved else [72,72,74]),
  DOS_results=[r['carry'] for r in rows]==([] if a.unobserved else [0,1,0]),observer_IF_expected=all(not r['forwarded_flags']&512 for r in rows) if a.legacy_if else all((r['entry_flags']^r['forwarded_flags'])&512==0 for r in rows),no_overflow=telemetry['overflow']==0)
 result=dict(passed=all(checks.values()),legacy_negative_control=a.legacy_if,unobserved_baseline=a.unobserved,checks=checks,caller_flags=flags,telemetry=telemetry,
  original_inputs=[],binary_sha256=sha(out/'CONTROL.COM'),sources={n:sha(ROOT/n) for n in ('standalone/notice_allocation_probe.py','standalone/check_notice_allocation_probe_dos.py')},
  scope=__doc__+' Successful/failed AH48 and successful AH4A in8086 DOS. Metadata heap addresses are intentionally synthetic and are not heap-capacity evidence.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
