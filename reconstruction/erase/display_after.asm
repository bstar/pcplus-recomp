; Recovered PCPlus 2.01 erase instructions; see docs/ERASE.md.
BITS 16
CPU 8086
%ifdef ERASE_OMF
SEGMENT _TEXT public class=CODE use16
global csi_service_d8b6
extern csi_service_2530
extern erase_previous_attribute
extern erase_scan_attributes
extern erase_complex_protected
extern erase_repair_attributes
extern screen_cursor_row
extern screen_cursor_column
extern attributes_normal_value
extern screen_last_column
extern erase_lineflags_enabled
extern screen_line_flags
extern attributes_monochrome
extern attributes_current
extern screen_cursor_wrap
extern screen_attribute_checks
extern screen_attribute_offset
extern screen_attributes_base
extern screen_attribute_row_bytes
extern erase_protection_mode
extern erase_cell_count
extern erase_attribute_values_base
extern screen_last_row
extern csi_last_row
%define short
%else
ORG 0xd8b6
%define csi_service_2530 0x2530
%define erase_previous_attribute 0x2d4c
%define erase_scan_attributes 0x2d6c
%define erase_complex_protected 0xd05f
%define erase_repair_attributes 0x2d98
%define screen_cursor_row 0x399c
%define screen_cursor_column 0x399e
%define attributes_normal_value 0x1d32
%define screen_last_column 0x3258
%define erase_lineflags_enabled 0x3260
%define screen_line_flags 0xcf86
%define attributes_monochrome 0x8ff6
%define attributes_current 0x1f70
%define screen_cursor_wrap 0x900c
%define screen_attribute_checks 0x3734
%define screen_attribute_offset 0x3346
%define screen_attributes_base 0x39c4
%define screen_attribute_row_bytes 0x325a
%define erase_protection_mode 0x3736
%define erase_cell_count 0x325c
%define erase_attribute_values_base 0x39c2
%define screen_last_row 0xce3a
%define csi_last_row 0x334a
%endif
%include "encodings.inc"
csi_service_d8b6:
L_d8b6: push bp
L_d8b7: mov_load bp,sp
L_d8b9: sub sp,0x6
L_d8bc: push di
L_d8bd: push si
L_d8be: cmp word [attributes_monochrome],0x0
L_d8c3: jz short L_d8ca
L_d8c5: mov al,[attributes_current]
L_d8c8: jmp short L_d909
L_d8ca: cmp word [screen_cursor_wrap],0x0
L_d8cf: jz short L_d906
L_d8d1: cmp word [screen_attribute_checks],0x0
L_d8d6: jz short L_d8e4
L_d8d8: push word [bp+0x4]
L_d8db: call erase_complex_protected
L_d8de: add sp,0x2
L_d8e1: jmp near L_da09
L_d8e4: push word [screen_attribute_offset]
L_d8e8: call erase_previous_attribute
L_d8eb: mov [bp-0x1],al
L_d8ee: mov ax,[screen_attribute_offset]
L_d8f1: add ax,[screen_attributes_base]
L_d8f5: push ax
L_d8f6: mov ax,[screen_attribute_row_bytes]
L_d8f9: sub ax,[screen_cursor_column]
L_d8fd: push ax
L_d8fe: call erase_scan_attributes
L_d901: mov [bp-0x4],ax
L_d904: jmp short L_d90c
L_d906: mov al,[attributes_normal_value]
L_d909: mov [bp-0x1],al
L_d90c: sub_load ax,ax
L_d90e: push ax
L_d90f: mov ch,[screen_cursor_row]
L_d913: sub_load cl,cl
L_d915: mov_load dx,cx
L_d917: or cx,[screen_cursor_column]
L_d91b: push cx
L_d91c: or dx,[screen_last_column]
L_d920: push dx
L_d921: mov cl,[bp-0x1]
L_d924: sub_load ch,ch
L_d926: mov [bp-0x6],cx
L_d929: push cx
L_d92a: call csi_service_2530
L_d92d: cmp word [screen_cursor_wrap],0x0
L_d932: jz short L_d97e
L_d934: cmp word [erase_protection_mode],0x1
L_d939: sbb_load al,al
L_d93b: inc al
L_d93d: mov [bp-0x2],al
L_d940: cmp word [bp+0x4],0x0
L_d944: jz short L_d950
L_d946: mov dx,[erase_cell_count]
L_d94a: sub dx,[screen_attribute_offset]
L_d94e: jmp short L_d958
L_d950: mov dx,[screen_attribute_row_bytes]
L_d954: sub dx,[screen_cursor_column]
L_d958: mov al,[bp-0x2]
L_d95b: sub_load ah,ah
L_d95d: mov bx,[screen_attribute_offset]
L_d961: mov si,[screen_attributes_base]
L_d965: mov_load cx,dx
L_d967: lea di,[bx+si]
L_d969: push ds
L_d96a: pop es
L_d96b: rep stosb
L_d96d: mov ax,[bp-0x6]
L_d970: mov bx,[screen_attribute_offset]
L_d974: mov si,[erase_attribute_values_base]
L_d978: mov_load cx,dx
L_d97a: lea di,[bx+si]
L_d97c: rep stosb
L_d97e: cmp word [screen_cursor_wrap],0x0
L_d983: jz short L_d98c
L_d985: mov si,[screen_last_row]
L_d989: jmp short L_d990
L_d98b: nop
L_d98c: mov si,[csi_last_row]
L_d990: cmp word [bp+0x4],0x0
L_d994: jz short L_d9d2
L_d996: cmp [screen_cursor_row],si
L_d99a: jnl short L_d9d2
L_d99c: sub_load ax,ax
L_d99e: push ax
L_d99f: mov cl,[screen_cursor_row]
L_d9a3: inc cl
L_d9a5: mov_load ch,cl
L_d9a7: sub_load cl,cl
L_d9a9: push cx
L_d9aa: mov_load cx,si
L_d9ac: mov dl,[screen_last_column]
L_d9b0: mov_load dh,cl
L_d9b2: push dx
L_d9b3: push word [bp-0x6]
L_d9b6: call csi_service_2530
L_d9b9: cmp word [erase_lineflags_enabled],0x0
L_d9be: jz short L_d9d2
L_d9c0: sub_load ax,ax
L_d9c2: mov bx,[screen_cursor_row]
L_d9c6: mov_load cx,si
L_d9c8: sub_load cx,bx
L_d9ca: lea di,[bx+(screen_line_flags+1)]
L_d9ce: push ds
L_d9cf: pop es
L_d9d0: rep stosb
L_d9d2: cmp word [erase_lineflags_enabled],0x0
L_d9d7: jz short L_d9ef
L_d9d9: cmp word [bp+0x4],0x0
L_d9dd: jz short L_d9ef
L_d9df: cmp word [screen_cursor_column],0x0
L_d9e4: jnz short L_d9ef
L_d9e6: mov bx,[screen_cursor_row]
L_d9ea: mov byte [bx+screen_line_flags],0x0
L_d9ef: cmp word [screen_cursor_wrap],0x0
L_d9f4: jz short L_da09
L_d9f6: cmp word [bp+0x4],0x0
L_d9fa: jnz short L_da02
L_d9fc: cmp word [bp-0x4],0x0
L_da00: jz short L_da09
L_da02: mov ax,0x3
L_da05: push ax
L_da06: call erase_repair_attributes
L_da09: pop si
L_da0a: pop di
L_da0b: mov_load sp,bp
L_da0d: pop bp
L_da0e: ret word 0x2
