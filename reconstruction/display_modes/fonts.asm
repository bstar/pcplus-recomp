; Exact PCPlus2.01 display-mode service. See provenance.json.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef DISPLAY_MODES_OMF
SEGMENT _TEXT public class=CODE use16
global display_font_ega14
global display_font_ega8
global display_font_vga16
global display_font_vga14
global display_font_vga43
global display_font_vga50
global display_install_font
extern display_cursor_eight
extern display_font_reset
extern display_scanline_capable
extern display_scanlines
%else
ORG 0x7e72
%define display_scanline_capable 0x7a70
%define display_font_reset 0x7f0f
%define display_scanlines 0x7ee8
%define display_cursor_eight 0x7f2b
%endif
display_font_ega14:
L_7e72: mov al,0x11
L_7e74: call L_7eb4
L_7e77: ret
display_font_ega8:
L_7e78: mov al,0x12
L_7e7a: call L_7eb4
L_7e7d: ret
display_font_vga16:
L_7e7e: mov bl,0x2
L_7e80: call display_scanlines
L_7e83: call display_font_reset
L_7e86: call display_cursor_eight
L_7e89: ret
display_font_vga14:
L_7e8a: mov bl,0x2
L_7e8c: call display_scanlines
L_7e8f: call display_font_reset
L_7e92: mov al,0x11
L_7e94: call L_7eb4
L_7e97: ret
display_font_vga43:
L_7e98: mov bl,0x1
L_7e9a: call display_scanlines
L_7e9d: call display_font_reset
L_7ea0: mov al,0x12
L_7ea2: call L_7eb4
L_7ea5: ret
display_font_vga50:
L_7ea6: mov bl,0x2
L_7ea8: call display_scanlines
L_7eab: call display_font_reset
L_7eae: mov al,0x12
L_7eb0: call L_7eb4
L_7eb3: ret
display_install_font:
L_7eb4: push es
L_7eb5: push ax
L_7eb6: xor_load bx,bx
L_7eb8: mov es,bx
L_7eba: cmp word [display_scanline_capable],0x0
L_7ebf: jnz short L_7ecd
L_7ec1: cmp al,0x11
L_7ec3: jz short L_7ecd
L_7ec5: or byte [es:0x487],0x1
L_7ecb: jmp short L_7ed3
L_7ecd: and byte [es:0x487],0xfe
L_7ed3: pop ax
L_7ed4: mov ah,0x11
L_7ed6: int byte 0x10
L_7ed8: cmp word [display_scanline_capable],0x0
L_7edd: jnz short L_7ee6
L_7edf: mov ah,0x1
L_7ee1: mov cx,0x607
L_7ee4: int byte 0x10
L_7ee6: pop es
L_7ee7: ret
