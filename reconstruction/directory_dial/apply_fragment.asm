; Original overlay5:e6ea..e72c (66 bytes), internal selected-record apply span.
; OMF adds RET after the original span as an explicitly maintained call bridge.
; Original imports still require actual port close/reconfiguration; not standalone.
BITS 16
CPU 8086
%ifdef DIRECTORY_DIAL_OMF
SEGMENT _TEXT public class=CODE use16
global directory_dial_apply_original
extern directory_dial_record,directory_dial_port_index,directory_dial_baud_index
extern directory_dial_parity,directory_dial_stop_bits,directory_dial_data_bits,directory_dial_duplex
extern directory_dial_close_port,directory_dial_reconfigure
%else
ORG 0xe6ea
%define directory_dial_record 0xe650
%define directory_dial_port_index 0x1b84
%define directory_dial_baud_index 0x1b86
%define directory_dial_parity 0x1b88
%define directory_dial_stop_bits 0x1b8a
%define directory_dial_data_bits 0x1b8c
%define directory_dial_duplex 0x1d1a
%define directory_dial_close_port 0xadba
%define directory_dial_reconfigure 0x03a7
%endif
directory_dial_apply_original:
 cmp byte [directory_dial_record+104],0
 jz .serial
 mov al,[directory_dial_record+104]
 cbw
 sub ax,[directory_dial_port_index]
 dec ax
 jz .serial
 call directory_dial_close_port
 mov al,[directory_dial_record+104]
 cbw
 dec ax
 mov [directory_dial_port_index],ax
.serial:
 mov ax,[directory_dial_record+46]
 mov [directory_dial_baud_index],ax
 mov al,[directory_dial_record+48]
 cbw
 mov [directory_dial_parity],ax
 mov al,[directory_dial_record+50]
 cbw
 mov [directory_dial_stop_bits],ax
 mov al,[directory_dial_record+49]
 cbw
 mov [directory_dial_data_bits],ax
 mov al,[directory_dial_record+51]
 cbw
 mov [directory_dial_duplex],ax
 call directory_dial_reconfigure
%ifdef DIRECTORY_DIAL_OMF
 ret
%endif
