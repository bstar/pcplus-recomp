; Cursor-state DOS host links actual recovered screen code. Unrecovered services trap.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern screen_set_cursor,csi_save_cursor,csi_restore_cursor
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
 mov word [attributes_current],0x1234
 xor ax,ax
 push ax
 call csi_save_cursor
 add sp,2
 mov ax,3
 mov dx,4
 call screen_set_cursor
 mov word [attributes_current],0x4567
 xor ax,ax
 push ax
 call csi_restore_cursor
 add sp,2
 cmp word [screen_cursor_row],10
 jne .failed
 cmp word [screen_cursor_column],20
 jne .failed
 cmp word [attributes_current],0x1234
 jne .failed
 mov ah,3
 xor bh,bh
 int 0x10
 cmp dx,0x0a14
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

SEGMENT _DATA
word_state csi_saved_row,0
word_state csi_saved_column,0
word_state ansi_charset_g1_flag_graphics,0
word_state ansi_charset_g0_flag_graphics,0
word_state cursor_state_value_cdfc,0
word_state cursor_state_value_ce04,0
word_state attributes_current,0
word_state cursor_state_value_1d20,0
word_state csi_origin_mode,0
word_state csi_wrap_pending,0
word_state cursor_state_saved_cdf0,0
word_state cursor_state_saved_cdec,0
word_state cursor_state_saved_cdfc,0
word_state cursor_state_saved_ce04,0
word_state cursor_state_saved_1f70,0
word_state cursor_state_saved_1d20,0
word_state cursor_state_saved_cdd2,0
word_state cursor_state_saved_3342,0
