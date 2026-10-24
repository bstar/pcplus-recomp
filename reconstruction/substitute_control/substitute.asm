; Recovered PCPlus2.01 SUB control,1248..127c:53 exact baseline bytes.
; REA ev_569fc63c4a44ed77abaf3a0282ecdf4f47fc71a15851e3c4e72dcaa2db68f520.
BITS 16
CPU 8086
%ifdef SUBSTITUTE_CONTROL_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_control_1248
extern csi_terminal_id,render_direct_output,terminal_control_mode_9026,terminal_newline_mode_9020
extern terminal_substitute_profile_ge20,terminal_formfeed_profile_6_7,screen_cursor_up,screen_cursor_down
%define short
%else
ORG 0x1248
%define csi_terminal_id 0x1d18
%define render_direct_output 0x9056
%define terminal_control_mode_9026 0x9026
%define terminal_newline_mode_9020 0x9020
%define terminal_substitute_profile_ge20 0xbb77
%define terminal_formfeed_profile_6_7 0xba4b
%define screen_cursor_up 0x1efc
%define screen_cursor_down 0x1e0c
%endif
terminal_control_1248:
 cmp word [csi_terminal_id],0x14
 jl short .below20
 mov ax,0x3b
 push ax
 call terminal_substitute_profile_ge20
 add sp,2
 ret
.below20:
 cmp word [render_direct_output],0
 jz short .not_direct
 call terminal_formfeed_profile_6_7
 ret
 nop
.not_direct:
 cmp word [terminal_control_mode_9026],0
 jz short .not_up
 call screen_cursor_up
 ret
 nop
.not_up:
 cmp word [terminal_newline_mode_9020],0
 jz short .done
 call screen_cursor_down
.done:
 ret
