; Recovered PCPlus 2.01 reporting routines; not original source.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef REPORTS_OMF
SEGMENT _TEXT public class=CODE use16
global csi_primary_attributes,csi_device_status
extern csi_transmit_string, csi_transmit_byte, csi_report_decimal
extern ansi_parameters, csi_report_private_prefix, ansi_private, screen_cursor_row, screen_cursor_column, csi_origin_row, csi_report_buffer, csi_printer_ready, csi_terminal_id, csi_attributes_table, csi_attributes_prefix, csi_status_ok, csi_cursor_prefix, csi_printer_ok, csi_printer_unavailable
%else
%ifndef REPORTS_REGION
%define REPORTS_REGION 0
%endif
%define csi_transmit_string 0xabac
%define csi_transmit_byte 0xab0b
%define csi_report_decimal 0x8e6c
%define ansi_parameters 0xcb3c
%define csi_report_private_prefix 0x904c
%define ansi_private 0xceac
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define csi_origin_row 0xceb0
%define csi_report_buffer 0xcf2c
%define csi_printer_ready 0x3984
%define csi_terminal_id 0x1d18
%define csi_attributes_table 0x3234
%define csi_attributes_prefix 0x7503
%define csi_status_ok 0x7507
%define csi_cursor_prefix 0x750c
%define csi_printer_ok 0x750f
%define csi_printer_unavailable 0x7516
%endif
%ifdef REPORTS_OMF
%else
%if REPORTS_REGION = 0
ORG 0xdd58
%endif
%endif
%ifdef REPORTS_OMF
%assign REPORTS_EMIT 1
%else
%assign REPORTS_EMIT (REPORTS_REGION = 0)
%endif
%if REPORTS_EMIT
csi_primary_attributes:
L_dd58: mov ax, csi_attributes_prefix
L_dd5b: push ax
L_dd5c: call csi_transmit_string
L_dd5f: mov bx, word [csi_terminal_id]
L_dd63: shl bx, 0x1
L_dd65: push word [bx + csi_attributes_table]
L_dd69: call csi_transmit_string
L_dd6c: mov ax, 0x63
L_dd6f: push ax
L_dd70: call csi_transmit_byte
L_dd73: ret
%endif
%ifdef REPORTS_OMF
%else
%if REPORTS_REGION = 1
ORG 0xde04
%endif
%endif
%ifdef REPORTS_OMF
%assign REPORTS_EMIT 1
%else
%assign REPORTS_EMIT (REPORTS_REGION = 1)
%endif
%if REPORTS_EMIT
csi_device_status:
L_de04: cmp word [ansi_parameters], 0x5
L_de09: jnz L_de12
L_de0b: mov ax, csi_status_ok
L_de0e: push ax
L_de0f: call csi_transmit_string
L_de12: cmp word [ansi_parameters], 0x6
L_de17: jnz L_de7d
L_de19: mov ax, csi_cursor_prefix
L_de1c: push ax
L_de1d: call csi_transmit_string
L_de20: cmp word [csi_report_private_prefix], 0x0
L_de25: jz L_de3c
L_de27: cmp word [ansi_private], 0x0
L_de2c: jz L_de3c
L_de2e: mov ax, 0x30
L_de31: push ax
L_de32: call csi_transmit_byte
L_de35: mov ax, 0x3b
L_de38: push ax
L_de39: call csi_transmit_byte
L_de3c: mov ax, 0xa
L_de3f: push ax
L_de40: mov cx, csi_report_buffer
L_de43: push cx
L_de44: mov dx, word [screen_cursor_row]
L_de48: sub dx, word [csi_origin_row]
L_de4c: inc dx
L_de4d: push dx
L_de4e: call csi_report_decimal
L_de51: add sp, 0x6
L_de54: push ax
L_de55: call csi_transmit_string
L_de58: mov ax, 0x3b
L_de5b: push ax
L_de5c: call csi_transmit_byte
L_de5f: mov ax, 0xa
L_de62: push ax
L_de63: mov ax, csi_report_buffer
L_de66: push ax
L_de67: mov ax, [screen_cursor_column]
L_de6a: inc ax
L_de6b: push ax
L_de6c: call csi_report_decimal
L_de6f: add sp, 0x6
L_de72: push ax
L_de73: call csi_transmit_string
L_de76: mov ax, 0x52
L_de79: push ax
L_de7a: call csi_transmit_byte
L_de7d: cmp word [ansi_parameters], 0xf
L_de82: jnz L_de97
L_de84: cmp word [csi_printer_ready], 0x0
L_de89: jz L_de90
L_de8b: mov ax, csi_printer_ok
L_de8e: jmp short L_de93
L_de90: mov ax, csi_printer_unavailable
L_de93: push ax
L_de94: call csi_transmit_string
L_de97: ret
%endif
