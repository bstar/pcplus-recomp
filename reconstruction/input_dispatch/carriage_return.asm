; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_carriage_return
extern terminal_log_character
extern terminal_history_character
extern screen_set_cursor
extern scroll_up
extern terminal_cr_adds_lf
extern screen_cursor_row
extern screen_last_row
extern scroll_enabled
%define short
%else
ORG 0x1002
%define terminal_log_character 0x9b6
%define terminal_history_character 0x5832
%define screen_set_cursor 0x1bbe
%define scroll_up 0x1fc4
%define terminal_cr_adds_lf 0x1d24
%define screen_cursor_row 0x399c
%define screen_last_row 0xce3a
%define scroll_enabled 0x1d22
%endif
%include "encodings.inc"
terminal_carriage_return:
L_1002: cmp word [terminal_cr_adds_lf],0x0
L_1007: jz short L_1026
L_1009: mov ax,[screen_cursor_row]
L_100c: cmp [screen_last_row],ax
L_1010: jg short L_1022
L_1012: cmp word [scroll_enabled],0x0
L_1017: jz short L_101c
L_1019: call scroll_up
L_101c: mov ax,[screen_last_row]
L_101f: jmp short L_1029
L_1021: nop
L_1022: inc ax
L_1023: jmp short L_1029
L_1025: nop
L_1026: mov ax,[screen_cursor_row]
L_1029: sub_load dx,dx
L_102b: call screen_set_cursor
L_102e: mov ax,0xd
L_1031: push ax
L_1032: call terminal_history_character
L_1035: mov ax,0xd
L_1038: push ax
L_1039: call terminal_log_character
L_103c: add sp,0x2
L_103f: ret
