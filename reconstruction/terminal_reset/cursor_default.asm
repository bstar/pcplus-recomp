; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_reset_cursor_default
extern modes_cursor_shape
extern keyboard_state_333e
extern reset_data_1d48
%define short
%else
ORG 0x2518
%define modes_cursor_shape 0x2f78
%define keyboard_state_333e 0x333e
%define reset_data_1d48 0x1d48
%endif
%include "encodings.inc"
terminal_reset_cursor_default:
L_2518: cmp word [reset_data_1d48],0x1
L_251d: sbb_load ax,ax
L_251f: and ax,strict word 0x1
L_2522: add ax,strict word 0x4
L_2525: mov [keyboard_state_333e],ax
L_2528: push ax
L_2529: call modes_cursor_shape
L_252c: add sp,0x2
L_252f: ret
