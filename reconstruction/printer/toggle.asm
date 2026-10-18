; Exact original printer instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef PRINTER_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global printer_toggle_original
global printer_at_1a7b
global printer_at_1a7d
global printer_at_1a83
global printer_at_1a87
global printer_at_1a8a
global printer_at_1a8d
global printer_at_1a8f
global printer_at_1a90
global printer_at_1a96
global printer_at_1a99
global printer_at_1a9a
global printer_at_1a9d
global printer_at_1a9e
global printer_at_1aa1
global printer_at_1aa4
global printer_at_1aa7
extern printer_device
extern printer_status
extern printer_enabled
extern printer_binary_mode
extern printer_close
extern printer_open
extern printer_stream
%else
ORG 0x1a76
%define printer_device 0x1d50
%define printer_status 0x2fb8
%define printer_enabled 0x3988
%define printer_binary_mode 0x4688
%define printer_close 0x8318
%define printer_open 0x841a
%define printer_stream 0x8ff0
%endif
%include "encodings.inc"
printer_toggle_original: cmp word [printer_enabled],0x0
printer_at_1a7b: jz short printer_at_1a90
printer_at_1a7d: mov word [printer_enabled],0x0
printer_at_1a83: push word [printer_stream]
printer_at_1a87: call printer_close
printer_at_1a8a: add sp,0x2
printer_at_1a8d: jmp short printer_at_1aa7
printer_at_1a8f: nop
printer_at_1a90: mov word [printer_enabled],0x1
printer_at_1a96: mov ax,printer_binary_mode
printer_at_1a99: push ax
printer_at_1a9a: mov ax,printer_device
printer_at_1a9d: push ax
printer_at_1a9e: call printer_open
printer_at_1aa1: add sp,0x4
printer_at_1aa4: mov [printer_stream],ax
printer_at_1aa7: jmp near printer_status
