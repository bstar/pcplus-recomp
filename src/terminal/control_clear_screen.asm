; Recovered PCPlus2.01 overlay12:da12..da45, 51 exact baseline bytes.
; REA Evidence ev_69017b522a437c1c0ff6ec2b312f16bcce17c94eacc14171434df7bf025222d7.
; Original SHA256 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Resident trampoline ba4b dispatches here. See saved REA export
; analysis/pcplus-overlay-anchored-12/functions/0x1da12.asm.
; Clears full physical window with selected attribute, homes to origin row.
BITS 16
CPU 8086
%ifdef TERMINAL_CLEAR_FLAT
ORG 0xda12
%define screen_last_row 0x334a
%define screen_last_column 0x3258
%define attributes_monochrome 0x8ff6
%define attributes_current 0x1f70
%define csi_erase_attribute 0xd008
%define csi_origin_row 0xceb0
%define csi_service_2530 0x2530
%define screen_set_cursor 0x1bbe
%else
SEGMENT _TEXT public class=CODE use16
global csi_service_da12,terminal_formfeed_profile_6_7
extern screen_last_row,screen_last_column,attributes_monochrome,attributes_current
extern csi_erase_attribute,csi_origin_row,csi_service_2530,screen_set_cursor
%endif
%include "encodings.inc"
csi_service_da12:
terminal_formfeed_profile_6_7:
 push si
 sub_load ax,ax
 push ax
 sub_load cx,cx
 push cx
 mov ch,[screen_last_row]
 sub_load cl,cl
 or cx,[screen_last_column]
 push cx
 cmp [attributes_monochrome],ax
 jz .erase_attribute
 mov si,[attributes_current]
 jmp short .erase
.erase_attribute:
 mov al,[csi_erase_attribute]
 sub_load ah,ah
 mov_load si,ax
.erase:
 push si
 call csi_service_2530
 mov ax,[csi_origin_row]
 sub_load dx,dx
 call screen_set_cursor
 pop si
 ret
