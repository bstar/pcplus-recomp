; Combined source-only protocol/cursor diagnostic. Unrecovered services fail fast.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
GROUP DGROUP _DATA _BSS STACK
extern ansi_escape_entry
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
ansi_control_character:
 mov bx,sp
 mov ax,[bx+2]
 mov [ansi_last_control],ax
 inc word [ansi_control_count]
 ret
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
global ansi_escape_service_12c8
global csi_service_12c8
global screen_wrap_forward
ansi_escape_service_12c8:
csi_service_12c8:
screen_wrap_forward:
 mov ax,0x12c8
 jmp csi_unimplemented
global ansi_escape_service_20a4
global csi_reset_terminal
ansi_escape_service_20a4:
csi_reset_terminal:
 mov ax,0x20a4
 jmp csi_unimplemented
global csi_clear_tabs
csi_clear_tabs:
 mov ax,0x246c
 jmp csi_unimplemented
global csi_reset_scroll_region
csi_reset_scroll_region:
 mov ax,0x250a
 jmp csi_unimplemented
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
 mov ax,0xda46
 jmp csi_unimplemented
global ansi_escape_service_da84
global csi_service_da84
ansi_escape_service_da84:
csi_service_da84:
 mov ax,0xda84
 jmp csi_unimplemented
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
global csi_set_modes
csi_set_modes:
 mov ax,0xde98
 jmp csi_unimplemented
global csi_reset_modes
csi_reset_modes:
 mov ax,0xdf7e
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
%macro selftest_sequence 2
 mov word [ansi_input_pointer],%1
 mov word [ansi_input_length],%2
 call ansi_reset
 call ansi_escape_entry
%endmacro
..start:
 mov ax,DGROUP
 mov ds,ax
 cli
 mov ss,ax
 mov sp,stack_top
 sti
 call ansi_reset
 call ansi_escape_entry
 cmp word [screen_cursor_row],9
 jne .failed
 cmp word [screen_cursor_column],19
 jne .failed
 mov word [ansi_input_pointer],sgr_sample
 mov word [ansi_input_length],sgr_end-sgr_sample
 call ansi_reset
 call ansi_escape_entry
 cmp word [attributes_current],0x8c
 jne .failed
 mov word [ansi_input_pointer],up_sample
 mov word [ansi_input_length],up_end-up_sample
 call ansi_reset
 call ansi_escape_entry
 cmp word [screen_cursor_row],7
 jne .failed
 cmp word [screen_cursor_column],19
 jne .failed
 mov word [ansi_input_pointer],q_sample
 mov word [ansi_input_length],q_end-q_sample
 call ansi_reset
 call ansi_escape_entry
 cmp word [ansi_input_position],4
 jne .failed
 cmp word [csi_unimplemented_service],0
 jne .failed
 ; Parse ESC7/8: full state save/restore, including the actual BIOS cursor.
 selftest_sequence esc_save_sample,1
 selftest_sequence reset_sgr_sample,reset_sgr_end-reset_sgr_sample
 selftest_sequence default_sample,default_end-default_sample
 selftest_sequence esc_restore_sample,1
 cmp word [screen_cursor_row],7
 jne .failed
 cmp word [screen_cursor_column],19
 jne .failed
 cmp word [attributes_current],0x8c
 jne .failed
 mov ah,3
 xor bh,bh
 int 0x10
 cmp dx,0x0713
 jne .failed
 ; Parse CSIs/u: position restores while the newly chosen attribute stays.
 selftest_sequence csi_save_sample,csi_save_end-csi_save_sample
 selftest_sequence reset_sgr_sample,reset_sgr_end-reset_sgr_sample
 selftest_sequence default_sample,default_end-default_sample
 selftest_sequence csi_restore_sample,csi_restore_end-csi_restore_sample
 cmp word [screen_cursor_row],7
 jne .failed
 cmp word [screen_cursor_column],19
 jne .failed
 cmp word [attributes_current],7
 jne .failed
 mov ah,3
 xor bh,bh
 int 0x10
 cmp dx,0x0713
 jne .failed
 ; Exercise real CSI 2J through recovered rectangle code and the DOS BIOS.
 mov ax,3
 int 0x10
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov ax,0x4f41
 mov cx,2000
 cld
 rep stosw
 mov word [ansi_input_pointer],erase_sample
 mov word [ansi_input_length],erase_end-erase_sample
 call ansi_reset
 call ansi_escape_entry
 mov ax,0xb800
 mov es,ax
 xor di,di
 mov ax,0x0720
 mov cx,2000
 repe scasw
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
cursor_state_value_1d20: dw 0
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
global csi_terminal_id
csi_terminal_id:
 dw 4
global csi_report_private_prefix,csi_printer_ready
csi_report_private_prefix: dw 0
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
global erase_lineflags_enabled,erase_protection_mode,erase_cell_count
erase_lineflags_enabled: dw 0
erase_protection_mode: dw 0
erase_cell_count: dw 2000
global erase_attribute_values_base,erase_shadow_offset,erase_shadow_segment
erase_attribute_values_base: dw erase_attribute_values
erase_shadow_offset: dw erase_shadow_cells
erase_shadow_segment: dw seg erase_shadow_cells
erase_sample: db '[2J'
erase_end:
SEGMENT _BSS public align=16 class=BSS use16
global ansi_input_buffer,csi_output_buffer,screen_attribute_cells
ansi_input_buffer: resb 2048
csi_output_buffer: resb 256
screen_attribute_cells: resb 4096
global erase_attribute_values,erase_shadow_cells
erase_attribute_values: resb 4096
erase_shadow_cells: resb 8192
SEGMENT STACK stack align=16 class=STACK use16
resb 4096
stack_top:
