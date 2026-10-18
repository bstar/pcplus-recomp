; Exact original printer instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef PRINTER_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global printer_byte_original
global printer_at_36fd
global printer_at_36ff
global printer_at_3703
global printer_at_3706
global printer_at_3709
global printer_at_370a
global printer_at_370b
global printer_at_370f
global printer_at_3712
global printer_at_3713
global printer_at_3715
global printer_at_3716
extern printer_putc
extern printer_flush
extern printer_stream
%else
ORG 0x36fc
%define printer_putc 0x8436
%define printer_flush 0x8c54
%define printer_stream 0x8ff0
%endif
%include "encodings.inc"
printer_byte_original: push bp
printer_at_36fd: mov_load bp,sp
printer_at_36ff: push word [printer_stream]
printer_at_3703: push word [bp+0x4]
printer_at_3706: call printer_putc
printer_at_3709: pop bx
printer_at_370a: pop bx
printer_at_370b: push word [printer_stream]
printer_at_370f: call printer_flush
printer_at_3712: pop bx
printer_at_3713: mov_load sp,bp
printer_at_3715: pop bp
printer_at_3716: ret
