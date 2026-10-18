; Recovered PCPlus 2.01 video instructions; see docs/TEXT.md.
BITS 16
CPU 8086
%ifdef TEXT_OMF
SEGMENT _TEXT public class=CODE use16
global text_write_char
extern text_video_segment
extern text_cga_status_port
%define short
%else
ORG 0x6c84
%define text_video_segment 0x7a78
%define text_cga_status_port 0x7a8e
%endif
%include "encodings.inc"
text_write_char:
L_6c84: mov_load bx,sp
L_6c86: mov_load cx,di
L_6c88: mov di,[bx+0x2]
L_6c8b: mov ax,[bx+0x4]
L_6c8e: mov es,word [text_video_segment]
L_6c92: mov dx,[text_cga_status_port]
L_6c96: cmp dx,0x0
L_6c99: jnz short L_6ca1
L_6c9b: stosb
L_6c9c: mov_load di,cx
L_6c9e: ret word 0x4
L_6ca1: mov_load bl,al
L_6ca3: in al,dx
L_6ca4: test al,0x1
L_6ca6: jnz short L_6ca3
L_6ca8: cli
L_6ca9: in al,dx
L_6caa: test al,0x1
L_6cac: jz short L_6ca9
L_6cae: xchg ax,bx
L_6caf: stosb
L_6cb0: sti
L_6cb1: jmp short L_6c9c
