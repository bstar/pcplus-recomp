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

; Maintained builtin routing: original string builtin19 is the empty string.
; All other builtin services remain explicit unsupported actions.
global aspect_string_builtin
aspect_string_builtin:
 push bp
 mov bp,sp
 cmp word [bp+4],19
 jne unsupported
 mov ax,empty_script
 pop bp
 ret 2

global aspect_operand_builtin_integer,aspect_operand_builtin_long
aspect_operand_builtin_integer:
aspect_operand_builtin_long:
 mov ax,3
 jmp fail

global aspect_dispatch_wait,aspect_dispatch_shutdown
 global aspect_abort_tell,aspect_abort_format,aspect_abort_print
aspect_dispatch_wait:
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

SEGMENT _DATA public class=DATA use16
GROUP DGROUP _DATA
%macro scalar 2
 global %1,%2
%1:
%2: dw 0
%endmacro
scalar aspect_flow_depth,_runtime_depth
scalar aspect_flow_frame,_runtime_frame
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
 global aspect_dispatch_argument,aspect_dispatch_paused,aspect_dispatch_seek_enabled,aspect_dispatch_wait_disabled
aspect_dispatch_argument: times 10 db 0
aspect_dispatch_paused: dw 0
aspect_dispatch_seek_enabled: dw 0
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
%elif op=0xa4
 dw aspect_arith_shift_left
%elif op=0xa5
 dw aspect_arith_shift_right
%elif op=0xac
 dw aspect_string_assign
%elif op=0xb5
 dw aspect_arith_subtract
%elif op=0xbc
 dw aspect_expr_branch_true
%elif op=0xbd
 dw aspect_expr_branch_false_alias
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
%elif op=0xcf
 dw aspect_flow_gate_decrement
%elif op=0xd0
 dw aspect_flow_gate_increment
%elif op=0xd2
 dw aspect_flow_reserve_locals
%else
 dw unsupported
%endif
%assign op op+1
%endrep
