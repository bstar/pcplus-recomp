; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_set_mode
extern display_geometry
extern display_extended_mode
%define short
%else
ORG 28478
%define display_geometry 27930
%define display_extended_mode 31336
%endif
%include "encodings.inc"
display_set_mode:
L_6f3e: mov_load bx,sp
L_6f40: mov ax,[bx+0x2]
L_6f43: cmp word [display_extended_mode],0x0
L_6f48: jnz short L_6f54
L_6f4a: xor_load ah,ah
L_6f4c: int byte 0x10
L_6f4e: call display_geometry
L_6f51: ret word 0x2
L_6f54: cmp al,0x12
L_6f56: jc short L_6f4a
L_6f58: mov_load bx,ax
L_6f5a: mov ax,0x6f05
L_6f5d: jmp short L_6f4c
