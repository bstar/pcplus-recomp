; Original local duplex toggle CS:3316. Only zero maps to1; all other words to0.
; DS=SS. No UART write or keyboard read; display refresh is a separate owner.
BITS 16
CPU 8086
%ifdef RECON_FLAT
ORG 0x3316
%define modes_value_1d1a 0x1d1a
%else
SEGMENT _TEXT public class=CODE use16
extern modes_value_1d1a
global local_duplex_3316
%endif
local_duplex_3316:
 cmp word [modes_value_1d1a],1
 db 0x1b,0xc0 ; sbb ax,ax: preserve the original direction-bit encoding
 neg ax
 mov [modes_value_1d1a],ax
 ret
