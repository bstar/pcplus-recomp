; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_clear
extern display_fill
extern display_cells
%define short
%else
ORG 28512
%define display_fill 27680
%define display_cells 31372
%endif
%include "encodings.inc"
display_clear:
L_6f60: mov_load bx,sp
L_6f62: mov ax,[bx+0x2]
L_6f65: mov ah,0x20
L_6f67: push ax
L_6f68: mov ax,0x0
L_6f6b: push ax
L_6f6c: push word [display_cells]
L_6f70: call display_fill
L_6f73: ret word 0x2
