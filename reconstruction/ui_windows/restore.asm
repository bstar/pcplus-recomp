; Recovered PCPlus 2.01 window snapshot instructions; see docs/UI_WINDOWS.md.
BITS 16
CPU 8086
%ifdef UI_WINDOWS_OMF
SEGMENT _TEXT public class=CODE use16
global pcplus_screen_restore
extern text_write_packed
%define short
%else
ORG 0x7682
%define text_write_packed 0x6cb4
%endif
%include "encodings.inc"
pcplus_screen_restore:
L_7682: mov_load bx,sp
L_7684: push di
L_7685: push si
L_7686: push bp
L_7687: mov bp,[bx+0x2]
L_768a: mov di,[bx+0x4]
L_768d: push ds
L_768e: pop es
L_768f: mov si,[bx+0x6]
L_7692: cmp bp,0x0
L_7695: jz short L_76aa
L_7697: dec bp
L_7698: push es
L_7699: mov ax,[es:si]
L_769c: add si,0x2
L_769f: push ax
L_76a0: push di
L_76a1: add di,0x2
L_76a4: call text_write_packed
L_76a7: pop es
L_76a8: jmp short L_7692
L_76aa: pop bp
L_76ab: pop si
L_76ac: pop di
L_76ad: ret word 0x6
