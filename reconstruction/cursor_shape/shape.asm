; Recovered PCPlus 2.01 cursor-shape instructions; see docs/CURSOR_SHAPE.md.
BITS 16
CPU 8086
%ifdef CURSOR_SHAPE_OMF
SEGMENT _TEXT public class=CODE use16
global modes_cursor_shape
extern cursor_shape_show
extern cursor_shape_hide
extern cursor_shape_start_scanline
extern cursor_shape_end_scanline
%define short
%else
ORG 0x2f78
%define cursor_shape_show 0x6dca
%define cursor_shape_hide 0x6e5a
%define cursor_shape_start_scanline 0x7a88
%define cursor_shape_end_scanline 0x7a8a
%endif
%include "encodings.inc"
modes_cursor_shape:
L_2f78: push bp
L_2f79: mov_load bp,sp
L_2f7b: push si
L_2f7c: mov si,[bp+0x4]
L_2f7f: test si,0x4
L_2f83: jz short L_2fb0
L_2f85: test si,0x2
L_2f89: jz short L_2f96
L_2f8b: mov ax,[cursor_shape_end_scanline]
L_2f8e: cwd
L_2f8f: sub_load ax,dx
L_2f91: sar ax,1
L_2f93: inc ax
L_2f94: jmp short L_2fa4
L_2f96: test si,0x1
L_2f9a: jz short L_2fa2
L_2f9c: mov ax,[cursor_shape_end_scanline]
L_2f9f: dec ax
L_2fa0: jmp short L_2fa4
L_2fa2: sub_load ax,ax
L_2fa4: mov [cursor_shape_start_scanline],ax
L_2fa7: call cursor_shape_show
L_2faa: pop si
L_2fab: mov_load sp,bp
L_2fad: pop bp
L_2fae: ret
L_2faf: nop
L_2fb0: call cursor_shape_hide
L_2fb3: pop si
L_2fb4: mov_load sp,bp
L_2fb6: pop bp
L_2fb7: ret
