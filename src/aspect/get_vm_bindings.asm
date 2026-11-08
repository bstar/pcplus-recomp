; Maintained full-VM bindings, not recovered original bridge bytes.
BITS 16
CPU 8086
SEGMENT GET_VM_CODE public align=16 class=FARCODE use16
extern _get_bank_width,_get_bank_string,_get_bank_integer,_get_bank_long
extern _get_bank_optional,_get_bank_itoa,_get_bank_ltoa,_get_bank_flush
extern _get_bank_atoi,_get_bank_atol,_get_bank_copy,_get_bank_bell,_get_bank_error
extern _get_bank_confirm,runtime_get_abort_gate_impl
extern _runtime_get_cursor_impl,_runtime_get_adopt_impl
%macro alias 2
 global %1
 %1: jmp %2
%endmacro
alias aspect_get_read_width,_get_bank_width
alias aspect_get_string_destination,_get_bank_string
alias aspect_get_integer_destination,_get_bank_integer
alias aspect_get_long_destination,_get_bank_long
alias aspect_get_optional,_get_bank_optional
alias aspect_get_integer_text,_get_bank_itoa
alias aspect_get_long_text,_get_bank_ltoa
alias aspect_get_commit_string,_get_bank_flush
alias aspect_get_parse_integer,_get_bank_atoi
alias aspect_get_parse_long,_get_bank_atol
alias aspect_get_copy,_get_bank_copy
alias aspect_get_bell,_get_bank_bell
alias aspect_get_cursor,_runtime_get_cursor_impl
alias aspect_get_cancel_pending,_get_bank_confirm
alias aspect_get_cancel_dispatch,runtime_get_abort_gate_impl
global aspect_get_set_cursor
aspect_get_set_cursor:
 push dx
 push ax
 call _runtime_get_adopt_impl
 add sp,4
 ret
; Only ordinary GET mode0 is dispatched. Positioned/sibling modes have no
; admitted grammar; floating conversion must fail rather than fabricate data.
global aspect_get_read_position,aspect_get_read_attribute
aspect_get_read_position:
aspect_get_read_attribute:
 mov ax,3
 jmp failure
global aspect_get_float_destination,aspect_get_float_text,aspect_get_parse_float
aspect_get_float_destination:
aspect_get_float_text:
aspect_get_parse_float:
 mov ax,4
failure:
 push ax
 call _get_bank_error
 add sp,2
 jmp runtime_get_abort_gate_impl
; Identity tag only. The maintained editor handles the string key policy and
; does not invoke this original near callback. No native filter recovery claim.
global aspect_get_string_filter
aspect_get_string_filter: xor ax,ax
 ret
