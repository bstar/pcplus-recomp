; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_vertical
extern window_offset8
extern window_stride
%define short
%else
ORG 32586
%define window_offset8 32258
%define window_stride 32820
%endif
%include "encodings.inc"
window_vertical:
L_7f4a: push bp
L_7f4b: mov_load bp,sp
L_7f4d: mov dx,[bp+0x6]
L_7f50: call window_offset8
L_7f53: push word [bp+0x8]
L_7f56: push ax
L_7f57: push word [bp+0x4]
L_7f5a: call window_stride
L_7f5d: pop bp
L_7f5e: ret word 0x6
