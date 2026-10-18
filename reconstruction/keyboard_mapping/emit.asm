; Recovered PCPlus 2.01 terminal keyboard mapping instructions; see docs/KEYBOARD_MAPPING.md.
BITS 16
CPU 8086
%ifdef KEYBOARD_MAPPING_OMF
SEGMENT _TEXT public class=CODE use16
global keyboard_mapping_emit
extern keyboard_mapping_pace
extern keyboard_service_ab0b
extern keyboard_state_1d68
%define short
%else
ORG 0xa62
%define keyboard_mapping_pace 0x6b72
%define keyboard_service_ab0b 0xab0b
%define keyboard_state_1d68 0x1d68
%endif
%include "encodings.inc"
keyboard_mapping_emit:
L_0a62: push si
L_0a63: cmp byte [bx],0x0
L_0a66: jz short L_0a89
L_0a68: mov_load si,bx
L_0a6a: cmp byte [si],0xff
L_0a6d: jz short L_0a76
L_0a6f: mov al,[si]
L_0a71: sub_load ah,ah
L_0a73: jmp short L_0a78
L_0a75: nop
L_0a76: sub_load ax,ax
L_0a78: push ax
L_0a79: call keyboard_service_ab0b
L_0a7c: push word [keyboard_state_1d68]
L_0a80: call keyboard_mapping_pace
L_0a83: inc si
L_0a84: cmp byte [si],0x0
L_0a87: jnz short L_0a6a
L_0a89: pop si
L_0a8a: ret
