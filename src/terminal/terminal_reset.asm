; Maintained current-profile RIS, intentionally distinct from native20a4.
; Capture once after configuration, keyboard import and video initialization.
BITS 16
CPU 8086
GROUP DGROUP _DATA _BSS STACK
SEGMENT _TEXT public class=CODE use16
global terminal_reset_capture,ansi_escape_service_20a4,csi_reset_terminal
extern terminal_clear_home,terminal_abort
extern terminal_keymap,terminal_tab_stops,ansi_parameters,screen_line_flags
extern screen_attribute_cells,erase_attribute_values,erase_shadow_cells
extern csi_terminal_id
extern csi_previous_terminal_id
extern attributes_normal_value
extern attributes_bold_value
extern attributes_preset_value
extern attributes_reverse_value
extern attributes_underline_value
extern attributes_current
extern attributes_bold_active
extern attributes_blink_active
extern attributes_monochrome
extern attributes_color_mode
extern csi_last_column
extern csi_column_count
extern csi_last_row
extern csi_row_count
extern screen_columns
extern screen_video_row_bytes
extern screen_first_row
extern screen_last_row
extern csi_origin_row
extern csi_origin_bottom
extern screen_cursor_row
extern screen_cursor_column
extern screen_visible_column
extern screen_previous_row
extern screen_previous_column
extern screen_video_offset
extern screen_attribute_offset
extern screen_viewport_active
extern screen_viewport_enabled
extern screen_viewport_offset
extern screen_viewport_left
extern screen_viewport_right
extern screen_attributes_base
extern erase_attribute_values_base
extern erase_shadow_offset
extern erase_shadow_segment
extern screen_use_bios_cursor
extern screen_attribute_checks
extern screen_cursor_wrap
extern screen_vertical_attribute_check
extern screen_reverse_wrap_blocked
extern erase_lineflags_enabled
extern erase_protection_mode
extern erase_cell_count
extern csi_saved_row
extern csi_saved_column
extern cursor_state_value_cdfc
extern cursor_state_value_ce04
extern cursor_state_value_1d20
extern cursor_state_saved_cdf0
extern cursor_state_saved_cdec
extern cursor_state_saved_cdfc
extern cursor_state_saved_ce04
extern cursor_state_saved_1f70
extern cursor_state_saved_1d20
extern cursor_state_saved_cdd2
extern cursor_state_saved_3342
extern modes_value_1d1a
extern modes_value_3980
extern modes_value_3982
extern modes_cursor_flags
extern cursor_shape_start_scanline
extern cursor_shape_end_scanline
extern cursor_shape_visibility_state
extern csi_report_private_prefix
extern csi_printer_ready
extern csi_wrap_pending
extern csi_origin_mode
extern ansi_charset_g0_flag_a
extern ansi_charset_g1_flag_a
extern ansi_charset_g0_flag_graphics
extern ansi_charset_g1_flag_graphics
extern ansi_parameter_count
extern ansi_command
extern ansi_private
extern ansi_secondary
extern ansi_parse_error
extern csi_unimplemented_service
extern scroll_enabled
extern scroll_suppress_next_linefeed
extern terminal_dec_keys
extern terminal_mode_372c
extern render_deferred_row
extern render_deferred_column
extern render_direct_output
extern render_linefeed_suppression_enabled
extern render_input_character
extern terminal_c1_enabled
extern terminal_cr_adds_lf
extern terminal_tab_wrap
extern terminal_tab_mode_8ff8
extern terminal_backspace_mode_9058
extern terminal_newline_mode_9020
extern terminal_control_mode_9026
extern terminal_control_mode_1fb0
extern attributes_reverse_active
extern csi_erase_attribute
extern terminal_backspace_erases
terminal_reset_capture:
 push bp
 push si
 push di
 push es
 push bx
 push cx
 push dx
 cld
 mov ax,[csi_terminal_id]
 cmp ax,4
 je .supported
 cmp ax,6
 jne .unsupported
.supported:
 push ds
 pop es
 mov si,reset_word_addresses
 mov di,reset_words
 mov cx,RESET_WORD_COUNT
.word:
 lodsw
 mov bx,ax
 mov ax,[bx]
 stosw
 loop .word
 mov si,reset_byte_addresses
 mov di,reset_bytes
 mov cx,RESET_BYTE_COUNT
.byte:
 lodsw
 mov bx,ax
 mov al,[bx]
 stosb
 loop .byte
 mov si,terminal_keymap
 mov di,reset_keymap
 mov cx,948
 rep movsb
 mov si,terminal_tab_stops
 mov di,reset_tabs
 mov cx,30
 rep movsb
 mov word [reset_ready],1
 xor ax,ax
 jmp .done
.unsupported:
 mov word [reset_ready],0
 mov ax,1
.done:
 pop dx
 pop cx
 pop bx
 pop es
 pop di
 pop si
 pop bp
 ret

ansi_escape_service_20a4:
csi_reset_terminal:
 ; Native callers pass a cdecl argument; we neither consume nor interpret it.
 cmp word [reset_ready],1
 je .restore
 mov ax,0x20a4
 mov [csi_unimplemented_service],ax
 jmp terminal_abort
.restore:
 push bp
 push si
 push di
 push es
 push bx
 push cx
 push dx
 cld
 push ds
 pop es
 mov si,reset_word_addresses
 mov di,reset_words
 mov cx,RESET_WORD_COUNT
.word:
 lodsw
 mov bx,ax
 mov ax,[di]
 mov [bx],ax
 add di,2
 loop .word
 mov si,reset_byte_addresses
 mov di,reset_bytes
 mov cx,RESET_BYTE_COUNT
.byte:
 lodsw
 mov bx,ax
 mov al,[di]
 mov [bx],al
 inc di
 loop .byte
 mov si,reset_keymap
 mov di,terminal_keymap
 mov cx,948
 rep movsb
 mov si,reset_tabs
 mov di,terminal_tab_stops
 mov cx,30
 rep movsb
 xor ax,ax
 mov di,ansi_parameters
 mov cx,16
 rep stosw
 mov di,screen_line_flags
 mov cx,64
 rep stosw
 mov di,screen_attribute_cells
 mov cx,2048
 rep stosw
 mov di,erase_attribute_values
 mov cx,2048
 rep stosw
 mov ax,seg erase_shadow_cells
 mov es,ax
 xor ax,ax
 mov di,erase_shadow_cells
 mov cx,4096
 rep stosw
 push ds
 pop es
 ; Startup protection/viewport gates and owned pointers have been restored.
 ; This actual recovered helper clears the full video rectangle and homes.
 call terminal_clear_home
 mov ch,[cursor_shape_start_scanline]
 mov cl,[cursor_shape_end_scanline]
 cmp word [cursor_shape_visibility_state],0
 jne .cursor
 or ch,0x20
.cursor:
 mov ah,1
 int 0x10
 pop dx
 pop cx
 pop bx
 pop es
 pop di
 pop si
 pop bp
 ret

SEGMENT _DATA public align=16 class=DATA use16
reset_ready: dw 0
reset_word_addresses:
 dw csi_terminal_id
 dw csi_previous_terminal_id
 dw attributes_normal_value
 dw attributes_bold_value
 dw attributes_preset_value
 dw attributes_reverse_value
 dw attributes_underline_value
 dw attributes_current
 dw attributes_bold_active
 dw attributes_blink_active
 dw attributes_monochrome
 dw attributes_color_mode
 dw csi_last_column
 dw csi_column_count
 dw csi_last_row
 dw csi_row_count
 dw screen_columns
 dw screen_video_row_bytes
 dw screen_first_row
 dw screen_last_row
 dw csi_origin_row
 dw csi_origin_bottom
 dw screen_cursor_row
 dw screen_cursor_column
 dw screen_visible_column
 dw screen_previous_row
 dw screen_previous_column
 dw screen_video_offset
 dw screen_attribute_offset
 dw screen_viewport_active
 dw screen_viewport_enabled
 dw screen_viewport_offset
 dw screen_viewport_left
 dw screen_viewport_right
 dw screen_attributes_base
 dw erase_attribute_values_base
 dw erase_shadow_offset
 dw erase_shadow_segment
 dw screen_use_bios_cursor
 dw screen_attribute_checks
 dw screen_cursor_wrap
 dw screen_vertical_attribute_check
 dw screen_reverse_wrap_blocked
 dw erase_lineflags_enabled
 dw erase_protection_mode
 dw erase_cell_count
 dw csi_saved_row
 dw csi_saved_column
 dw cursor_state_value_cdfc
 dw cursor_state_value_ce04
 dw cursor_state_value_1d20
 dw cursor_state_saved_cdf0
 dw cursor_state_saved_cdec
 dw cursor_state_saved_cdfc
 dw cursor_state_saved_ce04
 dw cursor_state_saved_1f70
 dw cursor_state_saved_1d20
 dw cursor_state_saved_cdd2
 dw cursor_state_saved_3342
 dw modes_value_1d1a
 dw modes_value_3980
 dw modes_value_3982
 dw modes_cursor_flags
 dw cursor_shape_start_scanline
 dw cursor_shape_end_scanline
 dw cursor_shape_visibility_state
 dw csi_report_private_prefix
 dw csi_printer_ready
 dw csi_wrap_pending
 dw csi_origin_mode
 dw ansi_charset_g0_flag_a
 dw ansi_charset_g1_flag_a
 dw ansi_charset_g0_flag_graphics
 dw ansi_charset_g1_flag_graphics
 dw ansi_parameter_count
 dw ansi_command
 dw ansi_private
 dw ansi_secondary
 dw ansi_parse_error
 dw csi_unimplemented_service
 dw scroll_enabled
 dw scroll_suppress_next_linefeed
 dw terminal_dec_keys
 dw terminal_mode_372c
 dw render_deferred_row
 dw render_deferred_column
 dw render_direct_output
 dw render_linefeed_suppression_enabled
 dw render_input_character
 dw terminal_c1_enabled
 dw terminal_cr_adds_lf
 dw terminal_tab_wrap
 dw terminal_tab_mode_8ff8
 dw terminal_backspace_mode_9058
 dw terminal_newline_mode_9020
 dw terminal_control_mode_9026
 dw terminal_control_mode_1fb0
RESET_WORD_COUNT equ ($-reset_word_addresses)/2
reset_byte_addresses:
 dw attributes_reverse_active
 dw csi_erase_attribute
 dw terminal_backspace_erases
RESET_BYTE_COUNT equ ($-reset_byte_addresses)/2
SEGMENT _BSS public align=16 class=BSS use16
reset_words: resw RESET_WORD_COUNT
reset_bytes: resb RESET_BYTE_COUNT
reset_keymap: resb 948
reset_tabs: resb 30
SEGMENT STACK stack align=16 class=STACK use16
