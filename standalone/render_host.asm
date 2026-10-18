; Source-only linked original high-level renderer/low-level video/cursor host.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA STACK
extern render_character,screen_set_cursor
global render_test_character
render_test_character:
 push word [render_input_character]
 call render_character
 add sp,2
 ret
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 cld
 mov ax,3
 int 0x10
 mov word [render_input_character],'A'
 call render_test_character
 mov word [attributes_current],0x1e
 mov word [render_input_character],'B'
 call render_test_character
 mov ax,0xb800
 mov es,ax
 cmp word [es:0],0x0741
 jne .failed
 cmp word [es:2],0x1e42
 jne .failed
 cmp word [screen_cursor_column],2
 jne .failed
 cmp word [screen_video_offset],4
 jne .failed
 ; Deferred wrap writes last column first, then next call moves to next row.
 xor ax,ax
 mov dx,79
 call screen_set_cursor
 mov word [render_input_character],'C'
 call render_test_character
 cmp word [csi_wrap_pending],1
 jne .failed
 mov word [render_input_character],'D'
 call render_test_character
 cmp word [screen_cursor_row],1
 jne .failed
 cmp word [screen_cursor_column],1
 jne .failed
 mov ax,0xb800
 mov es,ax
 cmp word [es:158],0x1e43
 jne .failed
 cmp word [es:160],0x1e44
 jne .failed
 mov word [scroll_enabled],1
 mov ax,24
 mov dx,79
 call screen_set_cursor
 mov word [render_input_character],'E'
 call render_test_character
 mov word [render_input_character],'F'
 call render_test_character
 mov ax,0xb800
 mov es,ax
 cmp word [es:23*160+158],0x1e45
 jne .failed
 cmp word [es:24*160],0x1e46
 jne .failed
 cmp word [screen_cursor_row],24
 jne .failed
 cmp word [screen_cursor_column],1
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
; Unrecovered features trap visibly instead of silently pretending to work.
%macro missing 2
 global %1
 %1:
 mov word [render_unimplemented_service],%2
 int 3
 mov ax,0x4c02
 int 0x21
%endmacro
missing render_service_b9f7,0xb9f7
missing render_font_output,0xbb53
missing screen_adjust_attribute_boundary,0x2adc
missing erase_repair_attributes,0x2d98
missing erase_complex_protected,0xd05f
missing screen_viewport_enter,0x482a
missing screen_viewport_leave,0x4850
missing screen_viewport_refresh,0x2fb8
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
global attributes_color_mode
attributes_color_mode:
word_state screen_doublewidth_enabled,1
word_state screen_cursor_wrap,0
word_state screen_last_row,24
word_state csi_last_row,24
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
word_state attributes_current,7
word_state csi_wrap_pending,0
word_state render_autowrap,1
word_state render_deferred_row,0
word_state render_deferred_column,0
word_state scroll_enabled,0
word_state terminal_mode_372c,0
word_state ansi_charset_g0_flag_a,0
word_state ansi_charset_g1_flag_a,0
word_state ansi_charset_g0_flag_graphics,0
word_state ansi_charset_g1_flag_graphics,0
word_state cursor_state_value_cdfc,0
word_state cursor_state_value_ce04,0
word_state scroll_suppress_next_linefeed,0
word_state render_translation_enabled,0
word_state render_translation_base,render_translation_table
word_state render_direct_output,0
word_state erase_protection_mode,0
word_state render_linefeed_suppression_enabled,0
word_state render_input_character,0
word_state render_unimplemented_service,0
word_state text_video_segment,0xb800
word_state text_bios_output,0
word_state text_cga_status_port,0
global render_translation_mask,render_graphics_map,render_translation_table
render_translation_mask: db 255
render_graphics_map: times 128 db 0
render_translation_table: times 256 db 0
word_state attributes_normal_value,7
word_state erase_lineflags_enabled,0
word_state attributes_monochrome,0
word_state erase_cell_count,2000
word_state erase_attribute_values_base,erase_attribute_values
word_state erase_shadow_offset,erase_shadow_cells
word_state erase_shadow_segment,seg erase_shadow_cells
word_state csi_erase_attribute,7
word_state scroll_skip_attribute_scan,0
word_state scroll_unimplemented_service,0
global erase_attribute_flags,erase_attribute_values,erase_shadow_cells
erase_attribute_flags equ screen_attribute_cells
erase_attribute_values: times 4096 db 7
erase_shadow_cells: times 8192 db 0
SEGMENT STACK stack class=STACK use16
resb 4096
stack_top:
