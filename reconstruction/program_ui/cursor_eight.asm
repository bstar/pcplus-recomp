; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_cursor_eight
extern display_cursor_start
extern display_cursor_end
%define short
%else
ORG 32555
%define display_cursor_start 31368
%define display_cursor_end 31370
%endif
%include "encodings.inc"
display_cursor_eight:
L_7f2b: xor_load ax,ax
L_7f2d: mov es,ax
L_7f2f: and byte [es:0x487],0xfe
L_7f35: mov ah,0x1
L_7f37: mov cx,0x607
L_7f3a: int byte 0x10
L_7f3c: mov word [display_cursor_start],0x6
L_7f42: mov word [display_cursor_end],0x7
L_7f48: ret
