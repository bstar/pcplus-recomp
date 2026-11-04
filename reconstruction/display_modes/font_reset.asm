; Exact PCPlus2.01 display-mode service. See provenance.json.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef DISPLAY_MODES_OMF
SEGMENT _TEXT public class=CODE use16
global display_font_reset
extern display_font_capable
extern display_mode
%else
ORG 0x7f0f
%define display_font_capable 0x7a6e
%define display_mode 0x7a76
%endif
display_font_reset:
L_7f0f: mov ax,[display_mode]
L_7f12: cmp word [display_font_capable],0x0
L_7f17: jz short L_7f28
L_7f19: or al,0x80
L_7f1b: int byte 0x10
L_7f1d: xor_load ax,ax
L_7f1f: mov es,ax
L_7f21: and byte [es:0x487],0x7f
L_7f27: ret
L_7f28: int byte 0x10
L_7f2a: ret
