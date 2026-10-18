; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_reset_underline_default
extern terminal_set_underline_scanline
extern reset_underline_supported
extern reset_underline_suppressed
%define short
%else
ORG 0x40c9
%define terminal_set_underline_scanline 0x5c20
%define reset_underline_supported 0x7a6e
%define reset_underline_suppressed 0x7a86
%endif
%include "encodings.inc"
terminal_reset_underline_default:
L_40c9: cmp word [reset_underline_supported],0x0
L_40ce: jz short L_40de
L_40d0: cmp word [reset_underline_suppressed],0x0
L_40d5: jnz short L_40de
L_40d7: sub_load ax,ax
L_40d9: push ax
L_40da: call terminal_set_underline_scanline
L_40dd: pop bx
L_40de: ret
