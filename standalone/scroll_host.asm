; Source-only linked scroll diagnostic. Missing complex services fail fast.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern scroll_up,scroll_reverse_index,screen_wrap_forward,screen_set_cursor
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
 mov ax,0x0741
.row:
 mov cx,80
 rep stosw
 inc ax
 cmp al,'Z'
 jne .row
 call scroll_up
 mov ax,0xb800
 mov es,ax
 cmp word [es:0],0x0742
 jne .failed
 cmp word [es:3840],0x0720
 jne .failed
 xor ax,ax
 mov dx,3
 call screen_set_cursor
 call scroll_reverse_index
 mov ax,0xb800
 mov es,ax
 cmp word [es:0],0x0720
 jne .failed
 cmp word [es:160],0x0742
 jne .failed
 mov ax,1
 mov dx,79
 call screen_set_cursor
 call screen_wrap_forward
 cmp word [screen_cursor_row],2
 jne .failed
 cmp word [screen_cursor_column],0
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
global screen_viewport_enter
screen_viewport_enter:
 mov ax,0x482a
 mov [scroll_unimplemented_service],ax
 int 3
 mov ax,0x4c02
 int 0x21
global screen_viewport_leave
screen_viewport_leave:
 mov ax,0x4850
 mov [scroll_unimplemented_service],ax
 int 3
 mov ax,0x4c02
 int 0x21
global screen_viewport_refresh
screen_viewport_refresh:
 mov ax,0x2fb8
 mov [scroll_unimplemented_service],ax
 int 3
 mov ax,0x4c02
 int 0x21
global screen_adjust_attribute_boundary
screen_adjust_attribute_boundary:
 mov ax,0x2adc
 mov [scroll_unimplemented_service],ax
 int 3
 mov ax,0x4c02
 int 0x21
global erase_complex_protected
erase_complex_protected:
 mov ax,0xd05f
 mov [scroll_unimplemented_service],ax
 int 3
 mov ax,0x4c02
 int 0x21
global erase_repair_attributes
erase_repair_attributes:
 mov ax,0x2d98
 mov [scroll_unimplemented_service],ax
 int 3
 mov ax,0x4c02
 int 0x21
SEGMENT _DATA public class=DATA use16
%macro state 2
 global %1
 %1: dw %2
%endmacro
state csi_wrap_pending,0
state screen_cursor_row,0
state screen_cursor_column,0
state attributes_normal_value,7
state screen_last_column,79
state erase_lineflags_enabled,0
state attributes_monochrome,0
state attributes_current,7
state screen_cursor_wrap,0
state screen_attribute_checks,0
state screen_attribute_offset,0
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
state screen_visible_column,0
state screen_previous_row,0
state screen_previous_column,0
state screen_video_offset,0
state screen_viewport_offset,0
state screen_video_row_bytes,160
state screen_top_margin,0
state screen_bottom_margin,24
state screen_doublewidth_enabled,0
state screen_vertical_attribute_check,0
state screen_first_row,0
state screen_reverse_wrap_blocked,0
state screen_use_bios_cursor,1
state scroll_enabled,1
state scroll_suppress_next_linefeed,0
state scroll_skip_attribute_scan,0
state scroll_unimplemented_service,0
global screen_line_flags,erase_attribute_flags,erase_attribute_values,erase_shadow_cells,screen_attribute_cells
screen_line_flags: times 128 db 0
erase_attribute_flags:
screen_attribute_cells: times 4096 db 0
erase_attribute_values: times 4096 db 7
erase_shadow_cells: times 8192 db 0
SEGMENT STACK stack class=STACK use16
 resb 4096
stack_top:
