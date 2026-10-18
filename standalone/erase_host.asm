; Source-only rectangle/erase diagnostic; complex protected repair traps.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern csi_service_2530,csi_service_d844,csi_service_d85e,csi_service_d8b6
global erase_test_rectangle,erase_test_after
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 mov ax,3
 int 0x10
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov ax,0x4f41
 mov cx,2000
 cld
 rep stosw
 call erase_test_rectangle
 mov ax,0xb800
 mov es,ax
 cmp word [es:164],0x0720
 jne .failed
 cmp word [es:162],0x4f41
 jne .failed
 cmp word [es:490],0x0720
 jne .failed
 cmp word [es:492],0x4f41
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
erase_test_rectangle:
 push word [erase_test_scroll]
 push word [erase_test_top]
 push word [erase_test_bottom]
 push word [erase_test_attribute]
 call csi_service_2530
 ret
erase_test_after:
 push word [erase_test_flag]
 call csi_service_d8b6
 ret
global erase_complex_protected,erase_repair_attributes
erase_complex_protected:
erase_repair_attributes:
 int 3
 mov ax,0x4c02
 int 0x21
SEGMENT _DATA public class=DATA use16
%macro state 2
 global %1
 %1: dw %2
%endmacro
state erase_test_scroll,0
state erase_test_top,0x0102
state erase_test_bottom,0x0305
state erase_test_attribute,7
state erase_test_flag,0
state csi_wrap_pending,0
state screen_cursor_row,10
state screen_cursor_column,20
state attributes_normal_value,7
state screen_last_column,79
state erase_lineflags_enabled,0
state attributes_monochrome,0
state attributes_current,7
state screen_cursor_wrap,0
state screen_attribute_checks,0
state screen_attribute_offset,820
state screen_attributes_base,erase_attribute_flags
state screen_attribute_row_bytes,80
state erase_protection_mode,0
state erase_cell_count,2000
state erase_attribute_values_base,erase_attribute_values
state screen_last_row,24
state csi_last_row,24
state screen_viewport_enabled,0
state screen_viewport_left,40
state screen_columns,80
state screen_viewport_active,0
state screen_viewport_right,79
state erase_shadow_offset,erase_shadow_cells
state erase_shadow_segment,seg erase_shadow_cells
state csi_erase_attribute,7
global screen_line_flags,erase_attribute_flags,erase_attribute_values,erase_shadow_cells
screen_line_flags: times 128 db 0
erase_attribute_flags: times 4096 db 0
erase_attribute_values: times 4096 db 7
erase_shadow_cells: times 8192 db 0
SEGMENT STACK stack class=STACK use16
 resb 4096
stack_top:
