; Maintained initial terminal state. Original DS aliases stay shared.
; Source-owned defaults; no original install/configuration bytes are embedded.
BITS 16
CPU 8086
GROUP DGROUP _DATA _BSS STACK
SEGMENT _DATA public align=16 class=DATA use16
; Source-owned geometry for the recovered UART's bottom-row status service.
global ui_window_rows,ui_flow_region_cells,ui_flow_video_base
global ui_flow_coordinate_base,ui_flow_suppressed,ui_flow_attribute
ui_window_rows: dw 25
global snapshot_video_columns
snapshot_video_columns:
ui_flow_region_cells: dw 80
ui_flow_video_base: dw 0x0f00
ui_flow_coordinate_base: dw 0x1800
ui_flow_suppressed: dw 0
ui_flow_attribute: dw 0x001e
global csi_saved_row
csi_saved_row: dw 0
global csi_saved_column
csi_saved_column: dw 0
global cursor_state_value_cdfc
cursor_state_value_cdfc: dw 1
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
cursor_state_saved_1f70: dw 7
global cursor_state_saved_1d20
cursor_state_saved_1d20: dw 1
global cursor_state_saved_cdd2
cursor_state_saved_cdd2: dw 0
global cursor_state_saved_3342
cursor_state_saved_3342: dw 0
global modes_value_1d1a
modes_value_1d1a: dw 0
global modes_value_3980
modes_value_3980: dw 1
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
 dw 6 ; Proved original ANSI profile (4 is VT220).
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
global snapshot_shadow_columns
snapshot_shadow_columns:
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
global snapshot_video_stride
snapshot_video_stride:
screen_video_row_bytes:
 dw 160
global screen_viewport_right
screen_viewport_right:
 dw 79
global attributes_monochrome
attributes_monochrome:
 dw 1 ; Original 8ff6 profile flag: enabled for ANSI/IBM PC, not monochrome.
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
global snapshot_shadow_enabled
snapshot_shadow_enabled:
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
global csi_unimplemented_service
csi_unimplemented_service: dw 0
global scroll_enabled,scroll_suppress_next_linefeed
scroll_enabled: dw 1
scroll_suppress_next_linefeed: dw 0
global erase_lineflags_enabled,erase_protection_mode,erase_cell_count
erase_lineflags_enabled: dw 0
erase_protection_mode: dw 0
erase_cell_count: dw 2000
global erase_attribute_values_base,erase_shadow_offset,erase_shadow_segment
erase_attribute_values_base: dw erase_attribute_values
global snapshot_shadow_offset
snapshot_shadow_offset:
erase_shadow_offset: dw erase_shadow_cells
global snapshot_shadow_segment
snapshot_shadow_segment:
erase_shadow_segment: dw seg erase_shadow_cells
global terminal_dec_keys,terminal_tab_stops,terminal_keymap,terminal_keymap_end,terminal_mode_372c
terminal_dec_keys: dw 1
terminal_tab_stops: times 30 db 0xfe
terminal_keymap:
 ; Proved original slots72..75 are Up/Down/Left/Right. Keep startup arrows
 ; available to component callers; main initializes all maintained defaults.
 times 72*12 db 0
 db 27,'[A',0
 times 8 db 0
 db 27,'[B',0
 times 8 db 0
 db 27,'[D',0
 times 8 db 0
 db 27,'[C',0
 times 8 db 0
 times 3*12 db 0
terminal_keymap_end:
terminal_mode_372c: dw 0
SEGMENT _BSS public align=16 class=BSS use16
global screen_attribute_cells
screen_attribute_cells: resb 4096
global erase_attribute_values
erase_attribute_values: resb 4096
; Native consumers already use segment:offset pointers to these full buffers.
; Keep this segment outside DGROUP so DS=SS near callers retain their ABI.
SEGMENT FAR_STORAGE public align=16 class=FAR_DATA use16
global erase_shadow_cells,terminal_history_buffer,terminal_far_storage_end
erase_shadow_cells: resb 8192
SEGMENT HISTORY_STORAGE public align=16 class=FAR_DATA use16
terminal_history_buffer: resb 63000
terminal_far_storage_end:
global render_autowrap,terminal_input_mode_8fe8
render_autowrap equ cursor_state_value_1d20
terminal_input_mode_8fe8 equ terminal_dec_keys
SEGMENT STACK stack align=16 class=STACK use16
resb 8192
global terminal_stack_top
terminal_stack_top:

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
global snapshot_video_segment
snapshot_video_segment:
text_video_segment: dw 0xb800
global text_bios_output
text_bios_output: dw 0
global text_cga_status_port
global snapshot_cga_status_port
snapshot_cga_status_port:
text_cga_status_port: dw 0
global scroll_unimplemented_service
scroll_unimplemented_service: dw 0
global render_translation_mask
render_translation_mask: db 255
global render_graphics_map
render_graphics_map:
%assign glyph 0
%rep 128
 db glyph
%assign glyph glyph+1
%endrep
global render_translation_table
render_translation_table:
%assign glyph 0
%rep 256
 db glyph
%assign glyph glyph+1
%endrep
global terminal_c1_enabled
terminal_c1_enabled: dw 0
global terminal_sink_3988_enabled
terminal_sink_3988_enabled: dw 0
global terminal_cr_adds_lf
terminal_cr_adds_lf: dw 0
global terminal_sink_398a_enabled
global _terminal_sink_398a_enabled
_terminal_sink_398a_enabled:
terminal_sink_398a_enabled: dw 0
global terminal_sink_398c_disabled
global _terminal_sink_398c_disabled
_terminal_sink_398c_disabled:
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
terminal_backspace_mode_9058: dw 1
global terminal_backspace_erases
terminal_backspace_erases: db 0
global terminal_newline_mode_9020
terminal_newline_mode_9020: dw 0
global terminal_history_pending,terminal_history_pointer,terminal_history_start,terminal_history_end,terminal_history_wrapped,terminal_history_buffer
terminal_history_start: dw terminal_history_buffer
terminal_history_pointer: dw terminal_history_buffer,seg terminal_history_buffer
terminal_history_end: dw terminal_history_buffer+63000
terminal_history_wrapped: dw 0
terminal_history_pending: db 0

SEGMENT _DATA
global terminal_quit,terminal_exit_code,terminal_irq_vector,terminal_port_number
terminal_quit: dw 0
terminal_exit_code: dw 0
terminal_irq_vector: dw 0x0c
terminal_port_number: dw 1
global terminal_baud_low,terminal_baud_high,terminal_parity,terminal_data_bits,terminal_stop_bits
terminal_baud_low: dw 38400
terminal_baud_high: dw 0
terminal_parity: dw 0
terminal_data_bits: dw 8
terminal_stop_bits: dw 1

; Original SOH/VT/CAN emulation and protocol-detection gates.
global terminal_control_mode_9026,terminal_control_mode_1fb0
terminal_control_mode_9026: dw 0
terminal_control_mode_1fb0: dw 0
