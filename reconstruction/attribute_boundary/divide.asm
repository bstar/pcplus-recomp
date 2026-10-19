; Recovered PCPlus 2.01 terminal support instructions; see docs/ATTRIBUTE_BOUNDARY.md.
BITS 16
CPU 8086
%ifdef ATTRIBUTE_BOUNDARY_OMF
%ifdef KEYBOARD_ECHO_FAR
SEGMENT ASPECT_CODE public align=16 class=FARCODE use16
%else
SEGMENT _TEXT public class=CODE use16
%endif
global reverse_tab_signed_divide
%define short
%else
ORG 0x830c
%endif
%include "encodings.inc"
reverse_tab_signed_divide:
L_830c: push bp
L_830d: mov_load bp,sp
L_830f: mov ax,[bp+0x4]
L_8312: cwd
L_8313: idiv word [bp+0x6]
L_8316: pop bp
L_8317: ret
