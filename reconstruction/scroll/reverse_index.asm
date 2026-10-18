; Recovered PCPlus 2.01 scroll instructions; see docs/SCROLL.md.
BITS 16
CPU 8086
%ifdef SCROLL_OMF
SEGMENT _TEXT public class=CODE use16
global scroll_reverse_index
extern screen_set_cursor
extern csi_service_2530
extern csi_wrap_pending
extern screen_cursor_row
extern screen_cursor_column
extern screen_last_column
extern screen_last_row
extern screen_first_row
extern csi_erase_attribute
%define short
%else
ORG 0xda84
%define screen_set_cursor 0x1bbe
%define csi_service_2530 0x2530
%define csi_wrap_pending 0x3342
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define screen_last_column 0x3258
%define screen_last_row 0xce3a
%define screen_first_row 0xce0e
%define csi_erase_attribute 0xd008
%endif
%include "encodings.inc"
scroll_reverse_index:
L_da84: mov word [csi_wrap_pending],0x0
L_da8a: mov ax,[screen_first_row]
L_da8d: cmp [screen_cursor_row],ax
L_da91: jnz short L_dab6
L_da93: mov ax,0xffff
L_da96: push ax
L_da97: mov ah,[screen_first_row]
L_da9b: sub_load al,al
L_da9d: push ax
L_da9e: mov ah,[screen_last_row]
L_daa2: or ax,[screen_last_column]
L_daa6: push ax
L_daa7: mov al,[csi_erase_attribute]
L_daaa: sub_load ah,ah
L_daac: push ax
L_daad: call csi_service_2530
L_dab0: mov ax,[screen_first_row]
L_dab3: jmp short L_dabd
L_dab5: nop
L_dab6: dec word [screen_cursor_row]
L_daba: mov ax,[screen_cursor_row]
L_dabd: mov dx,[screen_cursor_column]
L_dac1: call screen_set_cursor
L_dac4: ret
