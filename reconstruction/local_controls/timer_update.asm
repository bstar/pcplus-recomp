; Original call elapsed formatter CS:37A5..3845 (161 bytes).
; Unsigned comparison of seconds since midnight, one86400-second wrap.
; Long arithmetic and sprintf are explicit external C-runtime services.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef RECON_FLAT
ORG 0x37a5
%define elapsed_seconds 0x3f73
%define elapsed_start_seconds 0xcd8e
%define elapsed_hours 0xcfec
%define elapsed_minutes 0xcfee
%define elapsed_secs 0xcff0
%define elapsed_divide 0x8d48
%define elapsed_remainder 0x8da8
%define elapsed_format 0x473b
%define elapsed_duration 0x2c7c
%define elapsed_sprintf 0x82b6
%else
SEGMENT ELAPSED_TIMER_CODE public align=16 class=FARCODE use16
extern elapsed_seconds,elapsed_start_seconds,elapsed_hours,elapsed_minutes,elapsed_secs
extern elapsed_divide,elapsed_remainder,elapsed_format,elapsed_duration,elapsed_sprintf
global elapsed_update
%endif
elapsed_update:
 push bp
 mov_load bp,sp
 sub sp,4
 push di
 push si
 call elapsed_seconds
 mov [bp-4],ax
 mov [bp-2],dx
 cmp [elapsed_start_seconds+2],dx
 jc .same_day
 ja .wrapped
 cmp [elapsed_start_seconds],ax
 jbe .same_day
.wrapped:
 mov ax,0x5180
 mov dx,1
 sub ax,[elapsed_start_seconds]
 sbb dx,[elapsed_start_seconds+2]
 add [bp-4],ax
 adc [bp-2],dx
 jmp short .duration
.same_day:
 mov ax,[elapsed_start_seconds]
 mov dx,[elapsed_start_seconds+2]
 sub [bp-4],ax
 sbb [bp-2],dx
.duration:
 mov ax,3600
 cwd
 push dx
 push ax
 push word [bp-2]
 push word [bp-4]
 call elapsed_divide
 mov [elapsed_hours],ax
 mov ax,60
 cwd
 push dx
 push ax
 mov cx,3600
 sub_load bx,bx
 push bx
 push cx
 push word [bp-2]
 push word [bp-4]
 call elapsed_remainder
 push dx
 push ax
 mov_load si,ax
 mov_load di,dx
 call elapsed_divide
 mov [elapsed_minutes],ax
 mov cx,60
 sub_load dx,dx
 push dx
 push cx
 push di
 push si
 mov_load si,ax
 call elapsed_remainder
 mov [elapsed_secs],ax
 push ax
 push si
 push word [elapsed_hours]
 mov ax,elapsed_format
 push ax
 mov ax,elapsed_duration
 push ax
 call elapsed_sprintf
 add sp,10
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
