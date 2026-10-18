; Recovered PCPlus 2.01 window snapshot instructions; see docs/UI_WINDOWS.md.
BITS 16
CPU 8086
%ifdef UI_WINDOWS_OMF
SEGMENT _TEXT public class=CODE use16
global ui_cga_unblank
extern text_cga_status_port
%define short
%else
ORG 0x77ae
%define text_cga_status_port 0x7a8e
%endif
%include "encodings.inc"
ui_cga_unblank:
L_77ae: mov dx,[text_cga_status_port]
L_77b2: cmp dx,0x0
L_77b5: jz short L_77bc
L_77b7: mov al,0x2d
L_77b9: mov dl,0xd8
L_77bb: out dx,al
L_77bc: ret
