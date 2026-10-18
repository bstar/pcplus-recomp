; Recovered PCPlus 2.01 terminal reset instructions; see docs/TERMINAL_RESET.md.
BITS 16
CPU 8086
%ifdef TERMINAL_RESET_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_reset_clear_shadow
extern erase_far_fill
extern screen_viewport_enabled
extern attributes_normal_value
extern erase_shadow_offset
extern erase_shadow_segment
extern reset_shadow_bytes
%define short
%else
ORG 0x27ea
%define erase_far_fill 0x63fa
%define screen_viewport_enabled 0xcdfa
%define attributes_normal_value 0x1d32
%define erase_shadow_offset 0x5dea
%define erase_shadow_segment 0x5dec
%define reset_shadow_bytes 0xce02
%endif
%include "encodings.inc"
terminal_reset_clear_shadow:
L_27ea: cmp word [screen_viewport_enabled],0x0
L_27ef: jz short L_2809
L_27f1: push word [erase_shadow_segment]
L_27f5: push word [erase_shadow_offset]
L_27f9: mov ax,[attributes_normal_value]
L_27fc: or ah,0x20
L_27ff: push ax
L_2800: mov ax,[reset_shadow_bytes]
L_2803: shr ax,1
L_2805: push ax
L_2806: call erase_far_fill
L_2809: ret
