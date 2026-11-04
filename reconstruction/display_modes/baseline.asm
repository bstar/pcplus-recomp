; Exact PCPlus2.01 display-mode service. See provenance.json.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef DISPLAY_MODES_OMF
SEGMENT _TEXT public class=CODE use16
global display_baseline
extern display_cursor_eight
extern display_font_capable
extern display_geometry
extern display_mono
extern display_scanline_capable
extern display_scanlines
%else
ORG 0x6f76
%define display_font_capable 0x7a6e
%define display_scanline_capable 0x7a70
%define display_mono 0x7a86
%define display_geometry 0x6d1a
%define display_scanlines 0x7ee8
%define display_cursor_eight 0x7f2b
%endif
display_baseline:
L_6f76: cmp word [display_scanline_capable],0x0
L_6f7b: jnz short L_6f99
L_6f7d: mov ax,0x3
L_6f80: cmp word [display_mono],0x0
L_6f85: jz short L_6f89
L_6f87: mov al,0x7
L_6f89: int byte 0x10
L_6f8b: call display_geometry
L_6f8e: cmp word [display_font_capable],0x0
L_6f93: jz short L_6f98
L_6f95: call display_cursor_eight
L_6f98: ret
L_6f99: mov bl,0x2
L_6f9b: call display_scanlines
L_6f9e: jmp short L_6f7d
