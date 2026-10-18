; Recovered PCPlus 2.01 character editing instructions; see docs/CHARACTER_EDIT.md.
BITS 16
CPU 8086
%ifdef CHARACTER_EDIT_OMF
SEGMENT _TEXT public class=CODE use16
global character_cga_disable
extern text_cga_status_port
%define short
%else
ORG 0x77be
%define text_cga_status_port 0x7a8e
%endif
%include "encodings.inc"
character_cga_disable:
L_77be: mov dx,[text_cga_status_port]
L_77c2: cmp dx,0x0
L_77c5: jz short L_77d1
L_77c7: in al,dx
L_77c8: test al,0x8
L_77ca: jz short L_77c7
L_77cc: mov al,0x25
L_77ce: mov dl,0xd8
L_77d0: out dx,al
L_77d1: ret
