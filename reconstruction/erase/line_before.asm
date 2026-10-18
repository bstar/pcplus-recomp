; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global csi_service_d844
extern csi_service_2530
extern csi_wrap_pending
extern screen_cursor_row
extern screen_cursor_column
extern attributes_normal_value
%define short
%else
ORG 0xd844
%define csi_service_2530 0x2530
%define csi_wrap_pending 0x3342
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define attributes_normal_value 0x1d32
%endif
%include "encodings.inc"
csi_service_d844:
L_d844: sub_load ax,ax
L_d846: mov [csi_wrap_pending],ax
L_d849: push ax
L_d84a: mov ah,[screen_cursor_row]
L_d84e: sub_load al,al
L_d850: push ax
L_d851: or ax,[screen_cursor_column]
L_d855: push ax
L_d856: push word [attributes_normal_value]
L_d85a: call csi_service_2530
L_d85d: ret
