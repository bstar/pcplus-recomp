; Recovered PCPlus 2.01 window snapshot instructions; see docs/UI_WINDOWS.md.
BITS 16
CPU 8086
%ifdef UI_WINDOWS_OMF
SEGMENT _TEXT public class=CODE use16
global pcplus_screen_save
extern ui_read_packed
%define short
%else
ORG 0x765c
%define ui_read_packed 0x6fd0
%endif
%include "encodings.inc"
pcplus_screen_save:
L_765c: mov_load bx,sp
L_765e: push di
L_765f: push si
L_7660: push bp
L_7661: mov bp,[bx+0x2]
L_7664: mov si,[bx+0x4]
L_7667: push ds
L_7668: pop es
L_7669: mov di,[bx+0x6]
L_766c: cmp bp,0x0
L_766f: jz short L_767c
L_7671: dec bp
L_7672: push si
L_7673: add si,0x2
L_7676: call ui_read_packed
L_7679: stosw
L_767a: jmp short L_766c
L_767c: pop bp
L_767d: pop si
L_767e: pop di
L_767f: ret word 0x6
