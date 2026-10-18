; Combined source-only protocol/cursor diagnostic. Unrecovered services fail fast.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA _BSS STACK
extern ansi_escape_entry
extern terminal_keyboard_mode,terminal_clear_home
global ansi_next_byte, ansi_unread_byte, ansi_control_character, ansi_reset
ansi_next_byte:
 inc word [csi_receive_calls]
 mov bx,[ansi_input_position]
 cmp bx,[ansi_input_length]
 jae .timeout
 inc word [ansi_input_position]
 add bx,[ansi_input_pointer]
 xor ax,ax
 mov al,[bx]
 ret
.timeout:
 mov ax,0xffff
 ret
ansi_unread_byte:
 cmp word [ansi_input_position],0
 je .done
 dec word [ansi_input_position]
.done:
 ret
extern terminal_receive_character
ansi_control_character:
 jmp terminal_receive_character
ansi_reset:
 push ax
 push cx
 push di
 push es
 mov ax,ds
 mov es,ax
 xor ax,ax
 mov di,ansi_parameters
 mov cx,16
 cld
 rep stosw
 mov [ansi_parameter_count],ax
 mov [ansi_command],ax
 mov [ansi_private],ax
 mov [ansi_secondary],ax
 mov [ansi_parse_error],ax
 mov [ansi_input_position],ax
 mov [ansi_control_count],ax
 mov [ansi_last_control],ax
 mov [csi_receive_calls],ax
 mov [csi_unimplemented_service],ax
 pop es
 pop di
 pop cx
 pop ax
 ret
; Output collector obeys original callee-cleanup ABI; no actual modem is used.
global csi_transmit_byte,csi_transmit_string
csi_transmit_byte:
 mov bx,sp
 mov ax,[bx+2]
 call csi_append_output
 ret 2
csi_transmit_string:
 mov bx,sp
 push si
 mov si,[bx+2]
.next:
 lodsb
 or al,al
 jz .done
 call csi_append_output
 jmp .next
.done:
 pop si
 ret 2
csi_append_output:
 push bx
 mov bx,[csi_output_length]
 cmp bx,256
 jae csi_output_overflow
 mov [csi_output_buffer+bx],al
 inc word [csi_output_length]
 pop bx
 ret
csi_output_overflow:
 mov ax,0xfffe
 jmp csi_unimplemented
global ansi_escape_service_12c8,csi_service_12c8
extern screen_wrap_forward,screen_linefeed,scroll_up,scroll_index,scroll_reverse_index
ansi_escape_service_12c8:
csi_service_12c8:
 jmp screen_wrap_forward
global ansi_escape_service_20a4
global csi_reset_terminal
ansi_escape_service_20a4:
csi_reset_terminal:
 mov ax,0x20a4
 jmp csi_unimplemented
extern csi_clear_tabs
extern csi_reset_scroll_region
global screen_adjust_attribute_boundary
screen_adjust_attribute_boundary:
 mov ax,0x2adc
 jmp csi_unimplemented
global screen_viewport_refresh
screen_viewport_refresh:
 mov ax,0x2fb8
 jmp csi_unimplemented
global screen_viewport_enter
screen_viewport_enter:
 mov ax,0x482a
 jmp csi_unimplemented
global screen_viewport_leave
screen_viewport_leave:
 mov ax,0x4850
 jmp csi_unimplemented
global csi_service_d270
csi_service_d270:
 mov ax,0xd270
 jmp csi_unimplemented
global csi_service_d440
csi_service_d440:
 mov ax,0xd440
 jmp csi_unimplemented
global csi_service_d668
csi_service_d668:
 mov ax,0xd668
 jmp csi_unimplemented
global csi_service_d73c
csi_service_d73c:
 mov ax,0xd73c
 jmp csi_unimplemented
global csi_service_da12
csi_service_da12:
 mov ax,0xda12
 jmp csi_unimplemented
global ansi_escape_service_da46
ansi_escape_service_da46:
 jmp scroll_index
global ansi_escape_service_da84
global csi_service_da84
ansi_escape_service_da84:
csi_service_da84:
 jmp scroll_reverse_index
global ansi_escape_service_dac6
ansi_escape_service_dac6:
 mov ax,0xdac6
 jmp csi_unimplemented
global csi_service_daf2
csi_service_daf2:
 mov ax,0xdaf2
 jmp csi_unimplemented
global ansi_escape_service_dd58
extern csi_primary_attributes,csi_device_status
ansi_escape_service_dd58:
 jmp csi_primary_attributes
global ansi_escape_service_dd74,ansi_escape_service_ddbc
extern csi_save_cursor,csi_restore_cursor
; Tail jumps preserve the caller-cleanup mode argument beneath the return address.
ansi_escape_service_dd74:
 jmp csi_save_cursor
ansi_escape_service_ddbc:
 jmp csi_restore_cursor
extern csi_set_modes,csi_reset_modes
global modes_keyboard_map
modes_keyboard_map:
 jmp terminal_keyboard_mode
global modes_screen_width
modes_screen_width:
 mov ax,0x2a6e
 jmp csi_unimplemented
global csi_media_copy
csi_media_copy:
 mov ax,0xe084
 jmp csi_unimplemented
global ansi_escape_service_e0f8
ansi_escape_service_e0f8:
 mov ax,0xe0f8
 jmp csi_unimplemented
global ansi_escape_service_ec94
ansi_escape_service_ec94:
 mov ax,0xec94
 jmp csi_unimplemented
global erase_complex_protected,erase_repair_attributes
erase_complex_protected:
 mov ax,0xd05f
 jmp csi_unimplemented
erase_repair_attributes:
 mov ax,0x2d98
 jmp csi_unimplemented
csi_unimplemented:
 mov [csi_unimplemented_service],ax
 int 3
 mov ax,0x4c02
 int 0x21
global render_service_b9f7
render_service_b9f7:
 mov ax,0xb9f7
 jmp csi_unimplemented
global render_font_output
render_font_output:
 mov ax,0xbb53
 jmp csi_unimplemented
global terminal_sink_36fc
terminal_sink_36fc:
 mov ax,0x36fc
 jmp csi_unimplemented
global terminal_sink_8436
terminal_sink_8436:
 mov ax,0x8436
 jmp csi_unimplemented
global terminal_sink_427f
terminal_sink_427f:
 mov ax,0x427f
 jmp csi_unimplemented
global terminal_sink_bb23
terminal_sink_bb23:
 mov ax,0xbb23
 jmp csi_unimplemented
global terminal_escape_b98b
terminal_escape_b98b:
 mov ax,0xb98b
 jmp csi_unimplemented
global terminal_escape_b9a3
terminal_escape_b9a3:
 mov ax,0xb9a3
 jmp csi_unimplemented
global terminal_escape_b97f
terminal_escape_b97f:
 mov ax,0xb97f
 jmp csi_unimplemented
global terminal_escape_b9af
terminal_escape_b9af:
 mov ax,0xb9af
 jmp csi_unimplemented
global terminal_escape_b997
terminal_escape_b997:
 mov ax,0xb997
 jmp csi_unimplemented
global terminal_escape_bb3b
terminal_escape_bb3b:
 mov ax,0xbb3b
 jmp csi_unimplemented
global terminal_control_0e62
terminal_control_0e62:
 mov ax,0xe62
 jmp csi_unimplemented
global terminal_control_0e70
terminal_control_0e70:
 mov ax,0xe70
 jmp csi_unimplemented
global terminal_control_4cd7
terminal_control_4cd7:
 mov ax,0x4cd7
 jmp csi_unimplemented
global terminal_control_0e7c
terminal_control_0e7c:
 mov ax,0xe7c
 jmp csi_unimplemented
global terminal_control_0ede
terminal_control_0ede:
 mov ax,0xede
 jmp csi_unimplemented
global terminal_control_3778
terminal_control_3778:
 mov ax,0x3778
 jmp csi_unimplemented
global terminal_control_0f62
terminal_control_0f62:
 mov ax,0xf62
 jmp csi_unimplemented
global terminal_control_0fb0
terminal_control_0fb0:
 mov ax,0xfb0
 jmp csi_unimplemented
global terminal_control_1040
terminal_control_1040:
 mov ax,0x1040
 jmp csi_unimplemented
global terminal_control_1064
terminal_control_1064:
 mov ax,0x1064
 jmp csi_unimplemented
global terminal_control_1096
terminal_control_1096:
 mov ax,0x1096
 jmp csi_unimplemented
global terminal_control_10ce
terminal_control_10ce:
 mov ax,0x10ce
 jmp csi_unimplemented
global terminal_control_10fc
terminal_control_10fc:
 mov ax,0x10fc
 jmp csi_unimplemented
global terminal_control_110a
terminal_control_110a:
 mov ax,0x110a
 jmp csi_unimplemented
global terminal_control_113e
terminal_control_113e:
 mov ax,0x113e
 jmp csi_unimplemented
global terminal_control_115c
terminal_control_115c:
 mov ax,0x115c
 jmp csi_unimplemented
global terminal_control_1190
terminal_control_1190:
 mov ax,0x1190
 jmp csi_unimplemented
global terminal_control_11a8
terminal_control_11a8:
 mov ax,0x11a8
 jmp csi_unimplemented
global terminal_control_123c
terminal_control_123c:
 mov ax,0x123c
 jmp csi_unimplemented
global terminal_control_1248
terminal_control_1248:
 mov ax,0x1248
 jmp csi_unimplemented
global terminal_control_127e
terminal_control_127e:
 mov ax,0x127e
 jmp csi_unimplemented
global terminal_control_1292
terminal_control_1292:
 mov ax,0x1292
 jmp csi_unimplemented
global terminal_control_12b0
terminal_control_12b0:
 mov ax,0x12b0
 jmp csi_unimplemented
global terminal_process_stream
terminal_process_stream:
 call ansi_next_byte
 cmp ax,0xffff
 je .done
 push ax
 call terminal_receive_character
 add sp,2
 jmp terminal_process_stream
.done:
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
 mov ax,1
 push ax
 call csi_clear_tabs
 add sp,2
 mov word [ansi_input_pointer],stream_sample
 mov word [ansi_input_length],stream_end-stream_sample
 call ansi_reset
 call terminal_process_stream
 mov ax,0xb800
 mov es,ax
 cmp word [es:0],0x0741
 jne .failed
 cmp word [es:2],0x0742
 jne .failed
 cmp word [es:16],0x0743
 jne .failed
 cmp word [es:160],0x0445
 jne .failed
 cmp word [screen_cursor_row],1
 jne .failed
 cmp word [screen_cursor_column],1
 jne .failed
 ; Maintained byte ABI must not jump through data for signed word arguments.
 mov ax,0xffb1
 push ax
 call terminal_receive_character
 add sp,2
 mov ax,0xffff
 push ax
 call terminal_receive_character
 add sp,2
 mov ax,0xb800
 mov es,ax
 cmp word [es:162],0x04b1
 jne .failed
 cmp word [es:164],0x04ff
 jne .failed
 mov ax,0x4c00
 int 0x21
.failed:
 mov ax,0x4c01
 int 0x21
SEGMENT _DATA public align=16 class=DATA use16
global csi_saved_row
csi_saved_row: dw 0
global csi_saved_column
csi_saved_column: dw 0
global cursor_state_value_cdfc
cursor_state_value_cdfc: dw 0
global cursor_state_value_ce04
cursor_state_value_ce04: dw 0
global cursor_state_value_1d20
cursor_state_value_1d20: dw 1
global cursor_state_saved_cdf0
cursor_state_saved_cdf0: dw 0
global cursor_state_saved_cdec
cursor_state_saved_cdec: dw 0
global cursor_state_saved_cdfc
cursor_state_saved_cdfc: dw 0
global cursor_state_saved_ce04
cursor_state_saved_ce04: dw 0
global cursor_state_saved_1f70
cursor_state_saved_1f70: dw 0
global cursor_state_saved_1d20
cursor_state_saved_1d20: dw 0
global cursor_state_saved_cdd2
cursor_state_saved_cdd2: dw 0
global cursor_state_saved_3342
cursor_state_saved_3342: dw 0
global modes_value_1d1a
modes_value_1d1a: dw 0
global modes_value_3980
modes_value_3980: dw 0
global modes_value_3982
modes_value_3982: dw 0
global modes_cursor_flags
modes_cursor_flags: dw 0
global cursor_shape_start_scanline,cursor_shape_end_scanline,cursor_shape_visibility_state
cursor_shape_start_scanline: dw 6
cursor_shape_end_scanline: dw 15
cursor_shape_visibility_state: dw 1
global csi_terminal_id
csi_terminal_id:
 dw 4
global csi_report_private_prefix,csi_printer_ready
global scroll_skip_attribute_scan
csi_report_private_prefix:
scroll_skip_attribute_scan: dw 0
csi_printer_ready: dw 0
global attributes_normal_value
attributes_normal_value:
 dw 7
global attributes_bold_value
attributes_bold_value:
 dw 15
global attributes_preset_value
attributes_preset_value:
 dw 23
global attributes_reverse_value
attributes_reverse_value:
 dw 112
global attributes_underline_value
attributes_underline_value:
 dw 1
global attributes_current
attributes_current:
 dw 7
global attributes_reverse_active
attributes_reverse_active:
 db 0
global csi_previous_terminal_id
csi_previous_terminal_id:
 dw 0
global csi_secondary_322c
csi_secondary_322c:
 db '1;10;0',0
global screen_viewport_active
screen_viewport_active:
 dw 0
global csi_last_column
global screen_last_column
csi_last_column:
screen_last_column:
 dw 79
global csi_column_count
global screen_attribute_row_bytes
csi_column_count:
screen_attribute_row_bytes:
 dw 80
global csi_wrap_pending
csi_wrap_pending:
 dw 0
global screen_video_offset
screen_video_offset:
 dw 0
global screen_attribute_offset
screen_attribute_offset:
 dw 0
global screen_previous_column
screen_previous_column:
 dw 0
global csi_last_row
csi_last_row:
 dw 24
global csi_row_count
csi_row_count:
 dw 25
global screen_attribute_checks
screen_attribute_checks:
 dw 0
global attributes_bold_active
attributes_bold_active:
 dw 0
global attributes_blink_active
attributes_blink_active:
 dw 0
global screen_cursor_row
screen_cursor_row:
 dw 0
global screen_cursor_column
screen_cursor_column:
 dw 0
global screen_visible_column
screen_visible_column:
 dw 0
global screen_previous_row
screen_previous_row:
 dw 0
global screen_viewport_offset
screen_viewport_offset:
 dw 0
global screen_attributes_base
screen_attributes_base:
 dw screen_attribute_cells
global csi_secondary_prefix
csi_secondary_prefix:
 db 27,'[>',0
global csi_secondary_7529
csi_secondary_7529:
 db '24;10;0',0
global screen_use_bios_cursor
screen_use_bios_cursor:
 dw 1
global screen_columns
screen_columns:
 dw 80
global screen_video_row_bytes
screen_video_row_bytes:
 dw 160
global screen_viewport_right
screen_viewport_right:
 dw 79
global attributes_monochrome
attributes_monochrome:
 dw 0
global screen_cursor_wrap
screen_cursor_wrap:
 dw 0
global screen_vertical_attribute_check
screen_vertical_attribute_check:
 dw 0
global screen_reverse_wrap_blocked
screen_reverse_wrap_blocked:
 dw 0
global ansi_parameters
ansi_parameters:
 times 16 dw 0
global ansi_parameter_canary
ansi_parameter_canary: dw 0xa55a
global ansi_parameter_count
ansi_parameter_count:
 dw 0
global ansi_command
ansi_command:
 dw 0
global csi_origin_mode
csi_origin_mode:
 dw 0
global ansi_charset_g0_flag_a
ansi_charset_g0_flag_a:
 dw 0
global ansi_charset_g1_flag_a
ansi_charset_g1_flag_a:
 dw 0
global ansi_charset_g0_flag_graphics
ansi_charset_g0_flag_graphics:
 dw 0
global ansi_charset_g1_flag_graphics
ansi_charset_g1_flag_graphics:
 dw 0
global screen_viewport_enabled
screen_viewport_enabled:
 dw 0
global csi_scroll_top
global screen_first_row
csi_scroll_top:
screen_first_row:
 dw 0
global screen_viewport_left
screen_viewport_left:
 dw 0
global csi_scroll_bottom
global screen_last_row
csi_scroll_bottom:
screen_last_row:
 dw 24
global ansi_private
ansi_private:
 dw 0
global csi_origin_row
global screen_top_margin
csi_origin_row:
screen_top_margin:
 dw 0
global ansi_secondary
ansi_secondary:
 dw 0
global csi_origin_bottom
global screen_bottom_margin
csi_origin_bottom:
screen_bottom_margin:
 dw 24
global screen_line_flags
screen_line_flags:
 times 128 db 0
global csi_erase_attribute
csi_erase_attribute:
 db 7
global attributes_color_mode
global screen_doublewidth_enabled
attributes_color_mode:
screen_doublewidth_enabled:
 dw 1
global ansi_parse_error
ansi_parse_error: dw 0
global ansi_input_position
ansi_input_position: dw 0
global ansi_input_pointer
ansi_input_pointer: dw default_sample
global ansi_input_length
ansi_input_length: dw default_end-default_sample
global ansi_control_count
ansi_control_count: dw 0
global ansi_last_control
ansi_last_control: dw 0
global csi_receive_calls
csi_receive_calls: dw 0
global csi_output_length
csi_output_length: dw 0
global csi_unimplemented_service
csi_unimplemented_service: dw 0
esc_save_sample: db '7'
esc_restore_sample: db '8'
csi_save_sample: db '[s'
csi_save_end:
csi_restore_sample: db '[u'
csi_restore_end:
reset_sgr_sample: db '[0m'
reset_sgr_end:
default_sample: db '[10;20H'
default_end:
sgr_sample: db '[31;1;5m'
sgr_end:
up_sample: db '[2A'
up_end:
q_sample: db '[;4qNEXT'
q_end:
global scroll_enabled,scroll_suppress_next_linefeed
scroll_enabled: dw 1
scroll_suppress_next_linefeed: dw 0
global erase_lineflags_enabled,erase_protection_mode,erase_cell_count
erase_lineflags_enabled: dw 0
erase_protection_mode: dw 0
erase_cell_count: dw 2000
global erase_attribute_values_base,erase_shadow_offset,erase_shadow_segment
erase_attribute_values_base: dw erase_attribute_values
erase_shadow_offset: dw erase_shadow_cells
erase_shadow_segment: dw seg erase_shadow_cells
scroll_bottom_sample: db '[25;20H'
scroll_bottom_end:
scroll_top_sample: db '[1;20H'
scroll_top_end:
index_sample: db 'D'
reverse_index_sample: db 'M'
next_line_sample: db 'E'
modes_cursor_set: db '[?25h'
modes_cursor_set_end:
modes_cursor_reset: db '[?25l'
modes_cursor_reset_end:
modes_keys_set: db '[?1h'
modes_keys_set_end:
modes_keys_reset: db '[?1l'
modes_keys_reset_end:
modes_wrap_set: db '[?7h'
modes_wrap_set_end:
modes_wrap_reset: db '[?7l'
modes_wrap_reset_end:
modes_origin_set: db '[?6h'
modes_origin_set_end:
modes_origin_reset: db '[?6l'
modes_origin_reset_end:
erase_sample: db '[2J'
erase_end:
global terminal_dec_keys,terminal_tab_stops,terminal_keymap,terminal_keymap_end,terminal_mode_372c
terminal_dec_keys: dw 0
terminal_tab_stops: times 30 db 0xfe
terminal_keymap: times 948 db 0
terminal_keymap_end:
terminal_mode_372c: dw 0
SEGMENT _BSS public align=16 class=BSS use16
global ansi_input_buffer,csi_output_buffer,screen_attribute_cells
ansi_input_buffer: resb 2048
csi_output_buffer: resb 256
screen_attribute_cells: resb 4096
global erase_attribute_values,erase_shadow_cells
erase_attribute_values: resb 4096
erase_shadow_cells: resb 8192
global render_autowrap,terminal_input_mode_8fe8
render_autowrap equ cursor_state_value_1d20
terminal_input_mode_8fe8 equ terminal_dec_keys
SEGMENT STACK stack align=16 class=STACK use16
resb 4096
stack_top:

SEGMENT _DATA
global render_deferred_row
render_deferred_row: dw 0
global render_deferred_column
render_deferred_column: dw 0
global render_translation_enabled
render_translation_enabled: dw 0
global render_translation_base
render_translation_base: dw render_translation_table
global render_direct_output
render_direct_output: dw 0
global render_linefeed_suppression_enabled
render_linefeed_suppression_enabled: dw 0
global render_input_character
render_input_character: dw 0
global text_video_segment
text_video_segment: dw 0xb800
global text_bios_output
text_bios_output: dw 0
global text_cga_status_port
text_cga_status_port: dw 0
global scroll_unimplemented_service
scroll_unimplemented_service: dw 0
global render_translation_mask
render_translation_mask: db 255
global render_graphics_map
render_graphics_map: times 128 db 0
global render_translation_table
render_translation_table: times 256 db 0
global terminal_c1_enabled
terminal_c1_enabled: dw 0
global terminal_sink_3988_enabled
terminal_sink_3988_enabled: dw 0
global terminal_cr_adds_lf
terminal_cr_adds_lf: dw 0
global terminal_sink_398a_enabled
terminal_sink_398a_enabled: dw 0
global terminal_sink_398c_disabled
terminal_sink_398c_disabled: dw 0
global terminal_sink_handle
terminal_sink_handle: dw 0
global terminal_sink_error_state
terminal_sink_error_state: dw 0
global terminal_tab_wrap
terminal_tab_wrap: dw 0
global terminal_tab_mode_8ff8
terminal_tab_mode_8ff8: dw 0
global terminal_backspace_mode_9058
terminal_backspace_mode_9058: dw 0
global terminal_backspace_erases
terminal_backspace_erases: db 0
global terminal_newline_mode_9020
terminal_newline_mode_9020: dw 0
global terminal_history_pending,terminal_history_pointer,terminal_history_start,terminal_history_end,terminal_history_wrapped,terminal_history_buffer
terminal_history_start: dw terminal_history_buffer
terminal_history_pointer: dw terminal_history_buffer,seg terminal_history_buffer
terminal_history_end: dw terminal_history_buffer+4096
terminal_history_wrapped: dw 0
terminal_history_pending: db 0
terminal_history_buffer: times 4096 db 0
stream_sample: db "AB",9,"C",13,10,27,"[31mD",8,"E"
stream_end:
