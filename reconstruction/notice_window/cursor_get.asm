; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_cursor_get
extern window_state_7a66
%define short
%else
ORG 31118
%define window_state_7a66 31334
%endif
%include "encodings.inc"
window_cursor_get:
L_798e: cmp word [window_state_7a66],0x0
L_7993: jnz short L_799f
L_7995: mov ax,0x40
L_7998: mov es,ax
L_799a: mov ax,[es:0x50]
L_799e: ret
L_799f: xor_load bh,bh
L_79a1: mov ah,0x3
L_79a3: int byte 0x10
L_79a5: mov_load ax,dx
L_79a7: ret
