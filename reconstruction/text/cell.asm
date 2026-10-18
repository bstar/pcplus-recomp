; Recovered PCPlus 2.01 video instructions; see docs/TEXT.md.
BITS 16
CPU 8086
%ifdef TEXT_OMF
SEGMENT _TEXT public class=CODE use16
global text_write_cell
extern text_write_bios
extern text_video_segment
extern text_bios_output
%define short
%else
ORG 0x6c5e
%define text_write_bios 0x6c4a
%define text_video_segment 0x7a78
%define text_bios_output 0x7a92
%endif
%include "encodings.inc"
text_write_cell:
L_6c5e: mov_load bx,sp
L_6c60: push di
L_6c61: mov di,[bx+0x2]
L_6c64: mov ax,[bx+0x6]
L_6c67: mov bx,[bx+0x4]
L_6c6a: cmp word [text_bios_output],0x0
L_6c6f: jnz short L_6c7c
L_6c71: mov_load ah,bl
L_6c73: mov es,word [text_video_segment]
L_6c77: stosw
L_6c78: pop di
L_6c79: ret word 0x6
L_6c7c: push ax
L_6c7d: push bx
L_6c7e: call text_write_bios
L_6c81: jmp short L_6c78
