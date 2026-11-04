; Original status-line clear4795..47B5;33 exact bytes.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef STATUS_TOGGLE_OMF
SEGMENT STATUS_TOGGLE_NATIVE_CODE public align=16 class=FARCODE use16
extern status_hidden,status_coordinate_base,status_columns,status_attribute,csi_service_2530
global status_clear_original
%else
ORG 0x4795
%define status_hidden 0x1d46
%define status_coordinate_base 0x7a84
%define status_columns 0xceae
%define status_attribute 0xd008
%define csi_service_2530 0x2530
%endif
status_clear_original:
 cmp word [status_hidden],byte 0
 jz .done
 sub_load ax,ax
 push ax
 push word [status_coordinate_base]
 mov ax,[status_columns]
 add ax,[status_coordinate_base]
 dec ax
 push ax
 mov al,[status_attribute]
 sub_load ah,ah
 push ax
 call csi_service_2530
.done:
 ret
