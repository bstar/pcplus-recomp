; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_reset_clear_video
extern text_fill_cells
extern reset_video_cells
%define short
%else
ORG 0x6f60
%define text_fill_cells 0x6c20
%define reset_video_cells 0x7a8c
%endif
%include "encodings.inc"
terminal_reset_clear_video:
L_6f60: mov_load bx,sp
L_6f62: mov ax,[bx+0x2]
L_6f65: mov ah,0x20
L_6f67: push ax
L_6f68: mov ax,0x0
L_6f6b: push ax
L_6f6c: push word [reset_video_cells]
L_6f70: call text_fill_cells
L_6f73: ret word 0x2
