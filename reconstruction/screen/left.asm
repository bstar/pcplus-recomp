; Recovered PCPlus 2.01 cursor instructions; see docs/SCREEN.md.
BITS 16
CPU 8086
%ifdef SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
global screen_cursor_left
extern screen_set_cursor
extern screen_adjust_attribute_boundary
extern screen_attribute_offset
extern screen_cursor_column
extern screen_cursor_row
extern screen_last_row
extern screen_attribute_checks
extern screen_attributes_base
extern screen_last_column
extern screen_line_flags
extern screen_cursor_wrap
extern screen_first_row
extern screen_reverse_wrap_blocked
%define short
%else
ORG 0x1e30
%define screen_set_cursor 0x1bbe
%define screen_adjust_attribute_boundary 0x2adc
%define screen_attribute_offset 0x3346
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%define screen_last_row 0xce3a
%define screen_attribute_checks 0x3734
%define screen_attributes_base 0x39c4
%define screen_last_column 0x3258
%define screen_line_flags 0xcf86
%define screen_cursor_wrap 0x900c
%define screen_first_row 0xce0e
%define screen_reverse_wrap_blocked 0x9038
%endif
%include "encodings.inc"
screen_cursor_left:
L_1e30: push si
L_1e31: cmp word [screen_cursor_column],0x0
L_1e36: jng short L_1e4e
L_1e38: mov bx,[screen_cursor_row]
L_1e3c: mov al,[bx+screen_line_flags]
L_1e40: and al,0x40
L_1e42: cmp al,0x1
L_1e44: sbb_load ax,ax
L_1e46: inc ax
L_1e47: inc ax
L_1e48: sub [screen_cursor_column],ax
L_1e4c: jmp short L_1e78
L_1e4e: cmp word [screen_cursor_wrap],0x0
L_1e53: jz short L_1e78
L_1e55: mov ax,[screen_first_row]
L_1e58: cmp [screen_cursor_row],ax
L_1e5c: jnz short L_1e6e
L_1e5e: cmp word [screen_reverse_wrap_blocked],0x0
L_1e63: jnz short L_1e9d
L_1e65: mov ax,[screen_last_row]
L_1e68: mov [screen_cursor_row],ax
L_1e6b: jmp short L_1e72
L_1e6d: nop
L_1e6e: dec word [screen_cursor_row]
L_1e72: mov ax,[screen_last_column]
L_1e75: mov [screen_cursor_column],ax
L_1e78: mov ax,[screen_cursor_row]
L_1e7b: mov dx,[screen_cursor_column]
L_1e7f: call screen_set_cursor
L_1e82: cmp word [screen_attribute_checks],0x0
L_1e87: jz short L_1e9d
L_1e89: mov si,[screen_attribute_offset]
L_1e8d: mov bx,[screen_attributes_base]
L_1e91: test byte [bx+si],0x81
L_1e94: jz short L_1e9d
L_1e96: sub_load ax,ax
L_1e98: push ax
L_1e99: push si
L_1e9a: call screen_adjust_attribute_boundary
L_1e9d: pop si
L_1e9e: ret
