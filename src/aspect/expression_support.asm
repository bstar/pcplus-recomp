; Native PCPlus2.01 ASPECT expression/conditional support. Retained anchored
; overlay16 listings D2A0,D3F2,D3F9,D401,DB7D,DBC6,DBDD,DE4D,DE92,DECB.
; Resident9AC0 byte comparison independently observed through REA:
; ev_7a9e24a3273e69e0315cb5039db67e01713be330cdec779c10c1ec02bfb2700d.
; Original SHA6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Near DS=SS, DF=0. Branch consumes one word(RET2); other entries RET.
; Float read is a distinct dependency; byte comparison does not implement FP.
; Bank/index/frame and staging bounds remain unchecked native behavior.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_EXPR_FLAT
%if ASPECT_EXPR_UNIT=1
ORG 0xd2a0
%elif ASPECT_EXPR_UNIT=2
ORG 0xd3f2
%elif ASPECT_EXPR_UNIT=3
ORG 0xdb7d
%elif ASPECT_EXPR_UNIT=4
ORG 0xde4d
%elif ASPECT_EXPR_UNIT=5
ORG 0x9ac0
%else
%error Select ASPECT_EXPR_UNIT1..5
%endif
%define aspect_dispatch_read 0x4cb4
%define aspect_operand_is_integer 0xdb10
%define aspect_operand_is_long 0xdb2b
%define aspect_operand_is_float 0xdb48
%define aspect_operand_read_integer 0xdc48
%define aspect_operand_read_long 0xdcc1
%define aspect_operand_next_token 0xe0f1
%define aspect_operand_frame_plus 0xd19e
%define aspect_operand_frame_minus 0xd1a6
%define aspect_operand_invalid 0x4f90
%define aspect_operand_lookahead 0xe38c
%define aspect_operand_integer_bank_a 0xd126
%define aspect_operand_integer_bank_b 0xd482
%define aspect_operand_long_bank 0xd582
%define aspect_operand_system_values 0xe3c4
%define aspect_expr_float_bank 0xd782
%define aspect_expr_stage_index 0xe390
%define aspect_expr_stage_types 0xe146
%define aspect_ops_float_value 0xe150
%define aspect_expr_float_zero 0xe128
%define aspect_expr_read_float 0xdd26
%define aspect_flow_read_dword 0xe176
%define aspect_flow_seek 0xd287
%define erase_move_bytes 0x85b4
%define native_boolean 0xdb7d
%define native_branch 0xd2a0
%define native_compare 0x9ac0
%else
%define ASPECT_EXPR_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_expr_branch,aspect_expr_branch_false,aspect_expr_branch_true,aspect_expr_branch_false_alias
 global aspect_expr_boolean,aspect_expr_signed,aspect_expr_stage
 global aspect_expr_integer_address,aspect_expr_long_address,aspect_expr_float_address,aspect_expr_compare
extern aspect_dispatch_read,aspect_operand_is_integer,aspect_operand_is_long,aspect_operand_is_float
extern aspect_operand_read_integer,aspect_operand_read_long,aspect_operand_next_token
extern aspect_operand_frame_plus,aspect_operand_frame_minus,aspect_operand_invalid,aspect_operand_lookahead
extern aspect_operand_integer_bank_a,aspect_operand_integer_bank_b,aspect_operand_long_bank,aspect_operand_system_values
extern aspect_expr_float_bank,aspect_expr_stage_index,aspect_expr_stage_types,aspect_ops_float_value
extern aspect_expr_float_zero,aspect_expr_read_float,aspect_flow_read_dword,aspect_flow_seek,erase_move_bytes
%define native_boolean aspect_expr_boolean
%define native_branch aspect_expr_branch
%define native_compare aspect_expr_compare
%endif
%if ASPECT_EXPR_UNIT=0 || ASPECT_EXPR_UNIT=1
aspect_expr_branch:
 push bp
 mov_load bp,sp
 sub sp,byte 4
 push si
 call aspect_flow_read_dword
 mov [bp-4],ax
 mov [bp-2],dx
 call native_boolean
 mov_load si,ax
 cmp word [bp+4],byte 0
 jne .sense
 cmp si,byte 1
 sbb_load ax,ax
 neg ax
.sense:
 or_load ax,ax
 jz .done
 push word [bp-2]
 push word [bp-4]
 call aspect_flow_seek
.done:
 pop si
 mov_load sp,bp
 pop bp
 ret 2
%endif
%if ASPECT_EXPR_UNIT=0 || ASPECT_EXPR_UNIT=2
aspect_expr_branch_false:
 sub_load ax,ax
 push ax
 call native_branch
 ret
aspect_expr_branch_true:
 mov ax,1
 push ax
 call native_branch
 ret
aspect_expr_branch_false_alias:
 sub_load ax,ax
 push ax
 call native_branch
 ret
%endif
%if ASPECT_EXPR_UNIT=0 || ASPECT_EXPR_UNIT=3
aspect_expr_boolean:
 push si
 call aspect_dispatch_read
 mov_load si,ax
 mov [aspect_operand_lookahead],si
 push si
 call aspect_operand_is_integer
 or_load ax,ax
 jz .long
 call aspect_operand_read_integer
 cmp ax,strict word 1
 sbb_load ax,ax
 inc ax
 pop si
 ret
.long:
 push si
 call aspect_operand_is_long
 or_load ax,ax
 jz .floating
 call aspect_operand_read_long
 or_load dx,ax
 jz .zero
 mov ax,1
 pop si
 ret
.zero:
 sub_load ax,ax
 pop si
 ret
.floating:
 mov ax,8
 push ax
 mov ax,aspect_expr_float_zero
 push ax
 call aspect_expr_read_float
 push ax
 call native_compare
 add sp,byte 6
 pop si
 ret
aspect_expr_signed:
 call aspect_dispatch_read
 mov [aspect_operand_lookahead],ax
 push ax
 call aspect_operand_is_long
 or_load ax,ax
 jz .integer
 call aspect_operand_read_long
 ret
.integer:
 call aspect_operand_read_integer
 cwd
 ret
aspect_expr_stage:
 call aspect_dispatch_read
 mov [aspect_operand_lookahead],ax
 mov al,[aspect_operand_lookahead]
 mov bx,[aspect_expr_stage_index]
 mov [bx+aspect_expr_stage_types],al
 push word [aspect_operand_lookahead]
 call aspect_operand_is_float
 or_load ax,ax
 jz .integer
 mov ax,8
 push ax
 call aspect_expr_read_float
 push ax
 mov cl,3
 mov ax,[aspect_expr_stage_index]
 shl ax,cl
 add ax,aspect_ops_float_value
 push ax
 call erase_move_bytes
 add sp,byte 6
 jmp short .next
.integer:
 push word [aspect_operand_lookahead]
 call aspect_operand_is_integer
 or_load ax,ax
 jz .long
 call aspect_operand_read_integer
 mov cl,3
 mov bx,[aspect_expr_stage_index]
 shl bx,cl
 mov [bx+aspect_ops_float_value],ax
 jmp short .next
.long:
 call aspect_operand_read_long
 mov cl,3
 mov bx,[aspect_expr_stage_index]
 shl bx,cl
 mov [bx+aspect_ops_float_value],ax
 mov [bx+aspect_ops_float_value+2],dx
.next:
 inc word [aspect_expr_stage_index]
 ret
%endif
%if ASPECT_EXPR_UNIT=0 || ASPECT_EXPR_UNIT=4
aspect_expr_integer_address:
 call aspect_operand_next_token
 sub ax,strict word 0x65
 jz .builtin
 sub ax,strict word 0x14
 jz .system
 sub ax,strict word 0x14
 jz .global
 sub ax,strict word 0xa
 jz .minus
 sub ax,strict word 0xa
 jz .plus
 call aspect_operand_invalid
 ret
.builtin:
 call aspect_dispatch_read
 shl ax,1
 add ax,aspect_operand_integer_bank_a
 ret
.system:
 call aspect_dispatch_read
 mov cl,3
 shl ax,cl
 add ax,aspect_operand_system_values
 ret
.global:
 call aspect_dispatch_read
 shl ax,1
 add ax,aspect_operand_integer_bank_b
 ret
.minus:
 call aspect_operand_frame_minus
 ret
.plus:
 call aspect_operand_frame_plus
 ret
aspect_expr_long_address:
 call aspect_operand_next_token
 sub ax,strict word 0x7a
 jz .system
 sub ax,strict word 0x14
 jz .global
 sub ax,strict word 0xa
 jz .minus
 sub ax,strict word 0xa
 jz .plus
 call aspect_operand_invalid
 ret
.system:
 call aspect_dispatch_read
 mov cl,3
 shl ax,cl
 add ax,aspect_operand_system_values
 ret
.global:
 call aspect_dispatch_read
 shl ax,1
 shl ax,1
 add ax,aspect_operand_long_bank
 ret
.minus:
 call aspect_operand_frame_minus
 ret
.plus:
 call aspect_operand_frame_plus
 ret
aspect_expr_float_address:
 call aspect_operand_next_token
 sub ax,strict word 0x7b
 jz .system
 sub ax,strict word 0x14
 jz .global
 sub ax,strict word 0xa
 jz .minus
 sub ax,strict word 0xa
 jz .plus
 call aspect_operand_invalid
 ret
.system:
 call aspect_dispatch_read
 mov cl,3
 shl ax,cl
 add ax,aspect_operand_system_values
 ret
.global:
 call aspect_dispatch_read
 mov cl,3
 shl ax,cl
 add ax,aspect_expr_float_bank
 ret
.minus:
 call aspect_operand_frame_minus
 ret
.plus:
 call aspect_operand_frame_plus
 ret
%endif
%if ASPECT_EXPR_UNIT=0 || ASPECT_EXPR_UNIT=5
aspect_expr_compare:
 push bp
 mov_load bp,sp
 mov_load dx,di
 mov_load bx,si
 mov ax,ds
 mov es,ax
 mov si,[bp+4]
 mov di,[bp+6]
 xor_load ax,ax
 mov cx,[bp+8]
 jcxz .done
 repe cmpsb
 jz .done
 sbb_load ax,ax
 sbb ax,strict word 0xffff
.done:
 mov_load si,bx
 mov_load di,dx
 pop bp
 ret
%endif
