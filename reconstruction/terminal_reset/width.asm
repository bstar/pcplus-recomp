; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_reset_width
extern screen_viewport_active
extern screen_attribute_row_bytes
extern screen_last_column
extern erase_cell_count
%define short
%else
ORG 0x2a36
%define screen_viewport_active 0x3256
%define screen_attribute_row_bytes 0x325a
%define screen_last_column 0x3258
%define erase_cell_count 0x325c
%endif
%include "encodings.inc"
terminal_reset_width:
L_2a36: push bp
L_2a37: mov_load bp,sp
L_2a39: cmp word [bp+0x4],0x0
L_2a3d: jz short L_2a54
L_2a3f: mov word [erase_cell_count],0xc60
L_2a45: mov word [screen_last_column],0x83
L_2a4b: mov word [screen_attribute_row_bytes],0x84
L_2a51: pop bp
L_2a52: ret
L_2a53: nop
L_2a54: mov word [erase_cell_count],0x780
L_2a5a: mov word [screen_last_column],0x4f
L_2a60: mov word [screen_attribute_row_bytes],0x50
L_2a66: mov word [screen_viewport_active],0x1
L_2a6c: pop bp
L_2a6d: ret
