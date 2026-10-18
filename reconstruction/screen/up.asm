; Recovered PCPlus 2.01 cursor instructions; see docs/SCREEN.md.
BITS 16
CPU 8086
%ifdef SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
global screen_cursor_up
extern screen_set_cursor
extern screen_width_transition
extern screen_adjust_attribute_boundary
extern screen_attribute_offset
extern screen_cursor_column
extern screen_cursor_row
extern screen_top_margin
extern screen_doublewidth_enabled
extern screen_last_row
extern screen_vertical_attribute_check
extern screen_attribute_checks
extern screen_attributes_base
extern screen_cursor_wrap
%define short
%else
ORG 0x1efc
%define screen_set_cursor 0x1bbe
%define screen_width_transition 0x2a90
%define screen_adjust_attribute_boundary 0x2adc
%define screen_attribute_offset 0x3346
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%define screen_top_margin 0xceb0
%define screen_doublewidth_enabled 0xd122
%define screen_last_row 0xce3a
%define screen_vertical_attribute_check 0x9018
%define screen_attribute_checks 0x3734
%define screen_attributes_base 0x39c4
%define screen_cursor_wrap 0x900c
%endif
%include "encodings.inc"
screen_cursor_up:
L_1efc: push si
L_1efd: mov ax,[screen_top_margin]
L_1f00: cmp [screen_cursor_row],ax
L_1f04: jng short L_1f1a
L_1f06: cmp word [screen_doublewidth_enabled],0x0
L_1f0b: jz short L_1f14
L_1f0d: mov ax,0xffff
L_1f10: push ax
L_1f11: call screen_width_transition
L_1f14: dec word [screen_cursor_row]
L_1f18: jmp short L_1f27
L_1f1a: cmp word [screen_cursor_wrap],0x0
L_1f1f: jz short L_1f27
L_1f21: mov ax,[screen_last_row]
L_1f24: mov [screen_cursor_row],ax
L_1f27: mov ax,[screen_cursor_row]
L_1f2a: mov dx,[screen_cursor_column]
L_1f2e: call screen_set_cursor
L_1f31: cmp word [screen_vertical_attribute_check],0x0
L_1f36: jz short L_1f53
L_1f38: cmp word [screen_attribute_checks],0x0
L_1f3d: jz short L_1f53
L_1f3f: mov si,[screen_attribute_offset]
L_1f43: mov bx,[screen_attributes_base]
L_1f47: test byte [bx+si],0x81
L_1f4a: jz short L_1f53
L_1f4c: sub_load ax,ax
L_1f4e: push ax
L_1f4f: push si
L_1f50: call screen_adjust_attribute_boundary
L_1f53: pop si
L_1f54: ret
