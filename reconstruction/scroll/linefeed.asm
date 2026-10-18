; Recovered PCPlus 2.01 scroll instructions; see docs/SCROLL.md.
BITS 16
CPU 8086
%ifdef SCROLL_OMF
SEGMENT _TEXT public class=CODE use16
global screen_linefeed
extern scroll_up
extern screen_set_cursor
extern screen_width_transition
extern screen_adjust_attribute_boundary
extern scroll_suppress_next_linefeed
extern screen_cursor_row
extern screen_cursor_column
extern screen_cursor_wrap
extern screen_attribute_checks
extern screen_attribute_offset
extern screen_attributes_base
extern screen_last_row
extern csi_last_row
extern screen_doublewidth_enabled
extern screen_vertical_attribute_check
extern scroll_enabled
%define short
%else
ORG 0x1d88
%define scroll_up 0x1fc4
%define screen_set_cursor 0x1bbe
%define screen_width_transition 0x2a90
%define screen_adjust_attribute_boundary 0x2adc
%define scroll_suppress_next_linefeed 0x3340
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define screen_cursor_wrap 0x900c
%define screen_attribute_checks 0x3734
%define screen_attribute_offset 0x3346
%define screen_attributes_base 0x39c4
%define screen_last_row 0xce3a
%define csi_last_row 0x334a
%define screen_doublewidth_enabled 0xd122
%define screen_vertical_attribute_check 0x9018
%define scroll_enabled 0x1d22
%endif
%include "encodings.inc"
screen_linefeed:
L_1d88: push si
L_1d89: cmp word [scroll_suppress_next_linefeed],0x0
L_1d8e: jz short L_1d98
L_1d90: mov word [scroll_suppress_next_linefeed],0x0
L_1d96: pop si
L_1d97: ret
L_1d98: mov ax,[screen_last_row]
L_1d9b: cmp [screen_cursor_row],ax
L_1d9f: jnz short L_1dc2
L_1da1: cmp word [scroll_enabled],0x0
L_1da6: jz short L_1db2
L_1da8: call scroll_up
L_1dab: mov bx,[screen_last_row]
L_1daf: jmp short L_1ddd
L_1db1: nop
L_1db2: cmp word [screen_cursor_wrap],0x0
L_1db7: jz short L_1ddd
L_1db9: mov word [screen_cursor_row],0x0
L_1dbf: jmp short L_1ddd
L_1dc1: nop
L_1dc2: mov ax,[screen_cursor_row]
L_1dc5: cmp [csi_last_row],ax
L_1dc9: jng short L_1ddd
L_1dcb: cmp word [screen_doublewidth_enabled],0x0
L_1dd0: jz short L_1dd9
L_1dd2: mov ax,0x1
L_1dd5: push ax
L_1dd6: call screen_width_transition
L_1dd9: inc word [screen_cursor_row]
L_1ddd: mov ax,[screen_cursor_row]
L_1de0: mov dx,[screen_cursor_column]
L_1de4: call screen_set_cursor
L_1de7: cmp word [screen_vertical_attribute_check],0x0
L_1dec: jz short L_1e0a
L_1dee: cmp word [screen_attribute_checks],0x0
L_1df3: jz short L_1e0a
L_1df5: mov si,[screen_attribute_offset]
L_1df9: mov bx,[screen_attributes_base]
L_1dfd: test byte [bx+si],0x81
L_1e00: jz short L_1e0a
L_1e02: mov ax,0x1
L_1e05: push ax
L_1e06: push si
L_1e07: call screen_adjust_attribute_boundary
L_1e0a: pop si
L_1e0b: ret
