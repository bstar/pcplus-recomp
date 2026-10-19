; Maintained experimental owner bridges for recovered ASPECT instructions.
; Near DS=SS. Actual DOS files/far heap; unsupported commands/services abort.
; This table is deliberately incomplete and never treats an unknown slot as NOP.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_dispatch,aspect_abort,session_setjmp
extern aspect_globals_initialize,aspect_globals_release
extern aspect_flow_gate_decrement,aspect_flow_gate_increment,aspect_flow_seek
extern aspect_flow_call_operand,aspect_flow_call_framed,aspect_flow_return,aspect_flow_return_framed
extern aspect_flow_call,aspect_flow_push_frame
extern aspect_flow_jump,aspect_flow_reserve_locals
extern aspect_expr_branch_false,aspect_expr_branch_true,aspect_expr_branch_false_alias
extern aspect_ops_logical_and,aspect_ops_logical_not,aspect_ops_logical_or
extern aspect_ops_equal,aspect_ops_less_equal,aspect_ops_less,aspect_ops_greater_equal,aspect_ops_greater,aspect_ops_not_equal
extern aspect_ops_decrement,aspect_ops_increment,aspect_ops_assign,aspect_ops_assign_chained
extern aspect_arith_add,aspect_arith_bit_and,aspect_arith_bit_not,aspect_arith_divide
extern aspect_arith_modulo,aspect_arith_multiply,aspect_arith_negate,aspect_arith_bit_or
extern aspect_arith_shift_left,aspect_arith_shift_right,aspect_arith_subtract,aspect_arith_bit_xor
extern aspect_parameter_push_numeric,aspect_parameter_push_string
extern aspect_string_assign
extern aspect_strcmd_compare_bytes,aspect_strcmd_concat,aspect_strcmd_compare,aspect_strcmd_length
extern aspect_strcmd_lower,aspect_strcmd_get_char,aspect_strcmd_set_char,aspect_strcmd_fill
extern aspect_strcmd_subcopy,aspect_strcmd_upper,aspect_strcmd_substr
extern program_strlen,program_strncmp,directory_dial_append_original,directory_dial_upper_original
extern aspect_string_status,aspect_string_success
extern aspect_convert_atoi,aspect_convert_atol,aspect_convert_itoa,aspect_convert_ltoa
extern aspect_console_message,aspect_console_exit,aspect_console_pause,aspect_console_native_wait_second
extern _runtime_console_emit_byte,_runtime_console_cancel_poll
extern aspect_serial_transmit,aspect_serial_wait_for,aspect_serial_wait_status,aspect_serial_native_clock
extern aspect_receive_comgetc,aspect_receive_comgetcd,aspect_receive_rget,aspect_receive_wait_quiet
extern aspect_receive_native_seconds,aspect_receive_available_status,aspect_receive_forever
extern _runtime_receive_character,_runtime_receive_raw_character,_runtime_receive_begin
extern _runtime_serial_read_raw
extern aspect_receive_policy_read
extern aspect_when_register,aspect_when_cancel,aspect_when_monitor,aspect_when_service
extern _runtime_when_poll,_runtime_when_cancel_poll,_runtime_when_idle_allowed
extern _runtime_when_host_poll,_runtime_serial_carrier
extern _runtime_set_status_refresh,_runtime_break_command
extern aspect_break_command,aspect_break_setting,aspect_fetch_command
extern aspect_console_pause_operand
extern aspect_set_dispatch,aspect_set_display,aspect_set_duplex,aspect_set_findcase
extern aspect_set_keys,aspect_set_msg_crlf,aspect_set_rxdata,aspect_set_switchcase
extern aspect_set_waitcase,aspect_set_whencase,aspect_set_pausechar,aspect_set_txpace
extern aspect_string_store_integer
extern aspect_find_command,aspect_case_switch,aspect_case_compare
extern program_strcpy,program_strcmpi
extern _runtime_find_alloc,_runtime_find_free
extern aspect_expr_integer_address
extern _runtime_when_key_ready,_runtime_when_read_key,_runtime_when_confirm_abort
extern _runtime_when_abort,_runtime_when_dispatch_key
extern _runtime_when_monitor_begin,_runtime_when_monitor_end
%ifndef ASPECT_RUNTIME_SERIAL
extern _runtime_receive_seconds
%endif
extern _runtime_serial_ready,_runtime_serial_send,_runtime_serial_receive,_runtime_serial_character_delay
extern _runtime_serial_pause
extern _runtime_serial_wait_second
extern _runtime_error
%ifndef ASPECT_RUNTIME_SERIAL
extern _runtime_serial_clock
%endif
extern _runtime_file,_runtime_reset_native,_runtime_open,_runtime_alloc,_runtime_free
extern _runtime_cleanup,_runtime_close,_runtime_finish,_runtime_service,_runtime_read
extern _runtime_native_error,_runtime_set_error,_runtime_header
extern _aspect_file_refill,_aspect_file_read,_aspect_file_seek,_aspect_file_tell

; Maintained INT0 owner: rewrite the interrupt return, then IRET restores FLAGS.
; No C/DOS call or DS access occurs on the interrupt frame. Parent owns vector.
global _runtime_divide_interrupt
_runtime_divide_interrupt:
 push bp
 mov bp,sp
 mov word [ss:bp+2],runtime_divide_trap
 mov ax,cs
 mov word [ss:bp+4],ax
 pop bp
 iret
runtime_divide_trap:
 mov ax,12
 jmp fail

global _runtime_enter
_runtime_enter:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov [saved_sp],sp
 mov si,0x1234
 mov di,0x5678
 push word [bp+4]
 mov ax,1
 push ax
 call aspect_dispatch
 cmp sp,[saved_sp]
 jne .bad
 cmp si,0x1234
 jne .bad
 cmp di,0x5678
 jne .bad
 mov ax,ss
 mov dx,ds
 cmp ax,dx
 je .done
.bad:
 inc word [_runtime_abi_bad]
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

global _runtime_globals_init,_runtime_globals_release
_runtime_globals_init: jmp aspect_globals_initialize
_runtime_globals_release: jmp aspect_globals_release

global aspect_dispatch_initialize,aspect_dispatch_probe,aspect_dispatch_open
aspect_dispatch_initialize: jmp _runtime_reset_native
aspect_dispatch_probe: jmp session_setjmp
aspect_dispatch_open:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call _runtime_open
 add sp,byte 4
 pop bp
 ret 4

global aspect_dispatch_service,aspect_dispatch_read
aspect_dispatch_service:
 call _runtime_service
 or ax,ax
 jz .done
 call aspect_abort
.done: ret
aspect_dispatch_read:
 call _runtime_read
 cmp ax,0xffff
 jne .done
 call aspect_abort
.done: ret

global aspect_dispatch_seek,aspect_flow_fseek
aspect_dispatch_seek:
aspect_flow_fseek:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call _aspect_file_seek
 add sp,byte 8
 or ax,ax
 jz .done
 mov ax,5
 jmp fail
.done:
 pop bp
 ret

global aspect_flow_ftell
aspect_flow_ftell:
 push bp
 mov bp,sp
 push word [bp+4]
 call _aspect_file_tell
 pop bx
 cmp dx,0xffff
 jne .done
 cmp ax,0xffff
 jne .done
 mov ax,5
 jmp fail
.done:
 pop bp
 ret

global aspect_flow_fread
aspect_flow_fread:
 push bp
 mov bp,sp
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call _aspect_file_read
 add sp,byte 8
 cmp ax,[bp+8]
 je .done
 mov ax,5
 jmp fail
.done:
 pop bp
 ret

global aspect_flow_refill
aspect_flow_refill:
 push bp
 mov bp,sp
 push word [bp+4]
 call _aspect_file_refill
 pop bx
 cmp ax,0xffff
 jne .done
 mov ax,5
 jmp fail
.done:
 pop bp
 ret

global aspect_globals_read,aspect_globals_alloc,aspect_globals_free
aspect_globals_read: mov ax,[_runtime_header]
 ret
aspect_globals_alloc: jmp _runtime_alloc
aspect_globals_free: jmp _runtime_free

global aspect_dispatch_cleanup,aspect_dispatch_close,aspect_dispatch_finish
aspect_dispatch_cleanup: jmp _runtime_cleanup
aspect_dispatch_close: jmp _runtime_close
aspect_dispatch_finish: jmp _runtime_finish

global aspect_dispatch_error,aspect_flow_error,aspect_stack_error,aspect_globals_error,aspect_arith_error,aspect_string_error
aspect_dispatch_error:
aspect_flow_error:
aspect_stack_error:
aspect_globals_error:
aspect_arith_error:
aspect_string_error:
 push bp
 mov bp,sp
 push word [bp+4]
 call _runtime_native_error
 pop bx
 call aspect_abort
 ; Deliberately unreachable; native errors never resume unchecked operations.
 pop bp
 ret 2

global aspect_flow_exit
aspect_flow_exit:
 mov word [aspect_dispatch_exit_state],1
 ret

global aspect_dispatch_invalid_command,aspect_operand_invalid
aspect_dispatch_invalid_command:
 mov ax,3
 jmp fail
aspect_operand_invalid:
 mov ax,7
 jmp fail
unsupported:
 mov ax,3
 jmp fail

global aspect_ops_float_transform,aspect_ops_float_operand,aspect_ops_float_destination,aspect_ops_float_compare
 global aspect_expr_read_float
aspect_ops_float_transform:
aspect_ops_float_operand:
aspect_ops_float_destination:
aspect_ops_float_compare:
aspect_expr_read_float:
 mov ax,4
 jmp fail

extern aspect_directory_builtin_entry,aspect_directory_builtin_ldate
extern aspect_directory_builtin_kbdfile,aspect_directory_builtin_metakey
extern aspect_directory_builtin_name,aspect_directory_builtin_note
extern aspect_directory_builtin_phone,aspect_directory_builtin_pword,aspect_directory_builtin_script
; Native directory pointer getters, with an immutable owned selected record.
; Other string builtin services remain explicit unsupported actions.
global aspect_string_builtin
aspect_string_builtin:
 push bp
 mov bp,sp
 cmp word [bp+4],7
 ja .other
 push bx
 mov bx,[bp+4]
 shl bx,1
 call [cs:directory_string_getters+bx]
 pop bx
 pop bp
 ret 2
.other:
 cmp word [bp+4],19
 jne unsupported
 mov ax,empty_script
 pop bp
 ret 2
directory_string_getters:
 dw aspect_directory_builtin_ldate,aspect_directory_builtin_kbdfile
 dw aspect_directory_builtin_metakey,aspect_directory_builtin_name
 dw aspect_directory_builtin_note,aspect_directory_builtin_phone
 dw aspect_directory_builtin_pword,aspect_directory_builtin_script

; Maintained routing to recovered compare-status services only.
global aspect_operand_builtin_integer,aspect_operand_builtin_long
aspect_operand_builtin_integer:
 push bp
 mov bp,sp
 cmp word [bp+4],3
 je .directory
 cmp word [bp+4],20
 je .comdata
 cmp word [bp+4],22
 je .forever
 cmp word [bp+4],23
 je .found
 cmp word [bp+4],21
 je .status
 cmp word [bp+4],28
 je .wait_status
 cmp word [bp+4],27
 jne unsupported
 call aspect_string_success
 jmp short .done
.comdata:
 call aspect_receive_available_status
 jmp short .done
.found:
 mov ax,[aspect_find_found]
 jmp short .done
.directory:
 call aspect_directory_builtin_entry
 jmp short .done
.forever:
 call aspect_receive_forever
 jmp short .done
.status:
 call aspect_string_status
 jmp short .done
.wait_status:
 call aspect_serial_wait_status
.done:
 pop bp
 ret 2
aspect_operand_builtin_long:
 mov ax,3
 jmp fail

global aspect_dispatch_wait,aspect_dispatch_shutdown
 global aspect_abort_tell,aspect_abort_format,aspect_abort_print
aspect_dispatch_wait: jmp aspect_serial_receive
aspect_dispatch_shutdown:
aspect_abort_tell:
aspect_abort_format:
aspect_abort_print:
 mov ax,10
fail:
 push ax
 call _runtime_set_error
 pop bx
 call aspect_abort
 ret

; Reuse existing recovered CRT code rather than another implementation.
global aspect_string_strlen,aspect_string_strncmp,aspect_string_concat,aspect_string_upper
aspect_string_strlen: jmp program_strlen
aspect_string_strncmp: jmp program_strncmp
aspect_string_concat: jmp directory_dial_append_original
aspect_string_upper: jmp directory_dial_upper_original
global aspect_find_upper,aspect_expr_integer_destination,aspect_find_alloc,aspect_find_free
aspect_find_upper: jmp directory_dial_upper_original
aspect_expr_integer_destination: jmp aspect_expr_integer_address
aspect_find_alloc:
 push bp
 mov bp,sp
 push word [bp+4]
 call _runtime_find_alloc
 add sp,2
 pop bp
 or ax,ax
 jnz .done
 mov ax,[_runtime_error]
 jmp fail
.done: ret
aspect_find_free:
 push bp
 mov bp,sp
 push word [bp+4]
 call _runtime_find_free
 add sp,2
 pop bp
 cmp word [_runtime_error],0
 je .done
 mov ax,[_runtime_error]
 jmp fail
.done: ret
global aspect_console_emit_byte,aspect_console_cancel_poll,aspect_console_wait_second
aspect_console_emit_byte: jmp _runtime_console_emit_byte
aspect_console_cancel_poll: jmp _runtime_when_cancel_poll
aspect_console_wait_second:
 call _runtime_serial_ready
 or ax,ax
 jz .native
 call _runtime_serial_wait_second
 or ax,ax
 jnz fail
 ret
.native:
 jmp aspect_console_native_wait_second

; Maintained platform admission and bounded UART adapters. Missing serial
; attachment is explicit unsupported; native matcher/formatting remains intact.
runtime_serial_transmit:
 call _runtime_serial_ready
 or ax,ax
 jz unsupported
 jmp aspect_serial_transmit
runtime_serial_wait_for:
 call _runtime_serial_ready
 or ax,ax
 jz unsupported
 jmp aspect_serial_wait_for
global aspect_serial_send_byte,aspect_serial_receive,aspect_serial_character_delay
%macro serial_argument_adapter 2
%1:
 push bp
 mov bp,sp
 push word [bp+4]
 call %2
 add sp,2
 pop bp
 cmp word [_runtime_error],0
 je %%done
 mov ax,[_runtime_error]
 jmp fail
%%done:
 ret 2
%endmacro
serial_argument_adapter aspect_serial_send_byte,_runtime_serial_send
serial_argument_adapter aspect_serial_receive,_runtime_serial_receive
serial_argument_adapter aspect_serial_character_delay,_runtime_serial_character_delay
global aspect_serial_clock,aspect_serial_pause_ticks
%ifdef ASPECT_RUNTIME_SERIAL
aspect_serial_clock: jmp aspect_serial_native_clock
serial_argument_adapter aspect_serial_pause_ticks,_runtime_serial_pause
%else
aspect_serial_clock: jmp _runtime_serial_clock
serial_argument_adapter aspect_serial_pause_ticks,_runtime_serial_pause
%endif

; Receive handlers retain their original algorithms. The explicit raw device
; adapter owns cooperative polling and cancellation, not terminal scheduling.
runtime_receive_comgetc:
 call _runtime_serial_ready
 or ax,ax
 jz unsupported
 jmp aspect_receive_comgetc
runtime_receive_comgetcd:
 call _runtime_serial_ready
 or ax,ax
 jz unsupported
 jmp aspect_receive_comgetcd
runtime_receive_wait_quiet:
 call _runtime_serial_ready
 or ax,ax
 jz unsupported
 jmp aspect_receive_wait_quiet
runtime_receive_rget:
 call _runtime_serial_ready
 or ax,ax
 jz unsupported
 mov ax,1
 push ax
 call _runtime_receive_begin
 add sp,2
 call aspect_receive_rget
 xor ax,ax
 push ax
 call _runtime_receive_begin
 add sp,2
 ret
global aspect_receive_seconds,aspect_receive_character,aspect_receive_raw_read
%ifdef ASPECT_RUNTIME_SERIAL
aspect_receive_seconds: jmp aspect_receive_native_seconds
%else
aspect_receive_seconds: jmp _runtime_receive_seconds
%endif
aspect_receive_raw_read:
 call _runtime_serial_read_raw
 cmp word [_runtime_error],0
 je .done
 mov ax,[_runtime_error]
 jmp fail
.done: ret
aspect_receive_character:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call _runtime_receive_character
 add sp,4
 pop bp
 cmp word [_runtime_error],0
 je .done
 mov ax,[_runtime_error]
 jmp fail
.done: ret 4

; Retain native4C74's mapping/call order. Direct script reads select display0
; until the full terminal renderer is connected; COMGETC uses native selector.
global _runtime_receive_policy_byte
_runtime_receive_policy_byte:
 push bp
 mov bp,sp
 push word [bp+6]
 push word [bp+4]
 call aspect_receive_policy_read
 pop bp
 ret
global aspect_receive_policy_raw,aspect_receive_policy_delayed
aspect_receive_policy_raw:
 xor ax,ax
 jmp receive_policy_raw_common
aspect_receive_policy_delayed:
 mov ax,1
receive_policy_raw_common:
 push ax
 call _runtime_receive_raw_character
 add sp,2
 cmp word [_runtime_error],0
 je .done
 mov ax,[_runtime_error]
 jmp fail
.done: ret
; Native WHEN sees only the once-translated lead, before rendered output.
; Its action executes native flow/FILE/frame code; no synchronous handler shim.
global aspect_receive_policy_pattern_byte,aspect_receive_policy_emit_byte
aspect_receive_policy_pattern_byte:
 push bp
 mov bp,sp
 call _runtime_when_monitor_begin
 cmp word [_runtime_error],0
 jne .failed
 push word [bp+4]
 call aspect_when_monitor
 call _runtime_when_monitor_end
 cmp word [_runtime_error],0
 je .done
.failed:
 pop bp
 mov ax,[_runtime_error]
 jmp fail
.done:
 pop bp
 ret 2
extern _runtime_receive_render_byte
aspect_receive_policy_emit_byte:
 push bp
 mov bp,sp
 push word [bp+4]
 call _runtime_receive_render_byte
 add sp,2
 pop bp
 cmp word [_runtime_error],0
 je .done
 mov ax,[_runtime_error]
 jmp fail
.done: ret

; Native service callbacks. Platform poll never calls the service recursively.
global _runtime_when_native_service,aspect_when_host_poll,aspect_when_carrier
 global aspect_when_key_ready,aspect_when_read_key,aspect_when_confirm_abort
 global aspect_when_abort,aspect_when_dispatch_key
global aspect_dispatch_idle_allowed
aspect_dispatch_idle_allowed: jmp _runtime_when_idle_allowed
_runtime_when_native_service: jmp aspect_when_service
aspect_when_host_poll: jmp _runtime_when_host_poll
aspect_when_carrier: jmp _runtime_serial_carrier
aspect_when_key_ready: jmp _runtime_when_key_ready
aspect_when_read_key: jmp _runtime_when_read_key
aspect_when_confirm_abort: jmp _runtime_when_confirm_abort
aspect_when_abort: jmp _runtime_when_abort
aspect_when_dispatch_key:
 push ax
 call _runtime_when_dispatch_key
 pop bx
 ret
runtime_when_register:
 call _runtime_serial_ready
 or ax,ax
 jz unsupported
 jmp aspect_when_register
; Native5458 reads its selector through the checked FILE adapter, calls this
; complete owned256-entry table and tail-calls native status. Boolean values
; remain raw bytes as in E6BB, rather than the earlier WHENCASE-only0/1 policy.
global aspect_set_status_refresh,aspect_set_query_integer
aspect_set_status_refresh:
 call _runtime_set_status_refresh
 or ax,ax
 jnz fail
 ret
aspect_set_query_integer: jmp aspect_string_store_integer
global aspect_break_native,aspect_break_status_refresh,aspect_break_operand,aspect_break_store_integer
aspect_break_status_refresh: jmp aspect_set_status_refresh
aspect_break_operand: jmp aspect_console_pause_operand
aspect_break_store_integer: jmp aspect_string_store_integer
aspect_break_native:
 call _runtime_break_command
 or ax,ax
 jnz fail
 ret
runtime_set_duplex:
 call aspect_set_duplex
 cmp word [aspect_set_query_mode],0
 jne .done
 mov word [_runtime_set_duplex_changed],1
.done:
 ret

SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
global aspect_directory_record,_runtime_directory_record
aspect_directory_record:
_runtime_directory_record: times 114 db 0
global aspect_directory_entry,_runtime_directory_entry
aspect_directory_entry:
_runtime_directory_entry: dw 0
; Maintained scanner data: only native ctype bit04 (decimal digit) is read.
; Other flags from the original CRT table are outside this owner's contract.
global aspect_convert_candidate_chars,aspect_convert_ctype
aspect_convert_candidate_chars: db '-.0123456789',0
aspect_convert_ctype:
%assign convert_char 0
%rep 256
%if convert_char >= '0' && convert_char <= '9'
 db 4
%else
 db 0
%endif
%assign convert_char convert_char+1
%endrep
%macro scalar 2
 global %1,%2
%1:
%2: dw 0
%endmacro
global aspect_receive_clock_sample
aspect_receive_clock_sample: times 4 dw 0
global aspect_receive_policy_table,_runtime_receive_translation_table
aspect_receive_policy_table:
_runtime_receive_translation_table: times 256 db 0
global aspect_when_active_count
aspect_when_active_count:
scalar aspect_receive_policy_pattern_count,_runtime_receive_pattern_count
 global aspect_when_records,_runtime_when_records
aspect_when_records:
_runtime_when_records: times 344 db 0
scalar aspect_when_disconnect_armed,_runtime_when_disconnect_armed
scalar aspect_when_case_sensitive,_runtime_when_case_sensitive
scalar aspect_when_keyboard_disabled,_runtime_when_keyboard_disabled
scalar aspect_when_last_key,_runtime_when_last_key
scalar aspect_when_pending_key,_runtime_when_pending_key
global aspect_receive_policy_display
aspect_receive_policy_display:
scalar aspect_receive_display,_runtime_receive_display
scalar aspect_console_message_mode,_runtime_console_message_mode
scalar aspect_serial_case_sensitive,_runtime_serial_case_sensitive
scalar aspect_serial_wait_result,_runtime_serial_wait_result
scalar aspect_serial_pause_character,_runtime_serial_pause_character
scalar aspect_serial_local_echo,_runtime_serial_local_echo
scalar aspect_serial_character_delay_value,_runtime_serial_character_delay_value
scalar aspect_break_delay_units,_runtime_serial_break_units
global aspect_break_query_mode
aspect_break_query_mode:
scalar aspect_set_query_mode,_runtime_set_query_mode
scalar aspect_set_findcase_value,_runtime_set_findcase_value
scalar aspect_set_switchcase_value,_runtime_set_switchcase_value
scalar aspect_find_found,_runtime_find_found
scalar aspect_case_integer,_runtime_case_integer
global aspect_case_type,_runtime_case_type,aspect_case_string,_runtime_case_string
aspect_case_type:
_runtime_case_type: db 0
aspect_case_string:
_runtime_case_string: times 81 db 0
global _runtime_set_duplex_changed
_runtime_set_duplex_changed: dw 0
global aspect_set_table
aspect_set_table:
%assign setting 0
%rep 256
%if setting=0x09
 dw aspect_break_setting
%elif setting=0x12
 dw aspect_set_display
%elif setting=0x18
 dw runtime_set_duplex
%elif setting=0x23
 dw aspect_set_findcase
%elif setting=0x29
 dw aspect_set_keys
%elif setting=0x2e
 dw aspect_set_msg_crlf
%elif setting=0x30
 dw aspect_set_pausechar
%elif setting=0x3b
 dw aspect_set_rxdata
%elif setting=0x44
 dw aspect_set_switchcase
%elif setting=0x4c
 dw aspect_set_txpace
%elif setting=0x55
 dw aspect_set_waitcase
%elif setting=0x56
 dw aspect_set_whencase
%else
 dw unsupported
%endif
%assign setting setting+1
%endrep
%ifndef ASPECT_RUNTIME_SERIAL
scalar aspect_serial_rx_count,_runtime_serial_rx_count
%else
extern aspect_serial_rx_count
%endif
scalar aspect_flow_depth,_runtime_depth
scalar aspect_flow_frame,_runtime_frame
global aspect_receive_suppress_echo,_runtime_receive_suppress_echo
aspect_receive_suppress_echo:
_runtime_receive_suppress_echo:
scalar aspect_flow_wait_gate,_runtime_wait_gate
scalar aspect_stack_pointer,_runtime_stack_pointer
scalar aspect_ops_source_type,_runtime_source_type
scalar aspect_ops_target_type,_runtime_target_type
scalar aspect_operand_lookahead,_runtime_lookahead
scalar aspect_expr_stage_index,_runtime_stage_index
scalar aspect_dispatch_exit_state,_runtime_exit_state
scalar aspect_flow_local_count,_runtime_local_count
scalar aspect_globals_count,_runtime_string_count
scalar aspect_string_pending_near,_runtime_string_pending_near
scalar aspect_string_scratch_pointer,_runtime_string_scratch_pointer
scalar aspect_string_scratch_index,_runtime_string_scratch_index
scalar aspect_string_check_range,_runtime_string_check_range
scalar aspect_string_compare_result,_runtime_string_compare_result
 global aspect_string_pending_far,_runtime_string_pending_far
aspect_string_pending_far:
_runtime_string_pending_far: dd 0
 global aspect_string_bank_a,_runtime_string_bank_a
aspect_string_bank_a:
_runtime_string_bank_a: times 10*81 db 0
 global aspect_string_scratch,_runtime_string_scratch
aspect_string_scratch:
_runtime_string_scratch: times 11*81 db 0
; Recovered literal-transform algorithm constants, shared with literal.c.
 global aspect_string_transform
aspect_string_transform: db 0xb3,0x35,0x0b,0xc7,0x47,0x29,0x1d,0xfb,0x1f,0x7f,0x05,0x59,0x17
scalar aspect_ops_word_value,_runtime_word_value
 global aspect_ops_dword_value,_runtime_dword_value
aspect_ops_dword_value:
_runtime_dword_value: dd 0
 global aspect_flow_stream,aspect_dispatch_stream
aspect_flow_stream:
aspect_dispatch_stream: dw _runtime_file
 global aspect_dispatch_argument,aspect_dispatch_seek_enabled,aspect_dispatch_wait_disabled
aspect_dispatch_argument: times 10 db 0
; Native8E20 andE2F8 are shared UART count and WHEN active count.
%ifndef ASPECT_RUNTIME_SERIAL
global aspect_dispatch_paused
aspect_dispatch_paused equ aspect_serial_rx_count
%else
extern aspect_dispatch_paused
%endif
aspect_dispatch_seek_enabled equ aspect_when_active_count
 global aspect_dispatch_next_script
; Native E104 is shared by scratch reads and the next-script pointer.
aspect_dispatch_next_script equ aspect_string_scratch_pointer
; String parameter pushes require a full readable81-byte value.
empty_script: times 81 db 0
; This aliases the same gate word used by recovered CF/D0.
aspect_dispatch_wait_disabled equ aspect_flow_wait_gate
 global aspect_abort_display_position,aspect_abort_format_string
aspect_abort_display_position: dw 0
aspect_abort_format_string: db 'owned script',0
 global _runtime_abi_bad
_runtime_abi_bad: dw 0
saved_sp: dw 0
 global aspect_flow_locals,_runtime_locals
aspect_flow_locals:
_runtime_locals: times 36 db 0
 global aspect_globals_table,_runtime_strings
aspect_globals_table:
_runtime_strings: times 128 dd 0
 global aspect_operand_integer_bank_a,_runtime_integer_a
aspect_operand_integer_bank_a:
_runtime_integer_a: times 10 dw 0
 global aspect_operand_integer_bank_b,_runtime_integer_b
aspect_operand_integer_bank_b:
_runtime_integer_b: times 128 dw 0
 global aspect_operand_long_bank,_runtime_longs
aspect_operand_long_bank:
_runtime_longs: times 128 dd 0
 global aspect_expr_float_bank,_runtime_float_bank
aspect_expr_float_bank:
_runtime_float_bank: times 128*8 db 0
 global aspect_operand_system_values,_runtime_system
aspect_operand_system_values:
_runtime_system: times 256*8 db 0
 global aspect_expr_stage_types,_runtime_stage_types
aspect_expr_stage_types:
_runtime_stage_types: times 10 db 0
 global aspect_ops_float_value,_runtime_float_values
aspect_ops_float_value:
_runtime_float_values: times 10*8 db 0
 global aspect_expr_float_zero
aspect_expr_float_zero: times 8 db 0
 global aspect_stack_arena,_runtime_arena
aspect_stack_arena:
_runtime_arena: times 0x3aca db 0
 global aspect_dispatch_handlers
aspect_dispatch_handlers:
%assign op 0
%rep 215
%if op=0x00
 dw aspect_arith_add
%elif op=0x02
 dw aspect_arith_bit_and
%elif op=0x03
 dw aspect_ops_logical_and
%elif op=0x06
 dw aspect_convert_atoi
%elif op=0x07
 dw aspect_convert_atol
%elif op=0x0d
 dw aspect_break_command
%elif op=0x37
 dw aspect_fetch_command
%elif op=0x13
 dw aspect_arith_bit_not
%elif op=0x15
 dw aspect_expr_branch_false
%elif op=0x1e
 dw aspect_ops_decrement
%elif op=0x26
 dw aspect_arith_divide
%elif op=0x32
 dw aspect_ops_equal
%elif op=0x33
 dw aspect_console_exit
%elif op=0x48
 dw aspect_ops_less_equal
%elif op=0x54
 dw aspect_ops_less
%elif op=0x5a
 dw aspect_ops_increment
%elif op=0x5b
 dw aspect_ops_assign
%elif op=0x5c
 dw aspect_ops_assign_chained
%elif op=0x62
 dw aspect_flow_jump
%elif op=0x68
 dw aspect_ops_greater_equal
%elif op=0x6d
 dw aspect_ops_greater
%elif op=0x7b
 dw aspect_arith_modulo
%elif op=0x7d
 dw aspect_arith_multiply
%elif op=0x7e
 dw aspect_arith_negate
%elif op=0x7f
 dw aspect_ops_not_equal
%elif op=0x81
 dw aspect_ops_logical_not
%elif op=0x82
 dw aspect_arith_bit_or
%elif op=0x84
 dw aspect_ops_logical_or
%elif op=0x94
 dw aspect_flow_return
%elif op=0x95
 dw aspect_flow_return_framed
%elif op=0x61
 dw aspect_convert_itoa
%elif op=0x6e
 dw aspect_convert_ltoa
%elif op=0x76
 dw aspect_console_message
%elif op=0x88
 dw aspect_console_pause
%elif op=0x1c
 dw aspect_when_cancel
%elif op=0x9e
 dw aspect_set_dispatch
%elif op=0x3b
 dw aspect_find_command
%elif op=0xb8
 dw aspect_case_switch
%elif op=0x0f
 dw aspect_case_compare
%elif op=0x9a
 dw aspect_strcmd_compare_bytes
%elif op=0xa4
 dw aspect_arith_shift_left
%elif op=0xa5
 dw aspect_arith_shift_right
%elif op=0xaa
 dw aspect_strcmd_concat
%elif op=0xab
 dw aspect_strcmd_compare
%elif op=0xac
 dw aspect_string_assign
%elif op=0xae
 dw aspect_strcmd_length
%elif op=0xaf
 dw aspect_strcmd_lower
%elif op=0xb0
 dw aspect_strcmd_get_char
%elif op=0xb1
 dw aspect_strcmd_set_char
%elif op=0xb2
 dw aspect_strcmd_fill
%elif op=0xb3
 dw aspect_strcmd_subcopy
%elif op=0xb4
 dw aspect_strcmd_upper
%elif op=0xb5
 dw aspect_arith_subtract
%elif op=0xb6
 dw aspect_strcmd_substr
%elif op=0xbc
 dw aspect_expr_branch_true
%elif op=0xbd
 dw aspect_expr_branch_false_alias
%elif op=0xbf
 dw runtime_serial_transmit
%elif op=0xc9
 dw runtime_receive_comgetc
%elif op=0xca
 dw runtime_receive_comgetcd
%elif op=0xc6
 dw aspect_arith_bit_xor
%elif op=0xc7
 dw aspect_flow_call_operand
%elif op=0xc8
 dw aspect_flow_call_framed
%elif op=0xcc
 dw aspect_parameter_push_numeric
%elif op=0xcd
 dw aspect_parameter_push_string
%elif op=0xce
 dw runtime_receive_rget
%elif op=0xcf
 dw aspect_flow_gate_decrement
%elif op=0xd0
 dw aspect_flow_gate_increment
%elif op=0xd2
 dw aspect_flow_reserve_locals
%elif op=0xd4
 dw runtime_serial_wait_for
%elif op=0xd5
 dw runtime_receive_wait_quiet
%elif op=0xd6
 dw runtime_when_register
%else
 dw unsupported
%endif
%assign op op+1
%endrep
global aspect_serial_ctype
aspect_serial_ctype:
%assign serial_char 0
%rep 256
%if serial_char >= 'a' && serial_char <= 'z'
 db 2
%elif serial_char >= '0' && serial_char <= '9'
 db 4
%else
 db 0
%endif
%assign serial_char serial_char+1
%endrep
