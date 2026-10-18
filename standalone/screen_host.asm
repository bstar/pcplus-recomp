; Source-only cursor diagnostic host. Unrecovered services deliberately trap.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern screen_set_cursor, screen_cursor_right, screen_cursor_down
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 mov ax,10
 mov dx,20
 call screen_set_cursor
 call screen_cursor_right
 call screen_cursor_down
 cmp word [screen_cursor_row],11
 jne .failed
 cmp word [screen_cursor_column],21
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
; Test-link boundaries, not screen implementations. Calling one is a failure.
global screen_viewport_enter, screen_viewport_leave, screen_viewport_refresh
global screen_adjust_attribute_boundary, screen_wrap_forward
screen_viewport_enter:
screen_viewport_leave:
screen_viewport_refresh:
screen_adjust_attribute_boundary:
screen_wrap_forward:
 int 3
 mov ax,0x4c02
 int 0x21
SEGMENT _DATA public class=DATA use16
%macro word_state 2
 global %1
 %1: dw %2
%endmacro
word_state screen_cursor_row,0
word_state screen_cursor_column,0
word_state screen_visible_column,0
word_state screen_previous_row,0
word_state screen_previous_column,0
word_state screen_video_offset,0
word_state screen_attribute_offset,0
word_state screen_viewport_enabled,0
word_state screen_viewport_left,0
word_state screen_viewport_right,79
word_state screen_viewport_active,0
word_state screen_viewport_offset,0
word_state screen_video_row_bytes,160
word_state screen_attribute_row_bytes,80
word_state screen_top_margin,0
word_state screen_bottom_margin,24
word_state screen_doublewidth_enabled,0
word_state screen_cursor_wrap,0
word_state screen_last_row,24
word_state screen_vertical_attribute_check,0
word_state screen_attribute_checks,0
word_state screen_attributes_base,screen_attribute_cells
word_state screen_last_column,79
word_state screen_first_row,0
word_state screen_reverse_wrap_blocked,0
word_state screen_use_bios_cursor,1
word_state screen_columns,80
global screen_line_flags, screen_attribute_cells
screen_line_flags: times 128 db 0
screen_attribute_cells: times 4096 db 0
SEGMENT STACK stack class=STACK use16
 resb 4096
stack_top:
