; Exact native mouse instructions; see provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_MOUSE_OMF
SEGMENT _TEXT public class=CODE use16
global mouse_bind
extern mouse_callback
%define short
%else
ORG 32658
%define mouse_callback 0x8074
%endif
%include "encodings.inc"
mouse_bind:
L_7f92: push cs
L_7f93: pop es
L_7f94: mov dx,mouse_callback
L_7f97: mov cx,0xb
L_7f9a: mov ax,0xc
L_7f9d: int byte 0x33
L_7f9f: ret
