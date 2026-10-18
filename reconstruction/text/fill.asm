; Recovered PCPlus 2.01 video instructions; see docs/TEXT.md.
BITS 16
CPU 8086
%ifdef TEXT_OMF
SEGMENT _TEXT public class=CODE use16
global text_fill_cells
extern text_cga_word
extern text_video_segment
extern text_cga_status_port
%define short
%else
ORG 0x6c20
%define text_cga_word 0x7e20
%define text_video_segment 0x7a78
%define text_cga_status_port 0x7a8e
%endif
%include "encodings.inc"
text_fill_cells:
L_6c20: mov_load bx,sp
L_6c22: push di
L_6c23: mov cx,[bx+0x2]
L_6c26: mov di,[bx+0x4]
L_6c29: mov ax,[bx+0x6]
L_6c2c: xchg al,ah
L_6c2e: mov es,word [text_video_segment]
L_6c32: mov dx,[text_cga_status_port]
L_6c36: cmp dx,0x0
L_6c39: jnz short L_6c41
L_6c3b: rep stosw
L_6c3d: pop di
L_6c3e: ret word 0x6
L_6c41: jcxz L_6c3d
L_6c43: call text_cga_word
L_6c46: loop L_6c43
L_6c48: jmp short L_6c3d
