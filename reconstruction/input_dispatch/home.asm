; Recovered PCPlus 2.01 input/control instructions; see docs/INPUT_DISPATCH.md.
BITS 16
CPU 8086
%ifdef INPUT_DISPATCH_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_control_home
extern screen_set_cursor
extern screen_adjust_attribute_boundary
extern screen_attribute_checks
%define short
%else
ORG 0x1f56
%define screen_set_cursor 0x1bbe
%define screen_adjust_attribute_boundary 0x2adc
%define screen_attribute_checks 0x3734
%endif
%include "encodings.inc"
terminal_control_home:
L_1f56: sub_load ax,ax
L_1f58: sub_load dx,dx
L_1f5a: call screen_set_cursor
L_1f5d: cmp word [screen_attribute_checks],0x0
L_1f62: jz short L_1f6e
L_1f64: mov ax,0x1
L_1f67: push ax
L_1f68: sub_load ax,ax
L_1f6a: push ax
L_1f6b: call screen_adjust_attribute_boundary
L_1f6e: ret
