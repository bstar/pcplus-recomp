; Diagnostic-only GET composition; UI/stream/cancel/opaque float boundaries
; are explicit C services. Actual typed readers/copy/flush/integer CRT linked.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_get,aspect_get_numeric_filter
global _owner_call,_owner_numeric_filter,_owner_string_filter
_owner_call: jmp aspect_get
_owner_numeric_filter: mov ax,aspect_get_numeric_filter
 ret
_owner_string_filter: mov ax,aspect_get_string_filter
 ret
global aspect_get_read_width
extern aspect_string_length_operand
aspect_get_read_width: jmp aspect_string_length_operand
global aspect_get_string_destination
extern aspect_string_read_destination
aspect_get_string_destination: jmp aspect_string_read_destination
global aspect_get_integer_destination
extern aspect_expr_integer_address
aspect_get_integer_destination: jmp aspect_expr_integer_address
global aspect_get_long_destination
extern aspect_expr_long_address
aspect_get_long_destination: jmp aspect_expr_long_address
global aspect_get_float_destination
extern aspect_expr_float_address
aspect_get_float_destination: jmp aspect_expr_float_address
global aspect_get_optional
extern aspect_string_option_flag
aspect_get_optional: jmp aspect_string_option_flag
global aspect_get_integer_text
extern aspect_conversion_itoa
aspect_get_integer_text: jmp aspect_conversion_itoa
global aspect_get_long_text
extern aspect_conversion_ltoa
aspect_get_long_text: jmp aspect_conversion_ltoa
global aspect_get_commit_string
extern aspect_string_flush
aspect_get_commit_string: jmp aspect_string_flush
global aspect_get_parse_integer
extern aspect_conversion_atoi
aspect_get_parse_integer: jmp aspect_conversion_atoi
global aspect_get_parse_long
extern aspect_conversion_atol
aspect_get_parse_long: jmp aspect_conversion_atol
global aspect_get_copy
extern erase_move_bytes
aspect_get_copy: jmp erase_move_bytes
global aspect_dispatch_read
extern _owner_read_byte
aspect_dispatch_read: jmp _owner_read_byte
global aspect_flow_read_word
extern _owner_read_word
aspect_flow_read_word: jmp _owner_read_word
global aspect_get_cursor
extern _owner_cursor
aspect_get_cursor: jmp _owner_cursor
global aspect_get_cancel_pending
extern _owner_confirm
aspect_get_cancel_pending: jmp _owner_confirm
global aspect_get_cancel_dispatch
extern _owner_cancel
aspect_get_cancel_dispatch: jmp _owner_cancel
global aspect_get_bell
extern _owner_bell
aspect_get_bell: jmp _owner_bell
global aspect_get_string_filter
aspect_get_string_filter:
 push bp
 mov bp,sp
 mov bx,[bp+4]
 xor ax,ax
 cmp word [bx],13
 jne .done
 mov ax,99
.done: pop bp
 ret
extern _owner_field,_owner_float,_owner_position,_owner_error
%macro adapter 3
 global %1
 %1:
 push bp
 mov bp,sp
 %assign offset %3*2+2
 %rep %3
 push word [bp+offset]
 %assign offset offset-2
 %endrep
 call %2
 add sp,%3*2
 pop bp
 ret %3*2
%endmacro
adapter aspect_get_field,_owner_field,7
adapter aspect_get_parse_float,_owner_float,1
adapter aspect_string_error,_owner_error,1
; Position is an unusual register ABI: AX=row,DX=column.
global aspect_get_set_cursor
aspect_get_set_cursor:
 push dx
 push ax
 call _owner_position
 add sp,4
 ret
extern _owner_unexpected
global aspect_get_read_position
aspect_get_read_position: jmp _owner_unexpected
global aspect_get_read_attribute
aspect_get_read_attribute: jmp _owner_unexpected
global aspect_get_float_text
aspect_get_float_text: jmp _owner_unexpected
global aspect_operand_invalid
aspect_operand_invalid: jmp _owner_unexpected
global aspect_operand_builtin_integer
aspect_operand_builtin_integer: jmp _owner_unexpected
global aspect_operand_builtin_long
aspect_operand_builtin_long: jmp _owner_unexpected
global aspect_string_builtin
aspect_string_builtin: jmp _owner_unexpected
global aspect_flow_read_dword
aspect_flow_read_dword: jmp _owner_unexpected
global aspect_flow_refill
aspect_flow_refill: jmp _owner_unexpected
global aspect_expr_read_float
aspect_expr_read_float: jmp _owner_unexpected
global aspect_flow_seek
aspect_flow_seek: jmp _owner_unexpected
global aspect_flow_fread
aspect_flow_fread: jmp _owner_unexpected
SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global aspect_get_destination_kind
aspect_get_destination_kind:
global aspect_operand_lookahead
aspect_operand_lookahead:
global _owner_lookahead
_owner_lookahead: dw 0
global aspect_get_scratch
aspect_get_scratch:
global _owner_scratch_pointer
_owner_scratch_pointer: dw 0
global aspect_get_row
aspect_get_row:
global _owner_row
_owner_row: dw 0
global aspect_get_column
aspect_get_column:
global _owner_column
_owner_column: dw 0
global aspect_get_attribute
aspect_get_attribute:
global _owner_attribute
_owner_attribute: dw 0
global aspect_get_wrap
aspect_get_wrap:
global _owner_wrap
_owner_wrap: dw 0
global aspect_get_rows
aspect_get_rows:
global _owner_rows
_owner_rows: dw 0
global aspect_get_columns
aspect_get_columns:
global _owner_columns
_owner_columns: dw 0
global aspect_get_cursor_origin
aspect_get_cursor_origin:
global _owner_origin
_owner_origin: dw 0
global aspect_get_failure
aspect_get_failure:
global _owner_failure
_owner_failure: dw 0
global aspect_get_keys_disabled
aspect_get_keys_disabled:
global _owner_keys_disabled
_owner_keys_disabled: dw 0
global aspect_get_float_text_pointer
aspect_get_float_text_pointer:
global _owner_float_pointer
_owner_float_pointer: dw 0
global aspect_get_float_result
aspect_get_float_result:
global _owner_float_result
_owner_float_result: times 8 db 0
global aspect_flow_stream
aspect_flow_stream:
global _owner_file
_owner_file: dw 0
global aspect_flow_frame
aspect_flow_frame:
global _owner_frame
_owner_frame: dw 0
global aspect_operand_integer_bank_a
aspect_operand_integer_bank_a:
global _owner_integer_a
_owner_integer_a: times 10 dw 0
global aspect_operand_integer_bank_b
aspect_operand_integer_bank_b:
global _owner_integer_b
_owner_integer_b: times 128 dw 0
global aspect_operand_long_bank
aspect_operand_long_bank:
global _owner_longs
_owner_longs: times 128 dd 0
global aspect_expr_float_bank
aspect_expr_float_bank:
global _owner_floats
_owner_floats: times 1024 db 0
global aspect_operand_system_values
aspect_operand_system_values:
global _owner_system
_owner_system: times 2048 db 0
global aspect_string_bank_a
aspect_string_bank_a:
global _owner_strings
_owner_strings: times 810 db 0
global aspect_globals_table
aspect_globals_table:
global _owner_globals
_owner_globals: times 128 dd 0
global aspect_string_pending_far
aspect_string_pending_far:
global _owner_pending_far
_owner_pending_far: dd 0
global aspect_string_pending_near
aspect_string_pending_near:
global _owner_pending_near
_owner_pending_near: dw 0
global aspect_string_scratch
aspect_string_scratch:
global _owner_string_scratch
_owner_string_scratch: times 891 db 0
global aspect_string_scratch_pointer
aspect_string_scratch_pointer:
global _owner_string_pointer
_owner_string_pointer: dw 0
global aspect_string_scratch_index
aspect_string_scratch_index:
global _owner_string_index
_owner_string_index: dw 0
global aspect_string_check_range
aspect_string_check_range:
global _owner_check_range
_owner_check_range: dw 0
global aspect_dispatch_exit_state
aspect_dispatch_exit_state:
global _owner_exit_state
_owner_exit_state: dw 0
global aspect_string_transform
aspect_string_transform:
global _owner_transform
_owner_transform: times 13 db 0
global aspect_expr_stage_index
aspect_expr_stage_index:
global _owner_stage_index
_owner_stage_index: dw 0
global aspect_expr_stage_types
aspect_expr_stage_types:
global _owner_stage_types
_owner_stage_types: times 10 db 0
global aspect_ops_float_value
aspect_ops_float_value:
global _owner_stage_values
_owner_stage_values: times 80 db 0
global aspect_expr_float_zero
aspect_expr_float_zero:
global _owner_float_zero
_owner_float_zero: times 8 db 0
