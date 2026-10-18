; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_linefeed
extern terminal_log_character
extern terminal_history_character
extern screen_set_cursor
extern screen_linefeed
extern screen_cursor_row
extern terminal_newline_mode_9020
%define short
%else
ORG 0xf3e
%define terminal_log_character 0x9b6
%define terminal_history_character 0x5832
%define screen_set_cursor 0x1bbe
%define screen_linefeed 0x1d88
%define screen_cursor_row 0x399c
%define terminal_newline_mode_9020 0x9020
%endif
%include "encodings.inc"
terminal_linefeed:
L_0f3e: cmp word [terminal_newline_mode_9020],0x0
L_0f43: jz short L_0f4d
L_0f45: mov ax,[screen_cursor_row]
L_0f48: sub_load dx,dx
L_0f4a: call screen_set_cursor
L_0f4d: call screen_linefeed
L_0f50: mov ax,0xa
L_0f53: push ax
L_0f54: call terminal_history_character
L_0f57: mov ax,0xa
L_0f5a: push ax
L_0f5b: call terminal_log_character
L_0f5e: add sp,0x2
L_0f61: ret
