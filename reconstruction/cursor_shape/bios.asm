; Recovered PCPlus 2.01 cursor-shape instructions; see docs/CURSOR_SHAPE.md.
BITS 16
CPU 8086
%ifdef CURSOR_SHAPE_OMF
SEGMENT _TEXT public class=CODE use16
global cursor_shape_bios
extern cursor_shape_start_scanline
extern cursor_shape_end_scanline
%define short
%else
ORG 0x7e58
%define cursor_shape_start_scanline 0x7a88
%define cursor_shape_end_scanline 0x7a8a
%endif
%include "encodings.inc"
cursor_shape_bios:
L_7e58: mov ax,[cursor_shape_start_scanline]
L_7e5b: mov dx,[cursor_shape_end_scanline]
L_7e5f: mov cx,0x5
L_7e62: shl bl,cl
L_7e64: or_load bl,al
L_7e66: mov_load ch,bl
L_7e68: mov_load cl,dl
L_7e6a: mov ah,0x1
L_7e6c: push bp
L_7e6d: int byte 0x10
L_7e6f: pop bp
L_7e70: ret
