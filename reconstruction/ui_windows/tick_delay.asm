; Recovered PCPlus 2.01 window snapshot instructions; see docs/UI_WINDOWS.md.
BITS 16
CPU 8086
%ifdef UI_WINDOWS_OMF
SEGMENT _TEXT public class=CODE use16
global ui_tick_delay
%define short
%else
ORG 0x6b98
%endif
%include "encodings.inc"
ui_tick_delay:
L_6b98: mov_load bx,sp
L_6b9a: mov dx,[bx+0x2]
L_6b9d: inc dx
L_6b9e: sti
L_6b9f: xor_load cx,cx
L_6ba1: mov es,cx
L_6ba3: mov bx,0x46c
L_6ba6: mov ax,[es:bx]
L_6ba9: cmp ax,[es:bx]
L_6bac: jz short L_6ba9
L_6bae: inc cx
L_6baf: cmp_load cx,dx
L_6bb1: jc short L_6ba6
L_6bb3: ret word 0x2
