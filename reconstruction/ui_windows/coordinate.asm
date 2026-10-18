; Recovered PCPlus 2.01 window snapshot instructions; see docs/UI_WINDOWS.md.
BITS 16
CPU 8086
%ifdef UI_WINDOWS_OMF
SEGMENT _TEXT public class=CODE use16
global ui_coordinate_offset
extern screen_columns
%define short
%else
ORG 0x7e02
%define screen_columns 0x7a72
%endif
%include "encodings.inc"
ui_coordinate_offset:
L_7e02: mov al,[screen_columns]
L_7e05: mul dh
L_7e07: xor_load dh,dh
L_7e09: add_load ax,dx
L_7e0b: shl ax,1
L_7e0d: ret
