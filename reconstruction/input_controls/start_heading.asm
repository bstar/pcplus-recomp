; Recovered PCPlus 2.01 input controls; see docs/INPUT_CONTROLS.md.
BITS 16
CPU 8086
%ifdef INPUT_CONTROLS_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_control_0e62
extern screen_set_cursor
extern terminal_control_mode_9026
%define short
%else
ORG 0xe62
%define screen_set_cursor 0x1bbe
%define terminal_control_mode_9026 0x9026
%endif
%include "encodings.inc"
terminal_control_0e62:
L_0e62: cmp word [terminal_control_mode_9026],0x0
L_0e67: jz short L_0e6f
L_0e69: sub_load ax,ax
L_0e6b: cwd
L_0e6c: call screen_set_cursor
L_0e6f: ret
