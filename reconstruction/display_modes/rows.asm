; Exact PCPlus2.01 display-mode service. See provenance.json.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef DISPLAY_MODES_OMF
SEGMENT _TEXT public class=CODE use16
global display_select_rows
extern display_font_capable
extern display_font_ega14
extern display_font_ega8
extern display_font_vga14
extern display_font_vga16
extern display_font_vga43
extern display_font_vga50
extern display_geometry
extern display_scanline_capable
%else
ORG 0x6ef6
%define display_font_capable 0x7a6e
%define display_scanline_capable 0x7a70
%define display_font_ega14 0x7e72
%define display_font_ega8 0x7e78
%define display_font_vga16 0x7e7e
%define display_font_vga14 0x7e8a
%define display_font_vga43 0x7e98
%define display_font_vga50 0x7ea6
%define display_geometry 0x6d1a
%endif
display_select_rows:
L_6ef6: mov_load bx,sp
L_6ef8: cmp word [display_font_capable],0x0
L_6efd: jz short L_6f26
L_6eff: mov al,[bx+0x2]
L_6f02: cmp word [display_scanline_capable],0x0
L_6f07: jz short L_6f1a
L_6f09: cmp al,0x1c
L_6f0b: jz short L_6f29
L_6f0d: cmp al,0x2b
L_6f0f: jz short L_6f33
L_6f11: cmp al,0x32
L_6f13: jz short L_6f38
L_6f15: call display_font_vga16
L_6f18: jmp short L_6f23
L_6f1a: cmp al,0x2b
L_6f1c: jz short L_6f2e
L_6f1e: call display_font_ega14
L_6f21: jmp short L_6f23
L_6f23: call display_geometry
L_6f26: ret word 0x2
L_6f29: call display_font_vga14
L_6f2c: jmp short L_6f23
L_6f2e: call display_font_ega8
L_6f31: jmp short L_6f23
L_6f33: call display_font_vga43
L_6f36: jmp short L_6f23
L_6f38: call display_font_vga50
L_6f3b: jmp short L_6f23
