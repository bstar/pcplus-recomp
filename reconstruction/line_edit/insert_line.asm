; Recovered PCPlus 2.01 scroll instructions; see docs/LINE_EDIT.md.
BITS 16
CPU 8086
%ifdef LINE_EDIT_OMF
SEGMENT _TEXT public class=CODE use16
global csi_insert_line
extern screen_set_cursor
extern csi_service_2530
extern erase_previous_attribute
extern erase_move_bytes
extern screen_cursor_row
extern attributes_normal_value
extern screen_last_column
extern screen_cursor_wrap
extern screen_attribute_checks
extern screen_attribute_offset
extern screen_attributes_base
extern screen_attribute_row_bytes
extern erase_attribute_values_base
extern screen_last_row
extern csi_last_row
%define short
%else
ORG 0xd668
%define screen_set_cursor 0x1bbe
%define csi_service_2530 0x2530
%define erase_previous_attribute 0x2d4c
%define erase_move_bytes 0x85b4
%define screen_cursor_row 0x399c
%define attributes_normal_value 0x1d32
%define screen_last_column 0x3258
%define screen_cursor_wrap 0x900c
%define screen_attribute_checks 0x3734
%define screen_attribute_offset 0x3346
%define screen_attributes_base 0x39c4
%define screen_attribute_row_bytes 0x325a
%define erase_attribute_values_base 0x39c2
%define screen_last_row 0xce3a
%define csi_last_row 0x334a
%endif
%include "encodings.inc"
csi_insert_line:
L_d668: push bp
L_d669: mov_load bp,sp
L_d66b: sub sp,0x2
L_d66e: push di
L_d66f: push si
L_d670: cmp word [screen_attribute_checks],0x0
L_d675: jz short L_d67a
L_d677: jmp near L_d735
L_d67a: mov ax,[screen_cursor_row]
L_d67d: cmp [csi_last_row],ax
L_d681: jnz short L_d688
L_d683: sub_load si,si
L_d685: jmp short L_d68b
L_d687: nop
L_d688: mov si,0xffff
L_d68b: sub_load dx,dx
L_d68d: call screen_set_cursor
L_d690: cmp word [screen_cursor_wrap],0x0
L_d695: jz short L_d6a2
L_d697: push word [screen_attribute_offset]
L_d69b: call erase_previous_attribute
L_d69e: sub_load ah,ah
L_d6a0: jmp short L_d6a5
L_d6a2: mov ax,[attributes_normal_value]
L_d6a5: mov [bp-0x2],ax
L_d6a8: push si
L_d6a9: mov ah,[screen_cursor_row]
L_d6ad: sub_load al,al
L_d6af: push ax
L_d6b0: mov ah,[screen_last_row]
L_d6b4: or ax,[screen_last_column]
L_d6b8: push ax
L_d6b9: push word [bp-0x2]
L_d6bc: call csi_service_2530
L_d6bf: cmp word [screen_cursor_wrap],0x0
L_d6c4: jz short L_d735
L_d6c6: mov ax,0x17
L_d6c9: sub ax,[screen_cursor_row]
L_d6cd: mul word [screen_attribute_row_bytes]
L_d6d1: push ax
L_d6d2: mov si,[screen_attribute_offset]
L_d6d6: mov_load ax,si
L_d6d8: add ax,[screen_attributes_base]
L_d6dc: push ax
L_d6dd: mov_load ax,si
L_d6df: add ax,[screen_attribute_row_bytes]
L_d6e3: add ax,[screen_attributes_base]
L_d6e7: push ax
L_d6e8: call erase_move_bytes
L_d6eb: add sp,0x6
L_d6ee: sub_load ax,ax
L_d6f0: mov bx,[screen_attributes_base]
L_d6f4: mov cx,[screen_attribute_row_bytes]
L_d6f8: lea di,[bx+si]
L_d6fa: push ds
L_d6fb: pop es
L_d6fc: rep stosb
L_d6fe: mov ax,0x17
L_d701: sub ax,[screen_cursor_row]
L_d705: mul word [screen_attribute_row_bytes]
L_d709: push ax
L_d70a: mov_load ax,si
L_d70c: add si,[erase_attribute_values_base]
L_d710: push si
L_d711: mov_load cx,ax
L_d713: add ax,[screen_attribute_row_bytes]
L_d717: add ax,[erase_attribute_values_base]
L_d71b: push ax
L_d71c: mov_load si,cx
L_d71e: call erase_move_bytes
L_d721: add sp,0x6
L_d724: mov ax,[bp-0x2]
L_d727: mov bx,[erase_attribute_values_base]
L_d72b: mov cx,[screen_attribute_row_bytes]
L_d72f: lea di,[bx+si]
L_d731: push ds
L_d732: pop es
L_d733: rep stosb
L_d735: pop si
L_d736: pop di
L_d737: mov_load sp,bp
L_d739: pop bp
L_d73a: ret
