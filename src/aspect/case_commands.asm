; PCPlus2.01 overlay16 SWITCH D372..D39F and CASE D39F..D3F2.
; Original SHA6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; REA ev_5da52d37cfc90f6d0817abfa8954c91290e806efc2384a3c70527cd9a6857d22,
; ev_40a376dd122d0a0899897fad9b455bb17ac04ea98f9db09e043bf78aa589a3bb.
; DS=SS, near RET entries. Type byte/string81/integerword are shared global
; SWITCH state, not a nested-switch stack. String CASE uses E394 as zero/nonzero;
; numeric CASE ignores it. Mismatch consumes a DWORD seek target. Native token
; modulo10, unchecked strcpy/indices/seek and shared-state lifetimes preserved.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_CASE_FLAT
%if ASPECT_CASE_UNIT=1
ORG 0xd372
%elif ASPECT_CASE_UNIT=2
ORG 0xd39f
%else
%error Select ASPECT_CASE_UNIT1..2
%endif
%define aspect_dispatch_read 0x4cb4
%define aspect_operand_lookahead 0xe38c
%define aspect_case_type 0xe376
%define aspect_case_string 0xe322
%define aspect_case_integer 0xe374
%define aspect_set_switchcase_value 0xe394
%define aspect_string_read 0xdf04
%define aspect_operand_read_integer 0xdc48
%define aspect_flow_jump 0xd349
%define aspect_flow_seek 0xd287
%define aspect_flow_read_dword 0xe176
%define program_strcpy 0x8268
%define program_strcmpi 0x93de
%define aspect_string_strcmp 0x9476
%else
%define ASPECT_CASE_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_case_switch,aspect_case_compare
extern aspect_dispatch_read,aspect_operand_lookahead
extern aspect_case_type,aspect_case_string,aspect_case_integer,aspect_set_switchcase_value
extern aspect_string_read,aspect_operand_read_integer
extern aspect_flow_jump,aspect_flow_seek,aspect_flow_read_dword
extern program_strcpy,program_strcmpi,aspect_string_strcmp
%endif
%if ASPECT_CASE_UNIT=0 || ASPECT_CASE_UNIT=1
aspect_case_switch:
 call aspect_dispatch_read
 mov [aspect_operand_lookahead],ax
 mov cx,10
 cwd
 idiv cx
 mov [aspect_case_type],dl
 or_load dl,dl
 jnz .integer
 call aspect_string_read
 push ax
 mov ax,aspect_case_string
 push ax
 call program_strcpy
 pop bx
 pop bx
 jmp short .jump
.integer:
 call aspect_operand_read_integer
 mov [aspect_case_integer],ax
.jump:
 call aspect_flow_jump
 ret
%endif
%if ASPECT_CASE_UNIT=0 || ASPECT_CASE_UNIT=2
aspect_case_compare:
 push bp
 mov_load bp,sp
 sub sp,byte 4
 call aspect_flow_read_dword
 mov [bp-4],ax
 mov [bp-2],dx
 cmp byte [aspect_case_type],0
 jnz .integer
 cmp word [aspect_set_switchcase_value],byte 0
 jnz .sensitive
 call aspect_string_read
 push ax
 mov ax,aspect_case_string
 push ax
 call program_strcmpi
 jmp short .compared
.sensitive:
 call aspect_string_read
 push ax
 mov ax,aspect_case_string
 push ax
 call aspect_string_strcmp
.compared:
 pop bx
 pop bx
 or_load ax,ax
 jnz .seek
 jmp short .done
.integer:
 call aspect_operand_read_integer
 cmp ax,[aspect_case_integer]
 jz .done
.seek:
 push word [bp-2]
 push word [bp-4]
 call aspect_flow_seek
.done:
 mov_load sp,bp
 pop bp
 ret
%endif
