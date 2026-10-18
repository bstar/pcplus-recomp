; Recovered PCPlus 2.01 cursor-shape instructions; see docs/CURSOR_SHAPE.md.
BITS 16
CPU 8086
%ifdef CURSOR_SHAPE_OMF
SEGMENT _TEXT public class=CODE use16
global cursor_shape_show
extern cursor_shape_bios
extern cursor_shape_visibility_state
%define short
%else
ORG 0x6dca
%define cursor_shape_bios 0x7e58
%define cursor_shape_visibility_state 0x7a6c
%endif
%include "encodings.inc"
cursor_shape_show:
L_6dca: cmp word [cursor_shape_visibility_state],0x1
L_6dcf: jg short L_6ddc
L_6dd1: mov word [cursor_shape_visibility_state],0x1
L_6dd7: xor_load bx,bx
L_6dd9: jmp near cursor_shape_bios
L_6ddc: ret
