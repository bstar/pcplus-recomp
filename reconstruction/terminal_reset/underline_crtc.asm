; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_set_underline_scanline
extern reset_crtc_port
%define short
%else
ORG 0x5c20
%define reset_crtc_port 0x7a90
%endif
%include "encodings.inc"
terminal_set_underline_scanline:
L_5c20: mov_load bx,sp
L_5c22: mov cl,0x1f
L_5c24: cmp byte [bx+0x2],0x0
L_5c28: jz short L_5c35
L_5c2a: xor_load ax,ax
L_5c2c: mov es,ax
L_5c2e: mov cl,[es:0x485]
L_5c33: dec cl
L_5c35: mov dx,[reset_crtc_port]
L_5c39: mov al,0x14
L_5c3b: out dx,al
L_5c3c: inc dx
L_5c3d: mov_load al,cl
L_5c3f: out dx,al
L_5c40: ret
