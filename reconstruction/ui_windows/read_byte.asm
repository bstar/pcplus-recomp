; Recovered PCPlus 2.01 window snapshot instructions; see docs/UI_WINDOWS.md.
BITS 16
CPU 8086
%ifdef UI_WINDOWS_OMF
SEGMENT _TEXT public class=CODE use16
global ui_read_byte
extern text_video_segment
extern text_cga_status_port
%define short
%else
ORG 0x6fa0
%define text_video_segment 0x7a78
%define text_cga_status_port 0x7a8e
%endif
%include "encodings.inc"
ui_read_byte:
L_6fa0: mov_load bx,sp
L_6fa2: mov_load cx,si
L_6fa4: mov si,[bx+0x2]
L_6fa7: mov dx,[text_cga_status_port]
L_6fab: mov bx,ds
L_6fad: mov ds,word [text_video_segment]
L_6fb1: cmp dx,0x0
L_6fb4: jnz short L_6fc0
L_6fb6: lodsb
L_6fb7: mov ds,bx
L_6fb9: mov_load si,cx
L_6fbb: xor_load ah,ah
L_6fbd: ret word 0x2
L_6fc0: in al,dx
L_6fc1: test al,0x1
L_6fc3: jnz short L_6fc0
L_6fc5: cli
L_6fc6: in al,dx
L_6fc7: test al,0x1
L_6fc9: jz short L_6fc6
L_6fcb: lodsb
L_6fcc: sti
L_6fcd: jmp short L_6fb7
