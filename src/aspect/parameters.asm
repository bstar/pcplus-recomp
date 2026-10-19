; Exact native PCPlus2.01 overlay16 D1B0..D1F1 parameter primitives.
; Retained REA anchored16 functions0x1d1b0/0x1d1b8/0x1d1ea.asm;
; original SHA2566401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS,DF=0,nearRET; BP/SI/DI preserved,other registers/flags volatile.
; stack_address returns AX=word_operand+current value-stack pointer,unchecked.
; push_numeric caches the raw token, classifies unsigned token%10 as1/2, and
; forwards every other token to the floating operand service without checking
; its class. Float/string callbacks return near pointers to8/81 readablebytes.
; Actual native typed-stack reserve/copy policy applies after operand reading:
; errors may unwind or return and continue; no parser/resource rollback exists.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_PARAMETERS_FLAT
ORG 0xd1b0
%define aspect_flow_read_word 0xe129
%define aspect_stack_pointer 0xe13c
%define aspect_dispatch_read 0x4cb4
%define aspect_operand_lookahead 0xe38c
%define aspect_operand_is_integer 0xdb10
%define aspect_operand_is_long 0xdb2b
%define aspect_operand_read_integer 0xdc48
%define aspect_operand_read_long 0xdcc1
%define aspect_expr_read_float 0xdd26
%define aspect_string_read 0xdf04
%define aspect_stack_push_word 0xd0f2
%define aspect_stack_push_dword 0xd110
%define aspect_stack_push_eight 0xd134
%define aspect_stack_push_string 0xd157
%else
SEGMENT _TEXT public class=CODE use16
global aspect_parameter_stack_address,aspect_parameter_push_numeric,aspect_parameter_push_string
extern aspect_flow_read_word,aspect_stack_pointer,aspect_dispatch_read,aspect_operand_lookahead
extern aspect_operand_is_integer,aspect_operand_is_long,aspect_operand_read_integer,aspect_operand_read_long
extern aspect_expr_read_float,aspect_string_read
extern aspect_stack_push_word,aspect_stack_push_dword,aspect_stack_push_eight,aspect_stack_push_string
%endif
aspect_parameter_stack_address:
 call aspect_flow_read_word
 add ax,[aspect_stack_pointer]
 ret
aspect_parameter_push_numeric:
 call aspect_dispatch_read
 mov [aspect_operand_lookahead],ax
 push ax
 call aspect_operand_is_integer
 or_load ax,ax
 jz .long
 call aspect_operand_read_integer
 push ax
 call aspect_stack_push_word
 ret
.long:
 push word [aspect_operand_lookahead]
 call aspect_operand_is_long
 or_load ax,ax
 jz .float
 call aspect_operand_read_long
 push dx
 push ax
 call aspect_stack_push_dword
 ret
.float:
 call aspect_expr_read_float
 push ax
 call aspect_stack_push_eight
 ret
aspect_parameter_push_string:
 call aspect_string_read
 push ax
 call aspect_stack_push_string
 ret
