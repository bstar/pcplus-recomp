; Recovered PCPlus 2.01 scroll instructions; see docs/SCROLL.md.
BITS 16
CPU 8086
%ifdef SCROLL_OMF
SEGMENT _TEXT public class=CODE use16
global scroll_up
extern csi_service_2530
extern erase_previous_attribute
extern erase_scan_attributes
extern erase_move_bytes
extern erase_repair_attributes
extern csi_wrap_pending
extern attributes_normal_value
extern screen_last_column
extern attributes_monochrome
extern attributes_current
extern screen_cursor_wrap
extern screen_attributes_base
extern screen_attribute_row_bytes
extern erase_cell_count
extern erase_attribute_values_base
extern screen_last_row
extern screen_first_row
extern scroll_skip_attribute_scan
%define short
%else
ORG 0x1fc4
%define csi_service_2530 0x2530
%define erase_previous_attribute 0x2d4c
%define erase_scan_attributes 0x2d6c
%define erase_move_bytes 0x85b4
%define erase_repair_attributes 0x2d98
%define csi_wrap_pending 0x3342
%define attributes_normal_value 0x1d32
%define screen_last_column 0x3258
%define attributes_monochrome 0x8ff6
%define attributes_current 0x1f70
%define screen_cursor_wrap 0x900c
%define screen_attributes_base 0x39c4
%define screen_attribute_row_bytes 0x325a
%define erase_cell_count 0x325c
%define erase_attribute_values_base 0x39c2
%define screen_last_row 0xce3a
%define screen_first_row 0xce0e
%define scroll_skip_attribute_scan 0x904c
%endif
%include "encodings.inc"
scroll_up:
L_1fc4: push bp
L_1fc5: mov_load bp,sp
L_1fc7: sub sp,0x2
L_1fca: push di
L_1fcb: push si
L_1fcc: sub_load si,si
L_1fce: mov [csi_wrap_pending],si
L_1fd2: cmp [screen_cursor_wrap],si
L_1fd6: jz short L_1ff8
L_1fd8: push word [erase_cell_count]
L_1fdc: call erase_previous_attribute
L_1fdf: mov [bp-0x1],al
L_1fe2: cmp [scroll_skip_attribute_scan],si
L_1fe6: jnz short L_200a
L_1fe8: push word [screen_attributes_base]
L_1fec: push word [screen_attribute_row_bytes]
L_1ff0: call erase_scan_attributes
L_1ff3: mov_load si,ax
L_1ff5: jmp short L_200a
L_1ff7: nop
L_1ff8: cmp [attributes_monochrome],si
L_1ffc: jz short L_2004
L_1ffe: mov al,[attributes_current]
L_2001: jmp short L_2007
L_2003: nop
L_2004: mov al,[attributes_normal_value]
L_2007: mov [bp-0x1],al
L_200a: mov ax,0x1
L_200d: push ax
L_200e: mov ah,[screen_first_row]
L_2012: sub_load al,al
L_2014: push ax
L_2015: mov ah,[screen_last_row]
L_2019: or ax,[screen_last_column]
L_201d: push ax
L_201e: mov al,[bp-0x1]
L_2021: sub_load ah,ah
L_2023: push ax
L_2024: call csi_service_2530
L_2027: cmp word [screen_cursor_wrap],0x0
L_202c: jz short L_2093
L_202e: mov ax,[erase_cell_count]
L_2031: sub ax,[screen_attribute_row_bytes]
L_2035: push ax
L_2036: mov ax,[screen_attribute_row_bytes]
L_2039: add ax,[screen_attributes_base]
L_203d: push ax
L_203e: push word [screen_attributes_base]
L_2042: call erase_move_bytes
L_2045: add sp,0x6
L_2048: mov ax,[erase_cell_count]
L_204b: sub ax,[screen_attribute_row_bytes]
L_204f: push ax
L_2050: mov ax,[screen_attribute_row_bytes]
L_2053: add ax,[erase_attribute_values_base]
L_2057: push ax
L_2058: push word [erase_attribute_values_base]
L_205c: call erase_move_bytes
L_205f: add sp,0x6
L_2062: sub_load ax,ax
L_2064: mov bx,[erase_cell_count]
L_2068: sub bx,[screen_attribute_row_bytes]
L_206c: mov di,[screen_attributes_base]
L_2070: mov cx,[screen_attribute_row_bytes]
L_2074: lea di,[bx+di]
L_2076: push ds
L_2077: pop es
L_2078: rep stosb
L_207a: mov al,[bp-0x1]
L_207d: sub_load ah,ah
L_207f: mov bx,[erase_cell_count]
L_2083: sub bx,[screen_attribute_row_bytes]
L_2087: mov di,[erase_attribute_values_base]
L_208b: mov cx,[screen_attribute_row_bytes]
L_208f: lea di,[bx+di]
L_2091: rep stosb
L_2093: or_load si,si
L_2095: jz short L_209d
L_2097: sub_load ax,ax
L_2099: push ax
L_209a: call erase_repair_attributes
L_209d: pop si
L_209e: pop di
L_209f: mov_load sp,bp
L_20a1: pop bp
L_20a2: ret
