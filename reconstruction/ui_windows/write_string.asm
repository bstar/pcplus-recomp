; Recovered PCPlus 2.01 window snapshot instructions; see docs/UI_WINDOWS.md.
BITS 16
CPU 8086
%ifdef UI_WINDOWS_OMF
SEGMENT _TEXT public class=CODE use16
global ui_write_string
extern ui_coordinate_offset
extern ui_cga_blank
extern ui_cga_unblank
extern text_video_segment
%define short
%else
ORG 0x6bf0
%define ui_coordinate_offset 0x7e02
%define ui_cga_blank 0x77be
%define ui_cga_unblank 0x77ae
%define text_video_segment 0x7a78
%endif
%include "encodings.inc"
ui_write_string:
L_6bf0: push bp
L_6bf1: mov_load bp,sp
L_6bf3: push di
L_6bf4: push si
L_6bf5: mov dx,[bp+0x8]
L_6bf8: call ui_coordinate_offset
L_6bfb: mov_load di,ax
L_6bfd: push di
L_6bfe: mov es,word [text_video_segment]
L_6c02: call ui_cga_blank
L_6c05: mov si,[bp+0x4]
L_6c08: mov ax,[bp+0x6]
L_6c0b: mov_load ah,al
L_6c0d: lodsb
L_6c0e: or_load al,al
L_6c10: jz short L_6c15
L_6c12: stosw
L_6c13: jmp short L_6c0d
L_6c15: call ui_cga_unblank
L_6c18: pop di
L_6c19: pop si
L_6c1a: pop di
L_6c1b: pop bp
L_6c1c: ret word 0x6
