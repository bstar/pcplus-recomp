; Recovered PCPlus 2.01 terminal support instructions; see docs/TERMINAL_SERVICES.md.
BITS 16
CPU 8086
%ifdef TERMINAL_SERVICES_OMF
SEGMENT _TEXT public class=CODE use16
global csi_reset_scroll_region
extern csi_last_row
extern csi_scroll_top
extern csi_scroll_bottom
%define short
%else
ORG 0x250a
%define csi_last_row 0x334a
%define csi_scroll_top 0xce0e
%define csi_scroll_bottom 0xce3a
%endif
%include "encodings.inc"
csi_reset_scroll_region:
L_250a: mov word [csi_scroll_top],0x0
L_2510: mov ax,[csi_last_row]
L_2513: mov [csi_scroll_bottom],ax
L_2516: ret
