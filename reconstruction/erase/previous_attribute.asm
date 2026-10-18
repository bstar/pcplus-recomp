; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global erase_previous_attribute
extern erase_default_attribute
extern erase_attribute_values_base
%define short
%else
ORG 0x2d4c
%define erase_default_attribute 0x2d38
%define erase_attribute_values_base 0x39c2
%endif
%include "encodings.inc"
erase_previous_attribute:
L_2d4c: push bp
L_2d4d: mov_load bp,sp
L_2d4f: push si
L_2d50: mov bx,[bp+0x4]
L_2d53: or_load bx,bx
L_2d55: jnz short L_2d5c
L_2d57: call erase_default_attribute
L_2d5a: jmp short L_2d65
L_2d5c: mov_load si,bx
L_2d5e: mov bx,[erase_attribute_values_base]
L_2d62: mov al,[bx+si-0x1]
L_2d65: pop si
L_2d66: mov_load sp,bp
L_2d68: pop bp
L_2d69: ret word 0x2
