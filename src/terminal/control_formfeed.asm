; Recovered PCPlus 2.01 FF helper CS:0fb0..1001, 81 exact baseline bytes.
; REA assembly Evidence ev_d82dc1948d45d5e8c06dc39233f4f83717ed70b5dcbf83e12e4bb07fbfcdd576.
; Baseline SHA256 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS mode aliases describe observed use, not literal hardware color/mono modes.
BITS 16
CPU 8086
%ifdef TERMINAL_CONTROL_FLAT
ORG 0x0fb0
%define csi_terminal_id 0x1d18
%define terminal_tab_mode_8ff8 0x8ff8
%define attributes_monochrome 0x8ff6
%define attributes_color_mode 0xd122
%define terminal_newline_mode_9020 0x9020
%define screen_cursor_right 0x1ea0
%define screen_linefeed 0x1d88
%define terminal_formfeed_profile_6_7 0xba4b
%define attributes_normal 0x1c8c
%define terminal_clear_home 0x24e2
%define terminal_history_character 0x5832
%define terminal_log_character 0x09b6
%else
SEGMENT _TEXT public class=CODE use16
global terminal_control_0fb0
extern csi_terminal_id,terminal_tab_mode_8ff8,attributes_monochrome,attributes_color_mode,terminal_newline_mode_9020
extern screen_cursor_right,screen_linefeed,terminal_formfeed_profile_6_7,attributes_normal,terminal_clear_home
extern terminal_history_character,terminal_log_character
%endif
%include "encodings.inc"
terminal_control_0fb0:
 push bp
 mov_load bp,sp
 cmp word [csi_terminal_id],0x14
 jl .below20
 call screen_cursor_right
 jmp short .record
 nop
.below20:
 cmp word [terminal_tab_mode_8ff8],0
 jz .not_linefeed_profile
.linefeed:
 call screen_linefeed
 jmp short .record
.not_linefeed_profile:
 cmp word [attributes_monochrome],0
 jz .not_profile6_7
 call terminal_formfeed_profile_6_7
 jmp short .record
.not_profile6_7:
 cmp word [attributes_color_mode],0
 jnz .linefeed
 cmp word [terminal_newline_mode_9020],0
 jz .clear
 call attributes_normal
.clear:
 call terminal_clear_home
.record:
 mov ax,12
 push ax
 call terminal_history_character
 mov ax,12
 push ax
 call terminal_log_character
 add sp,2
 mov_load sp,bp
 pop bp
 ret
