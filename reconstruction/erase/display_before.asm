; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global csi_service_d85e
extern csi_service_d844
extern csi_service_2530
extern screen_cursor_row
extern screen_cursor_column
extern attributes_normal_value
extern screen_last_column
extern erase_lineflags_enabled
extern screen_line_flags
%define short
%else
ORG 0xd85e
%define csi_service_d844 0xd844
%define csi_service_2530 0x2530
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define attributes_normal_value 0x1d32
%define screen_last_column 0x3258
%define erase_lineflags_enabled 0x3260
%define screen_line_flags 0xcf86
%endif
%include "encodings.inc"
csi_service_d85e:
L_d85e: push di
L_d85f: cmp word [screen_cursor_row],0x0
L_d864: jz short L_d896
L_d866: sub_load ax,ax
L_d868: push ax
L_d869: sub_load cx,cx
L_d86b: push cx
L_d86c: mov ch,[screen_cursor_row]
L_d870: dec ch
L_d872: sub_load cl,cl
L_d874: or cx,[screen_last_column]
L_d878: push cx
L_d879: push word [attributes_normal_value]
L_d87d: call csi_service_2530
L_d880: cmp word [erase_lineflags_enabled],0x0
L_d885: jz short L_d896
L_d887: sub_load ax,ax
L_d889: mov dx,screen_line_flags
L_d88c: mov cx,[screen_cursor_row]
L_d890: mov_load di,dx
L_d892: push ds
L_d893: pop es
L_d894: rep stosb
L_d896: cmp word [erase_lineflags_enabled],0x0
L_d89b: jz short L_d8b0
L_d89d: mov ax,[screen_last_column]
L_d8a0: sub ax,[screen_cursor_column]
L_d8a4: dec ax
L_d8a5: jnz short L_d8b0
L_d8a7: mov bx,[screen_cursor_row]
L_d8ab: mov byte [bx+screen_line_flags],0x0
L_d8b0: call csi_service_d844
L_d8b3: pop di
L_d8b4: ret
