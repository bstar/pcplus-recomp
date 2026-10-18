; Recovered PCPlus 2.01 cursor instructions; see docs/SCREEN.md.
BITS 16
CPU 8086
%ifdef SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
global screen_width_transition
extern screen_cursor_column
extern screen_cursor_row
extern screen_last_column
extern screen_line_flags
%define short
%else
ORG 0x2a90
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%define screen_last_column 0x3258
%define screen_line_flags 0xcf86
%endif
%include "encodings.inc"
screen_width_transition:
L_2a90: push bp
L_2a91: mov_load bp,sp
L_2a93: push si
L_2a94: mov si,[bp+0x4]
L_2a97: mov bx,[screen_cursor_row]
L_2a9b: mov al,[bx+si+screen_line_flags]
L_2a9f: and ax,strict word 0x40
L_2aa2: mov_load cx,ax
L_2aa4: mov al,[bx+screen_line_flags]
L_2aa8: and ax,strict word 0x40
L_2aab: sub_load ax,cx
L_2aad: mov_load dx,ax
L_2aaf: or_load ax,ax
L_2ab1: jz short L_2ad5
L_2ab3: or_load dx,dx
L_2ab5: jng short L_2abe
L_2ab7: sar word [screen_cursor_column],1
L_2abb: jmp short L_2ad5
L_2abd: nop
L_2abe: mov ax,[screen_last_column]
L_2ac1: shr ax,1
L_2ac3: cmp ax,[screen_cursor_column]
L_2ac7: jnc short L_2ad1
L_2ac9: mov ax,[screen_last_column]
L_2acc: shr ax,1
L_2ace: mov [screen_cursor_column],ax
L_2ad1: shl word [screen_cursor_column],1
L_2ad5: pop si
L_2ad6: mov_load sp,bp
L_2ad8: pop bp
L_2ad9: ret word 0x2
