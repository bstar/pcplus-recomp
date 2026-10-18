; Recovered PCPlus 2.01 video instructions; see docs/TEXT.md.
BITS 16
CPU 8086
%ifdef TEXT_OMF
SEGMENT _TEXT public class=CODE use16
global text_cga_word
%define short
%else
ORG 0x7e20
%endif
%include "encodings.inc"
text_cga_word:
L_7e20: push bx
L_7e21: mov_load bx,ax
L_7e23: in al,dx
L_7e24: test al,0x1
L_7e26: jnz short L_7e23
L_7e28: cli
L_7e29: in al,dx
L_7e2a: test al,0x1
L_7e2c: jz short L_7e29
L_7e2e: xchg ax,bx
L_7e2f: stosw
L_7e30: sti
L_7e31: pop bx
L_7e32: ret
