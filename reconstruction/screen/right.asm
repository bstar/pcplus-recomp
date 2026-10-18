; Recovered PCPlus 2.01 cursor instructions; see docs/SCREEN.md.
BITS 16
CPU 8086
%ifdef SCREEN_OMF
SEGMENT _TEXT public class=CODE use16
global screen_cursor_right
extern screen_set_cursor
extern screen_adjust_attribute_boundary
extern screen_wrap_forward
extern screen_attribute_offset
extern screen_cursor_column
extern screen_cursor_row
extern screen_attribute_checks
extern screen_attributes_base
extern screen_last_column
extern screen_line_flags
extern screen_cursor_wrap
%define short
%else
ORG 0x1ea0
%define screen_set_cursor 0x1bbe
%define screen_adjust_attribute_boundary 0x2adc
%define screen_wrap_forward 0x12c8
%define screen_attribute_offset 0x3346
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%define screen_attribute_checks 0x3734
%define screen_attributes_base 0x39c4
%define screen_last_column 0x3258
%define screen_line_flags 0xcf86
%define screen_cursor_wrap 0x900c
%endif
%include "encodings.inc"
screen_cursor_right:
L_1ea0: push si
L_1ea1: mov ax,[screen_last_column]
L_1ea4: cmp [screen_cursor_column],ax
L_1ea8: jnc short L_1ed4
L_1eaa: mov bx,[screen_cursor_row]
L_1eae: test byte [bx+screen_line_flags],0x40
L_1eb3: jz short L_1ec4
L_1eb5: dec ax
L_1eb6: cmp ax,[screen_cursor_column]
L_1eba: jna short L_1ec8
L_1ebc: add word [screen_cursor_column],0x2
L_1ec1: jmp short L_1ec8
L_1ec3: nop
L_1ec4: inc word [screen_cursor_column]
L_1ec8: mov_load ax,bx
L_1eca: mov dx,[screen_cursor_column]
L_1ece: call screen_set_cursor
L_1ed1: jmp short L_1ede
L_1ed3: nop
L_1ed4: cmp word [screen_cursor_wrap],0x0
L_1ed9: jz short L_1ede
L_1edb: call screen_wrap_forward
L_1ede: cmp word [screen_attribute_checks],0x0
L_1ee3: jz short L_1efa
L_1ee5: mov si,[screen_attribute_offset]
L_1ee9: mov bx,[screen_attributes_base]
L_1eed: test byte [bx+si],0x81
L_1ef0: jz short L_1efa
L_1ef2: mov ax,0x1
L_1ef5: push ax
L_1ef6: push si
L_1ef7: call screen_adjust_attribute_boundary
L_1efa: pop si
L_1efb: ret
