; Exact PCPlus2.01 display service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_DISPLAY_OMF
SEGMENT _TEXT public class=CODE use16
global display_cursor_shape
extern display_cursor_start
extern display_cursor_end
%define short
%else
ORG 32344
%define display_cursor_start 31368
%define display_cursor_end 31370
%endif
%include "encodings.inc"
display_cursor_shape:
L_7e58: mov ax,[display_cursor_start]
L_7e5b: mov dx,[display_cursor_end]
L_7e5f: mov cx,0x5
L_7e62: shl bl,cl
L_7e64: or_load bl,al
L_7e66: mov_load ch,bl
L_7e68: mov_load cl,dl
L_7e6a: mov ah,0x1
L_7e6c: push bp
L_7e6d: int byte 0x10
L_7e6f: pop bp
L_7e70: ret
