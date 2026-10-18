; Recovered PCPlus 2.01 scroll instructions; see docs/LINE_EDIT.md.
BITS 16
CPU 8086
%ifdef LINE_EDIT_OMF
SEGMENT _TEXT public class=CODE use16
global csi_delete_line
extern screen_set_cursor
extern csi_service_2530
extern erase_previous_attribute
extern erase_scan_attributes
extern erase_move_bytes
extern erase_repair_attributes
extern screen_cursor_row
extern attributes_normal_value
extern screen_last_column
extern screen_cursor_wrap
extern screen_attribute_checks
extern screen_attribute_offset
extern screen_attributes_base
extern screen_attribute_row_bytes
extern erase_cell_count
extern erase_attribute_values_base
extern screen_last_row
extern csi_last_row
%define short
%else
ORG 0xd73c
%define screen_set_cursor 0x1bbe
%define csi_service_2530 0x2530
%define erase_previous_attribute 0x2d4c
%define erase_scan_attributes 0x2d6c
%define erase_move_bytes 0x85b4
%define erase_repair_attributes 0x2d98
%define screen_cursor_row 0x399c
%define attributes_normal_value 0x1d32
%define screen_last_column 0x3258
%define screen_cursor_wrap 0x900c
%define screen_attribute_checks 0x3734
%define screen_attribute_offset 0x3346
%define screen_attributes_base 0x39c4
%define screen_attribute_row_bytes 0x325a
%define erase_cell_count 0x325c
%define erase_attribute_values_base 0x39c2
%define screen_last_row 0xce3a
%define csi_last_row 0x334a
%endif
%include "encodings.inc"
csi_delete_line:
L_d73c: push bp
L_d73d: mov_load bp,sp
L_d73f: sub sp,0x6
L_d742: push di
L_d743: push si
L_d744: cmp word [screen_attribute_checks],0x0
L_d749: jz short L_d74e
L_d74b: jmp near L_d83d
L_d74e: mov ax,[screen_cursor_row]
L_d751: cmp [csi_last_row],ax
L_d755: jnz short L_d75c
L_d757: sub_load ax,ax
L_d759: jmp short L_d75f
L_d75b: nop
L_d75c: mov ax,0x1
L_d75f: mov [bp-0x4],ax
L_d762: mov ax,[screen_cursor_row]
L_d765: sub_load dx,dx
L_d767: call screen_set_cursor
L_d76a: cmp word [screen_cursor_wrap],0x0
L_d76f: jz short L_d790
L_d771: push word [erase_cell_count]
L_d775: call erase_previous_attribute
L_d778: sub_load ah,ah
L_d77a: mov_load si,ax
L_d77c: mov ax,[screen_attribute_offset]
L_d77f: add ax,[screen_attributes_base]
L_d783: push ax
L_d784: push word [screen_attribute_row_bytes]
L_d788: call erase_scan_attributes
L_d78b: mov [bp-0x6],ax
L_d78e: jmp short L_d794
L_d790: mov si,[attributes_normal_value]
L_d794: push word [bp-0x4]
L_d797: mov ah,[screen_cursor_row]
L_d79b: sub_load al,al
L_d79d: push ax
L_d79e: mov ah,[screen_last_row]
L_d7a2: or ax,[screen_last_column]
L_d7a6: push ax
L_d7a7: push si
L_d7a8: call csi_service_2530
L_d7ab: cmp word [screen_cursor_wrap],0x0
L_d7b0: jnz short L_d7b5
L_d7b2: jmp near L_d83d
L_d7b5: mov ax,0x17
L_d7b8: sub ax,[screen_cursor_row]
L_d7bc: mul word [screen_attribute_row_bytes]
L_d7c0: push ax
L_d7c1: mov ax,[screen_attribute_offset]
L_d7c4: mov [bp-0x2],ax
L_d7c7: add ax,[screen_attribute_row_bytes]
L_d7cb: add ax,[screen_attributes_base]
L_d7cf: push ax
L_d7d0: mov ax,[bp-0x2]
L_d7d3: add ax,[screen_attributes_base]
L_d7d7: push ax
L_d7d8: call erase_move_bytes
L_d7db: add sp,0x6
L_d7de: sub_load ax,ax
L_d7e0: mov bx,[erase_cell_count]
L_d7e4: mov di,[screen_attributes_base]
L_d7e8: mov cx,[screen_attribute_row_bytes]
L_d7ec: lea di,[bx+di]
L_d7ee: push ds
L_d7ef: pop es
L_d7f0: rep stosb
L_d7f2: mov ax,0x17
L_d7f5: sub ax,[screen_cursor_row]
L_d7f9: mul word [screen_attribute_row_bytes]
L_d7fd: push ax
L_d7fe: mov ax,[screen_attribute_row_bytes]
L_d801: add ax,[erase_attribute_values_base]
L_d805: add ax,[bp-0x2]
L_d808: push ax
L_d809: mov ax,[erase_attribute_values_base]
L_d80c: add ax,[bp-0x2]
L_d80f: push ax
L_d810: call erase_move_bytes
L_d813: add sp,0x6
L_d816: mov_load ax,si
L_d818: mov bx,[erase_cell_count]
L_d81c: mov si,[erase_attribute_values_base]
L_d820: mov cx,[screen_attribute_row_bytes]
L_d824: lea di,[bx+si]
L_d826: push ds
L_d827: pop es
L_d828: rep stosb
L_d82a: cmp word [bp-0x4],0x0
L_d82e: jz short L_d83d
L_d830: cmp word [bp-0x6],0x0
L_d834: jz short L_d83d
L_d836: mov ax,0x2
L_d839: push ax
L_d83a: call erase_repair_attributes
L_d83d: pop si
L_d83e: pop di
L_d83f: mov_load sp,bp
L_d841: pop bp
L_d842: ret
