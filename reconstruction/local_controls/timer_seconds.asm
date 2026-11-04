; Original seconds-since-midnight reader CS:3F73..3F9B (41 bytes).
; DOS time service writes four words: hundredths,hour,minute,second; RET2.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef RECON_FLAT
ORG 0x3f73
%define elapsed_gettime 0x778c
%else
SEGMENT ELAPSED_TIMER_CODE public align=16 class=FARCODE use16
extern elapsed_gettime
global elapsed_seconds
%endif
elapsed_seconds:
 push bp
 mov_load bp,sp
 sub sp,8
 lea ax,[bp-8]
 push ax
 call elapsed_gettime
 mov ax,3600
 imul word [bp-6]
 mov_load cx,ax
 mov ax,60
 mov_load bx,dx
 imul word [bp-4]
 add ax,[bp-2]
 cwd
 add_load ax,cx
 adc_load dx,bx
 mov_load sp,bp
 pop bp
 ret
