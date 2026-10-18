; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_reset_bios_rectangle
%define short
%else
ORG 0x6edc
%endif
%include "encodings.inc"
terminal_reset_bios_rectangle:
L_6edc: mov_load bx,sp
L_6ede: mov ax,[bx+0x8]
L_6ee1: mov cx,[bx+0x6]
L_6ee4: mov dx,[bx+0x4]
L_6ee7: mov bx,[bx+0x2]
L_6eea: mov_load bh,bl
L_6eec: mov ah,0x6
L_6eee: push bp
L_6eef: int byte 0x10
L_6ef1: pop bp
L_6ef2: ret word 0x8
