; Recovered PCPlus 2.01 cursor instructions; see docs/SCREEN.md.
BITS 16
CPU 8086
%ifdef SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
global screen_cursor_down
extern screen_set_cursor
extern screen_width_transition
extern screen_cursor_column
extern screen_cursor_row
extern screen_doublewidth_enabled
extern screen_bottom_margin
%define short
%else
ORG 0x1e0c
%define screen_set_cursor 0x1bbe
%define screen_width_transition 0x2a90
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%define screen_doublewidth_enabled 0xd122
%define screen_bottom_margin 0xcee4
%endif
%include "encodings.inc"
screen_cursor_down:
L_1e0c: mov ax,[screen_bottom_margin]
L_1e0f: cmp [screen_cursor_row],ax
L_1e13: jnl short L_1e2e
L_1e15: cmp word [screen_doublewidth_enabled],0x0
L_1e1a: jz short L_1e23
L_1e1c: mov ax,0x1
L_1e1f: push ax
L_1e20: call screen_width_transition
L_1e23: mov ax,[screen_cursor_row]
L_1e26: inc ax
L_1e27: mov dx,[screen_cursor_column]
L_1e2b: call screen_set_cursor
L_1e2e: ret
