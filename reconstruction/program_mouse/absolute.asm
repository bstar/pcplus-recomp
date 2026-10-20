; Exact native mouse instructions; see provenance.json.
BITS 16
CPU 8086
%ifdef PROGRAM_MOUSE_OMF
SEGMENT _TEXT public class=CODE use16
global mouse_absolute
%define short
%else
ORG 40294
%endif
%include "encodings.inc"
mouse_absolute:
L_9d66: push bp
L_9d67: mov_load bp,sp
L_9d69: mov ax,[bp+0x4]
L_9d6c: cwd
L_9d6d: xor_load ax,dx
L_9d6f: sub_load ax,dx
L_9d71: pop bp
L_9d72: ret
