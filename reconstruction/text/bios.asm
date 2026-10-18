; Recovered PCPlus 2.01 video instructions; see docs/TEXT.md.
BITS 16
CPU 8086
%ifdef TEXT_OMF
SEGMENT _TEXT public class=CODE use16
global text_write_bios
%define short
%else
ORG 0x6c4a
%endif
%include "encodings.inc"
text_write_bios:
L_6c4a: mov_load bx,sp
L_6c4c: mov ax,[bx+0x4]
L_6c4f: mov bx,[bx+0x2]
L_6c52: mov cx,0x1
L_6c55: mov ah,0x9
L_6c57: push bp
L_6c58: int byte 0x10
L_6c5a: pop bp
L_6c5b: ret word 0x4
