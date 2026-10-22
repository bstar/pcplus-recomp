; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_offset16
extern window_state_7a72
%define short
%else
ORG 31168
%define window_state_7a72 31346
%endif
%include "encodings.inc"
window_offset16:
L_79c0: mov_load bx,sp
L_79c2: mov dx,[bx+0x2]
L_79c5: mov ax,[window_state_7a72]
L_79c8: mul dh
L_79ca: xor_load dh,dh
L_79cc: add_load ax,dx
L_79ce: shl ax,1
L_79d0: ret word 0x2
