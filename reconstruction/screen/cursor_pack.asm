; Recovered PCPlus 2.01 cursor instructions; see docs/SCREEN.md.
BITS 16
CPU 8086
%ifdef SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
global screen_cursor_pack
extern screen_cursor_output
%define short
%else
ORG 0x6e66
%define screen_cursor_output 0x6e78
%endif
%include "encodings.inc"
screen_cursor_pack:
L_6e66: mov_load bx,sp
L_6e68: mov ax,[bx+0x2]
L_6e6b: mov bx,[bx+0x4]
L_6e6e: mov_load ah,bl
L_6e70: push ax
L_6e71: call screen_cursor_output
L_6e74: ret word 0x4
