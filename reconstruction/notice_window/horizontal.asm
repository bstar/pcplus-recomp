; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_horizontal
extern window_offset8
extern window_fill
%define short
%else
ORG 31144
%define window_offset8 32258
%define window_fill 27680
%endif
%include "encodings.inc"
window_horizontal:
L_79a8: push bp
L_79a9: mov_load bp,sp
L_79ab: mov dx,[bp+0x6]
L_79ae: call window_offset8
L_79b1: push word [bp+0x8]
L_79b4: push ax
L_79b5: push word [bp+0x4]
L_79b8: call window_fill
L_79bb: pop bp
L_79bc: ret word 0x6
