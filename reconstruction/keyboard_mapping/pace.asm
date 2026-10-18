; Recovered PCPlus 2.01 terminal keyboard mapping instructions; see docs/KEYBOARD_MAPPING.md.
BITS 16
CPU 8086
%ifdef KEYBOARD_MAPPING_OMF
SEGMENT _TEXT public class=CODE use16
global keyboard_mapping_pace
extern keyboard_state_7ac4
%define short
%else
ORG 0x6b72
%define keyboard_state_7ac4 0x7ac4
%endif
%include "encodings.inc"
keyboard_mapping_pace:
L_6b72: mov_load bx,sp
L_6b74: mov dx,[bx+0x2]
L_6b77: cmp dx,0x0
L_6b7a: jz short L_6b95
L_6b7c: mov ax,ds
L_6b7e: mov es,ax
L_6b80: mov bx,0x7a4e
L_6b83: mov cx,[keyboard_state_7ac4]
L_6b87: sub cx,0x1
L_6b8a: adc ax,strict word 0x0
L_6b8d: cmp cx,[es:bx]
L_6b90: jnz short L_6b87
L_6b92: dec dx
L_6b93: jnz short L_6b83
L_6b95: ret word 0x2
