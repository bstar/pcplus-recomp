; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_scanlines
%define short
%else
ORG 32488
%endif
%include "encodings.inc"
display_scanlines:
L_7ee8: push es
L_7ee9: xor_load ax,ax
L_7eeb: mov es,ax
L_7eed: mov al,[es:0x489]
L_7ef1: pop es
L_7ef2: and al,0x90
L_7ef4: jz short L_7f08
L_7ef6: cmp al,0x10
L_7ef8: jnz short L_7eff
L_7efa: cmp bl,0x2
L_7efd: jz short L_7f07
L_7eff: mov ah,0x12
L_7f01: mov_load al,bl
L_7f03: mov bl,0x30
L_7f05: int byte 0x10
L_7f07: ret
L_7f08: cmp bl,0x1
L_7f0b: jz short L_7f07
L_7f0d: jmp short L_7eff
