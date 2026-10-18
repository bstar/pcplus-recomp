; Recovered PCPlus 2.01 input controls; see docs/INPUT_CONTROLS.md.
BITS 16
CPU 8086
%ifdef INPUT_CONTROLS_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_control_0f62
extern screen_set_cursor
extern screen_cursor_up
extern ansi_next_byte
extern screen_linefeed
extern terminal_control_ba33
extern terminal_control_mode_9026
extern csi_terminal_id
extern screen_cursor_row
extern screen_cursor_column
extern terminal_dec_keys
extern terminal_newline_mode_9020
%define short
%else
ORG 0xf62
%define screen_set_cursor 0x1bbe
%define screen_cursor_up 0x1efc
%define ansi_next_byte 0x5ca0
%define screen_linefeed 0x1d88
%define terminal_control_ba33 0xba33
%define terminal_control_mode_9026 0x9026
%define csi_terminal_id 0x1d18
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define terminal_dec_keys 0x8fe8
%define terminal_newline_mode_9020 0x9020
%endif
%include "encodings.inc"
terminal_control_0f62:
L_0f62: cmp word [csi_terminal_id],0x14
L_0f67: jl short L_0f6e
L_0f69: call screen_cursor_up
L_0f6c: ret
L_0f6d: nop
L_0f6e: cmp word [terminal_control_mode_9026],0x0
L_0f73: jz short L_0f96
L_0f75: call ansi_next_byte
L_0f78: or al,0x60
L_0f7a: sub ax,strict word 0x60
L_0f7d: mov [screen_cursor_row],ax
L_0f80: or_load ax,ax
L_0f82: jnl short L_0f8a
L_0f84: mov word [screen_cursor_row],0x0
L_0f8a: mov ax,[screen_cursor_row]
L_0f8d: mov dx,[screen_cursor_column]
L_0f91: call screen_set_cursor
L_0f94: ret
L_0f95: nop
L_0f96: cmp word [terminal_dec_keys],0x0
L_0f9b: jz short L_0fa2
L_0f9d: call screen_linefeed
L_0fa0: ret
L_0fa1: nop
L_0fa2: cmp word [terminal_newline_mode_9020],0x0
L_0fa7: jz short L_0faf
L_0fa9: sub_load ax,ax
L_0fab: push ax
L_0fac: call terminal_control_ba33
L_0faf: ret
