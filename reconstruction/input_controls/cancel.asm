; Recovered PCPlus 2.01 input controls; see docs/INPUT_CONTROLS.md.
BITS 16
CPU 8086
%ifdef INPUT_CONTROLS_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_control_11a8
extern terminal_control_b9eb
extern terminal_control_6dca
extern screen_cursor_right
extern terminal_control_aad9
extern screen_cursor_left
extern text_write_bios
extern terminal_control_0dae
extern terminal_control_bb83
extern ansi_unread_byte
extern terminal_control_mode_9026
extern terminal_newline_mode_9020
extern terminal_tab_wrap
extern terminal_control_mode_1fb0
extern attributes_current
%define short
%else
ORG 0x11a8
%define terminal_control_b9eb 0xb9eb
%define terminal_control_6dca 0x6dca
%define screen_cursor_right 0x1ea0
%define terminal_control_aad9 0xaad9
%define screen_cursor_left 0x1e30
%define text_write_bios 0x6c4a
%define terminal_control_0dae 0xdae
%define terminal_control_bb83 0xbb83
%define ansi_unread_byte 0xabde
%define terminal_control_mode_9026 0x9026
%define terminal_newline_mode_9020 0x9020
%define terminal_tab_wrap 0x903e
%define terminal_control_mode_1fb0 0x1fb0
%define attributes_current 0x1f70
%endif
%include "encodings.inc"
terminal_control_11a8:
L_11a8: cmp word [terminal_tab_wrap],0x0
L_11ad: jz short L_11b4
L_11af: call terminal_control_b9eb
L_11b2: ret
L_11b3: nop
L_11b4: cmp word [terminal_control_mode_9026],0x0
L_11b9: jz short L_11c0
L_11bb: call terminal_control_6dca
L_11be: ret
L_11bf: nop
L_11c0: cmp word [terminal_newline_mode_9020],0x0
L_11c5: jz short L_11cc
L_11c7: call screen_cursor_right
L_11ca: ret
L_11cb: nop
L_11cc: cmp word [terminal_control_mode_1fb0],0x0
L_11d1: jz short L_123b
L_11d3: mov ax,0x1
L_11d6: push ax
L_11d7: call terminal_control_aad9
L_11da: cmp ax,strict word 0x42
L_11dd: jnz short L_1238
L_11df: mov ax,0x1
L_11e2: push ax
L_11e3: call terminal_control_aad9
L_11e6: cmp ax,strict word 0x30
L_11e9: jnz short L_1235
L_11eb: mov ax,0x1
L_11ee: push ax
L_11ef: call terminal_control_aad9
L_11f2: cmp ax,strict word 0x30
L_11f5: jnz short L_1232
L_11f7: call screen_cursor_left
L_11fa: mov al,0x20
L_11fc: push ax
L_11fd: push word [attributes_current]
L_1201: call text_write_bios
L_1204: call screen_cursor_left
L_1207: mov al,0x20
L_1209: push ax
L_120a: push word [attributes_current]
L_120e: call text_write_bios
L_1211: mov ax,0x1
L_1214: push ax
L_1215: call terminal_control_0dae
L_1218: add sp,0x2
L_121b: sub_load ax,ax
L_121d: push ax
L_121e: mov ax,0x1
L_1221: push ax
L_1222: call terminal_control_bb83
L_1225: add sp,0x4
L_1228: sub_load ax,ax
L_122a: push ax
L_122b: call terminal_control_0dae
L_122e: add sp,0x2
L_1231: ret
L_1232: call ansi_unread_byte
L_1235: call ansi_unread_byte
L_1238: call ansi_unread_byte
L_123b: ret
