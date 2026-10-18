; Recovered PCPlus 2.01 video instructions; see docs/TEXT.md.
BITS 16
CPU 8086
%ifdef TEXT_OMF
SEGMENT _TEXT public class=CODE use16
global text_write_packed
extern text_cga_word
extern text_video_segment
extern text_cga_status_port
%define short
%else
ORG 0x6cb4
%define text_cga_word 0x7e20
%define text_video_segment 0x7a78
%define text_cga_status_port 0x7a8e
%endif
%include "encodings.inc"
text_write_packed:
L_6cb4: mov_load bx,sp
L_6cb6: mov_load cx,di
L_6cb8: mov di,[bx+0x2]
L_6cbb: mov ax,[bx+0x4]
L_6cbe: xchg al,ah
L_6cc0: mov es,word [text_video_segment]
L_6cc4: mov dx,[text_cga_status_port]
L_6cc8: cmp dx,0x0
L_6ccb: jnz short L_6cd3
L_6ccd: stosw
L_6cce: mov_load di,cx
L_6cd0: ret word 0x4
L_6cd3: call text_cga_word
L_6cd6: jmp short L_6cce
