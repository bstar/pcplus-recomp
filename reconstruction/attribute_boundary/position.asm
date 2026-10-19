; Recovered PCPlus 2.01 terminal support instructions; see docs/ATTRIBUTE_BOUNDARY.md.
BITS 16
CPU 8086
%ifdef ATTRIBUTE_BOUNDARY_OMF
%ifdef KEYBOARD_ECHO_FAR
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global attribute_position_to_video
extern screen_viewport_enabled
extern screen_viewport_active
extern screen_viewport_right
extern screen_viewport_left
extern screen_columns
%define short
%else
ORG 0x2b86
%define screen_viewport_enabled 0xcdfa
%define screen_viewport_active 0x3256
%define screen_viewport_right 0x7a7e
%define screen_viewport_left 0xce2e
%define screen_columns 0x7a72
%endif
%include "encodings.inc"
attribute_position_to_video:
L_2b86: push bp
L_2b87: mov_load bp,sp
L_2b89: push di
L_2b8a: mov bx,[bp+0x4]
L_2b8d: mov di,[bx+0x4]
L_2b90: cmp word [screen_viewport_enabled],0x0
L_2b95: jz short L_2ba4
L_2b97: cmp word [screen_viewport_active],0x0
L_2b9c: jz short L_2bbc
L_2b9e: cmp [screen_viewport_right],di
L_2ba2: jc short L_2bb6
L_2ba4: mov word [bx],0x1
L_2ba8: cmp word [bx],0x0
L_2bab: jz short L_2bca
L_2bad: mov ax,[bx+0x2]
L_2bb0: mul word [screen_columns]
L_2bb4: jmp short L_2bd0
L_2bb6: mov word [bx],0x0
L_2bba: jmp short L_2ba8
L_2bbc: mov ax,[screen_viewport_left]
L_2bbf: dec ax
L_2bc0: cmp_load ax,di
L_2bc2: jnc short L_2bb6
L_2bc4: sub di,[screen_viewport_left]
L_2bc8: jmp short L_2ba4
L_2bca: mov ax,0x84
L_2bcd: mul word [bx+0x2]
L_2bd0: add_load ax,di
L_2bd2: shl ax,1
L_2bd4: mov [bx+0x6],ax
L_2bd7: pop di
L_2bd8: mov_load sp,bp
L_2bda: pop bp
L_2bdb: ret word 0x2
