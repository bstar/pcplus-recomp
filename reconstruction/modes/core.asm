; Recovered PCPlus2.01 mode handlers; exact flat and symbolic OMF tables.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef MODES_OMF
SEGMENT _TEXT public class=CODE use16
global csi_set_modes,csi_reset_modes
extern csi_report_private_prefix, ansi_parameter_count, ansi_parameters, ansi_private, terminal_mode_372c, csi_scroll_bottom, csi_origin_bottom, csi_origin_mode, csi_scroll_top, csi_origin_row, cursor_state_value_1d20, modes_value_1d1a, modes_value_3980, modes_value_3982, modes_cursor_flags, csi_terminal_id, csi_previous_terminal_id, csi_last_row, csi_wrap_pending
extern modes_keyboard_map, modes_screen_width, screen_set_cursor, screen_viewport_refresh, modes_cursor_shape, csi_reset_terminal
%else
ORG 0xde98
%define csi_report_private_prefix 0x904c
%define ansi_parameter_count 0xcb5c
%define ansi_parameters 0xcb3c
%define ansi_private 0xceac
%define terminal_mode_372c 0x372c
%define csi_scroll_bottom 0xce3a
%define csi_origin_bottom 0xcee4
%define csi_origin_mode 0xcdd2
%define csi_scroll_top 0xce0e
%define csi_origin_row 0xceb0
%define cursor_state_value_1d20 0x1d20
%define modes_value_1d1a 0x1d1a
%define modes_value_3980 0x3980
%define modes_value_3982 0x3982
%define modes_cursor_flags 0x333e
%define csi_terminal_id 0x1d18
%define csi_previous_terminal_id 0x321e
%define csi_last_row 0x334a
%define csi_wrap_pending 0x3342
%define modes_keyboard_map 0xb4e
%define modes_screen_width 0x2a6e
%define screen_set_cursor 0x1bbe
%define screen_viewport_refresh 0x2fb8
%define modes_cursor_shape 0x2f78
%define csi_reset_terminal 0x20a4
%endif
csi_set_modes:
L_de98: push di
L_de99: push si
L_de9a: cmp word [csi_report_private_prefix], 0x0
L_de9f: jz L_dea4
L_dea1: jmp near L_df7b
L_dea4: sub_load di, di
L_dea6: cmp word [ansi_parameter_count], di
L_deaa: jg L_deaf
L_deac: jmp near L_df7b
L_deaf: mov si, ansi_parameters
L_deb2: mov ax, word [si]
L_deb4: dec ax
L_deb5: cmp ax, strict word 0x18
L_deb8: jbe L_debd
L_deba: jmp near L_df6f
L_debd: shl ax, 0x1
L_debf: xchg ax, bx
L_dec0: jmp word cs:[bx + csi_set_modes_table]
nop ; original alignment before mode jump table
csi_set_modes_table:
 dw L_def8 ; mode 1
 dw L_df6f ; mode 2
 dw L_df02 ; mode 3
 dw L_df12 ; mode 4
 dw L_df6f ; mode 5
 dw L_df22 ; mode 6
 dw L_df3c ; mode 7
 dw L_df6f ; mode 8
 dw L_df6f ; mode 9
 dw L_df6f ; mode 10
 dw L_df6f ; mode 11
 dw L_df44 ; mode 12
 dw L_df6f ; mode 13
 dw L_df6f ; mode 14
 dw L_df6f ; mode 15
 dw L_df6f ; mode 16
 dw L_df6f ; mode 17
 dw L_df50 ; mode 18
 dw L_df58 ; mode 19
 dw L_df6f ; mode 20
 dw L_df6f ; mode 21
 dw L_df6f ; mode 22
 dw L_df6f ; mode 23
 dw L_df6f ; mode 24
 dw L_df60 ; mode 25
L_def8: mov ax, 0x4f
L_defb: push ax
L_defc: call modes_keyboard_map
L_deff: jmp short L_df6c
nop ; original alignment instruction
L_df02: cmp word [ansi_private], 0x0
L_df07: jz L_df6f
L_df09: mov ax, 0x1
L_df0c: push ax
L_df0d: call modes_screen_width
L_df10: jmp short L_df6f
L_df12: cmp word [ansi_private], 0x0
L_df17: jnz L_df6f
L_df19: mov word [terminal_mode_372c], 0x1
L_df1f: jmp short L_df6f
nop ; original alignment instruction
L_df22: mov ax, [csi_scroll_bottom]
L_df25: mov [csi_origin_bottom], ax
L_df28: mov word [csi_origin_mode], 0x1
L_df2e: mov ax, [csi_scroll_top]
L_df31: mov [csi_origin_row], ax
L_df34: sub_load dx, dx
L_df36: call screen_set_cursor
L_df39: jmp short L_df6f
nop ; original alignment instruction
L_df3c: mov word [cursor_state_value_1d20], 0x1
L_df42: jmp short L_df6f
L_df44: mov word [modes_value_1d1a], 0x0
L_df4a: call screen_viewport_refresh
L_df4d: jmp short L_df6f
nop ; original alignment instruction
L_df50: mov word [modes_value_3980], 0x1
L_df56: jmp short L_df6f
L_df58: mov word [modes_value_3982], 0x0
L_df5e: jmp short L_df6f
L_df60: or byte [modes_cursor_flags], 0x4
L_df65: push word [modes_cursor_flags]
L_df69: call modes_cursor_shape
L_df6c: add sp, 0x2
L_df6f: inc si
L_df70: inc si
L_df71: inc di
L_df72: cmp word [ansi_parameter_count], di
L_df76: jle L_df7b
L_df78: jmp near L_deb2
L_df7b: pop si
L_df7c: pop di
L_df7d: ret
csi_reset_modes:
L_df7e: push di
L_df7f: push si
L_df80: cmp word [csi_report_private_prefix], 0x0
L_df85: jz L_df8a
L_df87: jmp near L_e081
L_df8a: sub_load di, di
L_df8c: cmp word [ansi_parameter_count], di
L_df90: jg L_df95
L_df92: jmp near L_e081
L_df95: mov si, ansi_parameters
L_df98: mov ax, word [si]
L_df9a: dec ax
L_df9b: cmp ax, strict word 0x18
L_df9e: jbe L_dfa3
L_dfa0: jmp near L_e075
L_dfa3: shl ax, 0x1
L_dfa5: xchg ax, bx
L_dfa6: jmp word cs:[bx + csi_reset_modes_table]
nop ; original alignment before mode jump table
csi_reset_modes_table:
 dw L_dfde ; mode 1
 dw L_dfe8 ; mode 2
 dw L_e004 ; mode 3
 dw L_e014 ; mode 4
 dw L_e075 ; mode 5
 dw L_e024 ; mode 6
 dw L_e03a ; mode 7
 dw L_e075 ; mode 8
 dw L_e075 ; mode 9
 dw L_e075 ; mode 10
 dw L_e075 ; mode 11
 dw L_e044 ; mode 12
 dw L_e075 ; mode 13
 dw L_e075 ; mode 14
 dw L_e075 ; mode 15
 dw L_e075 ; mode 16
 dw L_e075 ; mode 17
 dw L_e056 ; mode 18
 dw L_e05e ; mode 19
 dw L_e075 ; mode 20
 dw L_e075 ; mode 21
 dw L_e075 ; mode 22
 dw L_e075 ; mode 23
 dw L_e075 ; mode 24
 dw L_e066 ; mode 25
L_dfde: mov ax, 0x5b
L_dfe1: push ax
L_dfe2: call modes_keyboard_map
L_dfe5: jmp near L_e072
L_dfe8: cmp word [ansi_private], 0x0
L_dfed: jnz L_dff2
L_dfef: jmp near L_e075
L_dff2: mov ax, [csi_terminal_id]
L_dff5: mov [csi_previous_terminal_id], ax
L_dff8: mov ax, 0x1
L_dffb: mov [csi_terminal_id], ax
L_dffe: push ax
L_dfff: call csi_reset_terminal
L_e002: jmp short L_e072
L_e004: cmp word [ansi_private], 0x0
L_e009: jz L_e075
L_e00b: sub_load ax, ax
L_e00d: push ax
L_e00e: call modes_screen_width
L_e011: jmp short L_e075
nop ; original alignment instruction
L_e014: cmp word [ansi_private], 0x0
L_e019: jnz L_e075
L_e01b: mov word [terminal_mode_372c], 0x0
L_e021: jmp short L_e075
nop ; original alignment instruction
L_e024: mov ax, [csi_last_row]
L_e027: mov [csi_origin_bottom], ax
L_e02a: sub_load ax, ax
L_e02c: mov [csi_origin_row], ax
L_e02f: mov [csi_origin_mode], ax
L_e032: sub_load dx, dx
L_e034: call screen_set_cursor
L_e037: jmp short L_e075
nop ; original alignment instruction
L_e03a: sub_load ax, ax
L_e03c: mov [cursor_state_value_1d20], ax
L_e03f: mov [csi_wrap_pending], ax
L_e042: jmp short L_e075
L_e044: cmp word [ansi_private], 0x0
L_e049: jnz L_e075
L_e04b: mov word [modes_value_1d1a], 0x1
L_e051: call screen_viewport_refresh
L_e054: jmp short L_e075
L_e056: mov word [modes_value_3980], 0x0
L_e05c: jmp short L_e075
L_e05e: mov word [modes_value_3982], 0x1
L_e064: jmp short L_e075
L_e066: and byte [modes_cursor_flags], 0xfb
L_e06b: push word [modes_cursor_flags]
L_e06f: call modes_cursor_shape
L_e072: add sp, 0x2
L_e075: inc si
L_e076: inc si
L_e077: inc di
L_e078: cmp word [ansi_parameter_count], di
L_e07c: jle L_e081
L_e07e: jmp near L_df98
L_e081: pop si
L_e082: pop di
L_e083: ret
