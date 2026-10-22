; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_copy_cell
extern window_write
%define short
%else
ORG 32630
%define window_write 27828
%endif
%include "encodings.inc"
window_copy_cell:
L_7f76: push bp
L_7f77: mov_load bp,sp
L_7f79: mov dx,[bp+0x4]
L_7f7c: les bx,word [bp+0x6]
L_7f7f: add_load bx,dx
L_7f81: mov ax,[es:bx]
L_7f84: xchg al,ah
L_7f86: push ax
L_7f87: push dx
L_7f88: call window_write
L_7f8b: pop bp
L_7f8c: ret word 0x6
