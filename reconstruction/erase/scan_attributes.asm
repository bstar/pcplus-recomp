; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global erase_scan_attributes
%define short
%else
ORG 0x2d6c
%endif
%include "encodings.inc"
erase_scan_attributes:
L_2d6c: push bp
L_2d6d: mov_load bp,sp
L_2d6f: sub sp,0x4
L_2d72: push di
L_2d73: mov dx,[bp+0x6]
L_2d76: sub_load cx,cx
L_2d78: mov di,[bp+0x4]
L_2d7b: add_load di,dx
L_2d7d: mov_load bx,dx
L_2d7f: inc dx
L_2d80: test byte [bx],0x80
L_2d83: jnz short L_2d8c
L_2d85: cmp_load dx,di
L_2d87: jc short L_2d7d
L_2d89: jmp short L_2d8f
L_2d8b: nop
L_2d8c: mov cx,0x1
L_2d8f: mov_load ax,cx
L_2d91: pop di
L_2d92: mov_load sp,bp
L_2d94: pop bp
L_2d95: ret word 0x4
