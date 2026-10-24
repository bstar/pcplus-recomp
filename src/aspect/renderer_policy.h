#ifndef PCPLUS_ASPECT_RENDERER_POLICY_H
#define PCPLUS_ASPECT_RENDERER_POLICY_H
/* Pure parent admission/preflight. Near cdecl DS=SS; returns0 or unsupported3.
 * No IO, close, DOS/BIOS call, scheduler, mutation, MCB or capability validation.
 * Compile -ms -0 -nt=ASPECT_CODE. Imports are the existing parent's symbols.
 */
unsigned __cdecl aspect_render_admit(void);
unsigned __cdecl aspect_render_preflight_modes(unsigned setting);
unsigned __cdecl aspect_render_preflight_command(void);
unsigned __cdecl aspect_render_preflight_control(unsigned character);
#define ASPECT_RENDER_WORDS(X) \
 X(terminal_program_active) X(terminal_program_kind) X(terminal_program_pending) \
 X(terminal_aspect_active) X(terminal_parser_active) X(terminal_ansi_wait_active) X(terminal_monitor_active) \
 X(terminal_snapshot_active) X(terminal_screen_print_active) X(terminal_controller_active) \
 X(terminal_macro_active) X(terminal_transfer_active) X(terminal_transfer_pending) \
 X(connection_state) X(reset_ready) X(csi_terminal_id) \
 X(terminal_sink_3988_enabled) X(terminal_sink_398a_enabled) X(terminal_sink_398c_disabled) \
 X(terminal_printer_count) X(terminal_printer_closing) X(csi_printer_ready) \
 X(screen_columns) X(screen_video_row_bytes) X(screen_attribute_row_bytes) \
 X(csi_last_column) X(csi_column_count) X(csi_last_row) X(csi_row_count) \
 X(screen_cursor_row) X(screen_cursor_column) X(screen_video_offset) X(screen_attribute_offset) \
 X(screen_first_row) X(screen_last_row) X(csi_origin_row) X(csi_origin_bottom) \
 X(screen_viewport_active) X(screen_viewport_enabled) X(screen_viewport_offset) \
 X(screen_attribute_checks) X(terminal_mode_372c) X(render_translation_enabled) \
 X(erase_protection_mode) X(erase_cell_count) X(text_video_segment) X(text_cga_status_port) \
 X(screen_attributes_base) X(erase_attribute_values_base) X(erase_shadow_offset) X(erase_shadow_segment) \
 X(terminal_history_start) X(terminal_history_end) X(terminal_history_wrapped) \
 X(ansi_parameter_count) X(ansi_private) X(csi_report_private_prefix) \
 X(terminal_tab_wrap) X(terminal_control_mode_9026) X(terminal_control_mode_1fb0) \
 X(terminal_dec_keys) X(terminal_newline_mode_9020) X(terminal_ansi_m_policy)
#define ASPECT_RENDER_DISPLAY_WORDS(X) \
 X(screen_visible_column) X(screen_viewport_left) X(screen_viewport_right) \
 X(screen_cursor_wrap) X(screen_vertical_attribute_check) X(screen_reverse_wrap_blocked) \
 X(ui_flow_suppressed) X(ui_flow_region_cells) X(ui_flow_video_base) X(ui_flow_coordinate_base) \
 X(attributes_color_mode) X(ansi_command) X(render_translation_base) X(render_direct_output)
#define AR_WORD(name) extern unsigned name;
ASPECT_RENDER_WORDS(AR_WORD)
ASPECT_RENDER_DISPLAY_WORDS(AR_WORD)
#undef AR_WORD
extern unsigned redisplay_active,command_menu_active;
extern unsigned char terminal_history_pending,render_translation_mask;
extern unsigned char render_translation_table[256];
extern unsigned terminal_history_pointer[2],ansi_parameters[16];
extern unsigned char screen_attribute_cells[4096],erase_attribute_values[4096];
extern unsigned char terminal_keymap[948],screen_line_flags[128];
extern unsigned char __far erase_shadow_cells[8192];
extern unsigned char __far terminal_history_buffer[63000];
#ifdef __WATCOMC__
#pragma aux render_translation_base "render_translation_base";
#pragma aux render_direct_output "render_direct_output";
#pragma aux render_translation_mask "render_translation_mask";
#pragma aux render_translation_table "render_translation_table";
#pragma aux screen_visible_column "screen_visible_column";
#pragma aux screen_viewport_left "screen_viewport_left";
#pragma aux screen_viewport_right "screen_viewport_right";
#pragma aux screen_cursor_wrap "screen_cursor_wrap";
#pragma aux screen_vertical_attribute_check "screen_vertical_attribute_check";
#pragma aux screen_reverse_wrap_blocked "screen_reverse_wrap_blocked";
#pragma aux ui_flow_suppressed "ui_flow_suppressed";
#pragma aux ui_flow_region_cells "ui_flow_region_cells";
#pragma aux ui_flow_video_base "ui_flow_video_base";
#pragma aux ui_flow_coordinate_base "ui_flow_coordinate_base";
#pragma aux attributes_color_mode "attributes_color_mode";
#pragma aux ansi_command "ansi_command";
#pragma aux terminal_program_active "terminal_program_active";
#pragma aux terminal_program_kind "terminal_program_kind";
#pragma aux terminal_program_pending "terminal_program_pending";
#pragma aux terminal_aspect_active "terminal_aspect_active";
#pragma aux terminal_parser_active "terminal_parser_active";
#pragma aux terminal_ansi_wait_active "terminal_ansi_wait_active";
#pragma aux terminal_monitor_active "terminal_monitor_active";
#pragma aux terminal_snapshot_active "terminal_snapshot_active";
#pragma aux terminal_screen_print_active "terminal_screen_print_active";
#pragma aux terminal_controller_active "terminal_controller_active";
#pragma aux terminal_macro_active "terminal_macro_active";
#pragma aux terminal_transfer_active "terminal_transfer_active";
#pragma aux terminal_transfer_pending "terminal_transfer_pending";
#pragma aux connection_state "connection_state";
#pragma aux reset_ready "reset_ready";
#pragma aux csi_terminal_id "csi_terminal_id";
#pragma aux terminal_sink_3988_enabled "terminal_sink_3988_enabled";
#pragma aux terminal_sink_398a_enabled "terminal_sink_398a_enabled";
#pragma aux terminal_sink_398c_disabled "terminal_sink_398c_disabled";
#pragma aux terminal_printer_count "terminal_printer_count";
#pragma aux terminal_printer_closing "terminal_printer_closing";
#pragma aux csi_printer_ready "csi_printer_ready";
#pragma aux screen_columns "screen_columns";
#pragma aux screen_video_row_bytes "screen_video_row_bytes";
#pragma aux screen_attribute_row_bytes "screen_attribute_row_bytes";
#pragma aux csi_last_column "csi_last_column";
#pragma aux csi_column_count "csi_column_count";
#pragma aux csi_last_row "csi_last_row";
#pragma aux csi_row_count "csi_row_count";
#pragma aux screen_cursor_row "screen_cursor_row";
#pragma aux screen_cursor_column "screen_cursor_column";
#pragma aux screen_video_offset "screen_video_offset";
#pragma aux screen_attribute_offset "screen_attribute_offset";
#pragma aux screen_first_row "screen_first_row";
#pragma aux screen_last_row "screen_last_row";
#pragma aux csi_origin_row "csi_origin_row";
#pragma aux csi_origin_bottom "csi_origin_bottom";
#pragma aux screen_viewport_active "screen_viewport_active";
#pragma aux screen_viewport_enabled "screen_viewport_enabled";
#pragma aux screen_viewport_offset "screen_viewport_offset";
#pragma aux screen_attribute_checks "screen_attribute_checks";
#pragma aux terminal_mode_372c "terminal_mode_372c";
#pragma aux render_translation_enabled "render_translation_enabled";
#pragma aux erase_protection_mode "erase_protection_mode";
#pragma aux erase_cell_count "erase_cell_count";
#pragma aux text_video_segment "text_video_segment";
#pragma aux text_cga_status_port "text_cga_status_port";
#pragma aux screen_attributes_base "screen_attributes_base";
#pragma aux erase_attribute_values_base "erase_attribute_values_base";
#pragma aux erase_shadow_offset "erase_shadow_offset";
#pragma aux erase_shadow_segment "erase_shadow_segment";
#pragma aux terminal_history_start "terminal_history_start";
#pragma aux terminal_history_end "terminal_history_end";
#pragma aux terminal_history_wrapped "terminal_history_wrapped";
#pragma aux ansi_parameter_count "ansi_parameter_count";
#pragma aux ansi_private "ansi_private";
#pragma aux csi_report_private_prefix "csi_report_private_prefix";
#pragma aux terminal_tab_wrap "terminal_tab_wrap";
#pragma aux terminal_control_mode_9026 "terminal_control_mode_9026";
#pragma aux terminal_control_mode_1fb0 "terminal_control_mode_1fb0";
#pragma aux terminal_dec_keys "terminal_dec_keys";
#pragma aux terminal_newline_mode_9020 "terminal_newline_mode_9020";
#pragma aux terminal_ansi_m_policy "terminal_ansi_m_policy";
#pragma aux terminal_history_pending "terminal_history_pending";
#pragma aux terminal_history_pointer "terminal_history_pointer";
#pragma aux ansi_parameters "ansi_parameters";
#pragma aux screen_attribute_cells "screen_attribute_cells";
#pragma aux erase_attribute_values "erase_attribute_values";
#pragma aux terminal_keymap "terminal_keymap";
#pragma aux screen_line_flags "screen_line_flags";
#pragma aux erase_shadow_cells "erase_shadow_cells";
#pragma aux terminal_history_buffer "terminal_history_buffer";
#endif
#endif
