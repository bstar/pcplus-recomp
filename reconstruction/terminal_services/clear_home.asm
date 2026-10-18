; Recovered PCPlus 2.01 terminal support instructions; see docs/TERMINAL_SERVICES.md.
BITS 16
CPU 8086
%ifdef TERMINAL_SERVICES_OMF
SEGMENT _TEXT public class=CODE use16
global terminal_clear_home
extern csi_service_2530
extern attributes_reset
extern screen_set_cursor
extern csi_last_row
extern csi_last_column
extern attributes_normal_value
extern csi_origin_row
%define short
%else
ORG 0x24e2
%define csi_service_2530 0x2530
%define attributes_reset 0x24da
%define screen_set_cursor 0x1bbe
%define csi_last_row 0x334a
%define csi_last_column 0x3258
%define attributes_normal_value 0x1d32
%define csi_origin_row 0xceb0
%endif
%include "encodings.inc"
terminal_clear_home:
L_24e2: sub_load ax,ax
L_24e4: push ax
L_24e5: sub_load cx,cx
L_24e7: push cx
L_24e8: mov ch,[csi_last_row]
L_24ec: sub_load cl,cl
L_24ee: or cx,[csi_last_column]
L_24f2: push cx
L_24f3: push word [attributes_normal_value]
L_24f7: call csi_service_2530
L_24fa: call attributes_reset
L_24fd: mov ax,[csi_origin_row]
L_2500: sub_load dx,dx
L_2502: call screen_set_cursor
L_2505: ret
