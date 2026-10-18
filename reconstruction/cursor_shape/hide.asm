; Recovered PCPlus 2.01 cursor-shape instructions; see docs/CURSOR_SHAPE.md.
BITS 16
CPU 8086
%ifdef CURSOR_SHAPE_OMF
SEGMENT _TEXT public class=CODE use16
global cursor_shape_hide
extern cursor_shape_bios
extern cursor_shape_visibility_state
%define short
%else
ORG 0x6e5a
%define cursor_shape_bios 0x7e58
%define cursor_shape_visibility_state 0x7a6c
%endif
%include "encodings.inc"
cursor_shape_hide:
L_6e5a: mov word [cursor_shape_visibility_state],0x0
L_6e60: mov bx,0x1
L_6e63: jmp near cursor_shape_bios
