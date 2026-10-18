; Exact original optional-wait, translation, script-log and dispatch helper.
BITS 16
CPU 8086
%ifdef TRANSLATION_OMF
SEGMENT _TEXT public class=CODE use16
global translation_receive_original
extern translation_table,translation_script_enabled
extern translation_read,translation_wait,translation_script,translation_dispatch
%define short
%else
ORG 0x4c74
%define translation_table 0xd00a
%define translation_script_enabled 0xe2f8
%define translation_read 0xaa65
%define translation_wait 0x5ca0
%define translation_script 0x534e
%define translation_dispatch 0x0610
%endif
%include "encodings.inc"
translation_receive_original:
 push bp
 mov_load bp,sp
 push si
 mov si,[bp+6]
 or_load si,si
 jnz short .wait
 call translation_read
 jmp short .received
.wait:
 call translation_wait
.received:
 mov_load si,ax
 or_load si,si
 jl short .done
 mov al,[translation_table+si]
 sub_load ah,ah
 mov_load si,ax
 cmp word [translation_script_enabled],0
 jz short .dispatch
 push si
 call translation_script
.dispatch:
 cmp word [bp+4],0
 jz short .done
 push si
 call translation_dispatch
 pop bx
.done:
 mov_load ax,si
 pop si
 mov_load sp,bp
 pop bp
 ret 4
