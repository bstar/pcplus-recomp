; Recovered PCPlus 2.01 scroll instructions; see docs/LINE_EDIT.md.
BITS 16
CPU 8086
%ifdef LINE_EDIT_OMF
SEGMENT _TEXT public class=CODE use16
global csi_wait_control_n
extern uart_receive_byte
extern keyboard_peek
extern keyboard_read
%define short
%else
ORG 0xdaf2
%define uart_receive_byte 0xaa65
%define keyboard_peek 0x651a
%define keyboard_read 0x64fe
%endif
%include "encodings.inc"
csi_wait_control_n:
L_daf2: push bp
L_daf3: mov_load bp,sp
L_daf5: call uart_receive_byte
L_daf8: cmp ax,strict word 0xe
L_dafb: jz short L_db0c
L_dafd: call keyboard_peek
L_db00: or_load ax,ax
L_db02: jz short L_daf5
L_db04: call keyboard_read
L_db07: cmp ax,strict word 0x1b
L_db0a: jnz short L_daf5
L_db0c: mov_load sp,bp
L_db0e: pop bp
L_db0f: ret
