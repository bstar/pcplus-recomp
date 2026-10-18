; Recovered PCPlus 2.01 scroll instructions; see docs/SCROLL.md.
BITS 16
CPU 8086
%ifdef SCROLL_OMF
SEGMENT _TEXT public class=CODE use16
global scroll_index
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
ORG 0xda46
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
scroll_index:
L_da46: mov word [csi_wrap_pending],0x0
L_da4c: mov ax,[screen_last_row]
L_da4f: cmp [screen_cursor_row],ax
L_da53: jnz short L_da78
L_da55: mov ax,0x1
L_da58: push ax
L_da59: mov ah,[screen_first_row]
L_da5d: sub_load al,al
L_da5f: push ax
L_da60: mov ah,[screen_last_row]
L_da64: or ax,[screen_last_column]
L_da68: push ax
L_da69: mov al,[csi_erase_attribute]
L_da6c: sub_load ah,ah
L_da6e: push ax
L_da6f: call csi_service_2530
L_da72: mov ax,[screen_last_row]
L_da75: jmp short L_da7c
L_da77: nop
L_da78: mov ax,[screen_cursor_row]
L_da7b: inc ax
L_da7c: mov dx,[screen_cursor_column]
L_da80: call screen_set_cursor
L_da83: ret
