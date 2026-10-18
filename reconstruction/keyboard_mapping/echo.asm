; Recovered PCPlus 2.01 terminal keyboard mapping instructions; see docs/KEYBOARD_MAPPING.md.
BITS 16
CPU 8086
%ifdef KEYBOARD_MAPPING_OMF
SEGMENT _TEXT public class=CODE use16
global keyboard_mapping_echo,keyboard_mapping_noop
extern keyboard_service_3adb
extern keyboard_state_1d1a
%define short
%else
ORG 0xe4e
%define keyboard_service_3adb 0x3adb
%define keyboard_state_1d1a 0x1d1a
%endif
%include "encodings.inc"
keyboard_mapping_echo:
L_0e4e: push bp
L_0e4f: mov_load bp,sp
L_0e51: cmp word [keyboard_state_1d1a],0x0
L_0e56: jz short L_0e5c
L_0e58: push bx
L_0e59: call keyboard_service_3adb
L_0e5c: mov_load sp,bp
L_0e5e: pop bp
L_0e5f: ret
keyboard_mapping_noop:
L_0e60: ret
