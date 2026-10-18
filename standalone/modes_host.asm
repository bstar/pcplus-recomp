; Source-only mode diagnostic links real screen services; unresolved effects trap.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern screen_set_cursor,csi_set_modes,csi_reset_modes
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 call csi_set_modes
 cmp word [cursor_state_value_1d20],1
 jne .failed
 call csi_reset_modes
 cmp word [cursor_state_value_1d20],0
 jne .failed
 mov word [ansi_parameters],6
 mov word [screen_first_row],4
 mov word [screen_last_row],19
 call csi_set_modes
 cmp word [csi_origin_mode],1
 jne .failed
 cmp word [screen_cursor_row],4
 jne .failed
 cmp word [screen_top_margin],4
 jne .failed
 cmp word [screen_bottom_margin],19
 jne .failed
 mov ah,3
 xor bh,bh
 int 0x10
 cmp dx,0x0400
 jne .failed
 call csi_reset_modes
 cmp word [csi_origin_mode],0
 jne .failed
 cmp word [screen_cursor_row],0
 jne .failed
 cmp word [screen_bottom_margin],24
 jne .failed
 mov ah,3
 xor bh,bh
 int 0x10
 or dx,dx
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
; These interfaces fail explicitly; no mode side effects are silently replaced.
%macro dependency 2
 global %1
 %1:
 mov ax,%2
 jmp modes_missing_dependency
%endmacro
dependency modes_keyboard_map,0x0b4e
dependency modes_screen_width,0x2a6e
dependency csi_reset_terminal,0x20a4
dependency modes_cursor_shape,0x2f78
dependency screen_viewport_refresh,0x2fb8
dependency screen_viewport_enter,0x482a
dependency screen_viewport_leave,0x4850
dependency screen_adjust_attribute_boundary,0x2adc
dependency screen_wrap_forward,0x12c8
modes_missing_dependency:
 mov [modes_dependency_id],ax
 mov bx,sp
 mov dx,[bx+2]
 mov [modes_dependency_argument],dx
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
global csi_origin_row
csi_origin_row:
word_state screen_top_margin,0
global csi_origin_bottom
csi_origin_bottom:
word_state screen_bottom_margin,24
word_state screen_doublewidth_enabled,0
word_state screen_cursor_wrap,0
global csi_scroll_bottom
csi_scroll_bottom:
word_state screen_last_row,24
word_state screen_vertical_attribute_check,0
word_state screen_attribute_checks,0
word_state screen_attributes_base,screen_attribute_cells
word_state screen_last_column,79
global csi_scroll_top
csi_scroll_top:
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
word_state csi_report_private_prefix,0
word_state ansi_parameter_count,1
global ansi_parameters
ansi_parameters: dw 7
 times 15 dw 0
word_state ansi_private,0
word_state terminal_mode_372c,0
word_state csi_origin_mode,0
word_state cursor_state_value_1d20,0
word_state modes_value_1d1a,0
word_state modes_value_3980,0
word_state modes_value_3982,0
word_state modes_cursor_flags,0
word_state csi_terminal_id,4
word_state csi_previous_terminal_id,0
word_state csi_last_row,24
word_state csi_wrap_pending,0
word_state modes_dependency_id,0
word_state modes_dependency_argument,0
