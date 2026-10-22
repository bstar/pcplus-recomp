; Exact PCPlus2.01 notice window service; numerical facts in provenance.json.
BITS 16
CPU 8086
%ifdef NOTICE_WINDOW_OMF
SEGMENT _TEXT public class=CODE use16
global window_cell
extern window_offset8
extern window_write
%define short
%else
ORG 32610
%define window_offset8 32258
%define window_write 27828
%endif
%include "encodings.inc"
window_cell:
L_7f62: push bp
L_7f63: mov_load bp,sp
L_7f65: mov dx,[bp+0x4]
L_7f68: call window_offset8
L_7f6b: push word [bp+0x6]
L_7f6e: push ax
L_7f6f: call window_write
L_7f72: pop bp
L_7f73: ret word 0x4
