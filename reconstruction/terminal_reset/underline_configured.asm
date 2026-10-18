; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_reset_underline_configured
extern terminal_set_underline_scanline
extern reset_underline_supported
extern reset_underline_enabled
%define short
%else
ORG 0x40df
%define terminal_set_underline_scanline 0x5c20
%define reset_underline_supported 0x7a6e
%define reset_underline_enabled 0x1d2c
%endif
%include "encodings.inc"
terminal_reset_underline_configured:
L_40df: cmp word [reset_underline_supported],0x0
L_40e4: jz short L_40f5
L_40e6: cmp word [reset_underline_enabled],0x0
L_40eb: jz short L_40f5
L_40ed: mov ax,0x1
L_40f0: push ax
L_40f1: call terminal_set_underline_scanline
L_40f4: pop bx
L_40f5: ret
