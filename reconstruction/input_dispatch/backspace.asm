; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_backspace
extern terminal_control_home
extern screen_set_cursor
extern screen_cursor_left
extern text_write_bios
extern screen_cursor_column
extern screen_cursor_row
extern terminal_backspace_mode_9058
extern terminal_backspace_erases
extern screen_line_flags
extern attributes_current
extern terminal_newline_mode_9020
%define short
%else
ORG 0xeea
%define terminal_control_home 0x1f56
%define screen_set_cursor 0x1bbe
%define screen_cursor_left 0x1e30
%define text_write_bios 0x6c4a
%define screen_cursor_column 0x399e
%define screen_cursor_row 0x399c
%define terminal_backspace_mode_9058 0x9058
%define terminal_backspace_erases 0x1d26
%define screen_line_flags 0xcf86
%define attributes_current 0x1f70
%define terminal_newline_mode_9020 0x9020
%endif
%include "encodings.inc"
terminal_backspace:
L_0eea: call screen_cursor_left
L_0eed: cmp word [terminal_backspace_mode_9058],0x0
L_0ef2: jz short L_0f32
L_0ef4: cmp byte [terminal_backspace_erases],0x0
L_0ef9: jz short L_0f3c
L_0efb: mov bx,[screen_cursor_row]
L_0eff: test byte [bx+screen_line_flags],0x40
L_0f04: jz short L_0f26
L_0f06: mov dx,[screen_cursor_column]
L_0f0a: inc dx
L_0f0b: mov_load ax,bx
L_0f0d: call screen_set_cursor
L_0f10: mov al,0x20
L_0f12: push ax
L_0f13: push word [attributes_current]
L_0f17: call text_write_bios
L_0f1a: mov dx,[screen_cursor_column]
L_0f1e: dec dx
L_0f1f: mov ax,[screen_cursor_row]
L_0f22: call screen_set_cursor
L_0f25: ret
L_0f26: mov al,0x20
L_0f28: push ax
L_0f29: push word [attributes_current]
L_0f2d: call text_write_bios
L_0f30: ret
L_0f31: nop
L_0f32: cmp word [terminal_newline_mode_9020],0x0
L_0f37: jz short L_0f3c
L_0f39: call terminal_control_home
L_0f3c: ret
