; Exact native PCPlus2.01 overlay16 D4A5..D942 numeric metadata/comparison/assignment.
; Retained anchored16 function listings; original SHA256
; 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS, DF=0; native near ABI. store_boolean and assignment consume one word.
; BP/SI/DI preserved. Shared type/result state is nonreentrant; all native type
; fallthroughs, truncation, wrap and aliasing behavior are preserved.
; Float/system/operand services remain explicit caller-supplied dependencies.
; No literal-only evaluator, float approximation, checked-address layer or
; independently complete arithmetic engine is provided here.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_OPERATIONS_FLAT
ORG 0xd4a5
%define aspect_dispatch_read 0x4cb4
%define aspect_expr_boolean 0xdb7d
%define aspect_expr_signed 0xdbc6
%define aspect_expr_stage 0xdbdd
%define aspect_operand_read_integer 0xdc48
%define aspect_operand_read_long 0xdcc1
%define aspect_expr_read_float 0xdd26
%define aspect_expr_integer_address 0xde4d
%define aspect_expr_long_address 0xde92
%define aspect_expr_float_address 0xdecb
%define aspect_operand_is_integer 0xdb10
%define aspect_operand_is_long 0xdb2b
%define erase_move_bytes 0x85b4
%define aspect_ops_float_transform 0xd408
%define aspect_ops_float_operand 0xd446
%define aspect_ops_float_destination 0xd458
%define aspect_ops_float_compare 0xd48c
%define aspect_ops_source_type 0xe3c0
%define aspect_ops_target_type 0xe3c2
%define aspect_operand_lookahead 0xe38c
%define aspect_ops_word_value 0xd474
%define aspect_ops_dword_value 0xd476
%define aspect_ops_float_value 0xe150
%else
SEGMENT _TEXT public class=CODE use16
global aspect_ops_metadata
global aspect_ops_store_result
global aspect_ops_store_boolean
global aspect_ops_load_first
global aspect_ops_word_result
global aspect_ops_dword_result
global aspect_ops_eight_result
global aspect_ops_logical_and
global aspect_ops_logical_not
global aspect_ops_logical_or
global aspect_ops_equal
global aspect_ops_less_equal
global aspect_ops_less
global aspect_ops_greater_equal
global aspect_ops_greater
global aspect_ops_not_equal
global aspect_ops_decrement
global aspect_ops_increment
global aspect_ops_assign
global aspect_ops_assign_chained
global aspect_ops_assignment
extern aspect_dispatch_read
extern aspect_expr_boolean
extern aspect_expr_signed
extern aspect_expr_stage
extern aspect_operand_read_integer
extern aspect_operand_read_long
extern aspect_expr_read_float
extern aspect_expr_integer_address
extern aspect_expr_long_address
extern aspect_expr_float_address
extern aspect_operand_is_integer
extern aspect_operand_is_long
extern erase_move_bytes
extern aspect_ops_float_transform
extern aspect_ops_float_operand
extern aspect_ops_float_destination
extern aspect_ops_float_compare
extern aspect_ops_source_type
extern aspect_ops_target_type
extern aspect_operand_lookahead
extern aspect_ops_word_value
extern aspect_ops_dword_value
extern aspect_ops_float_value
%endif

aspect_ops_metadata:
 call aspect_dispatch_read
 mov_load cx,ax
 shr ax, 0x1
 shr ax, 0x1
 mov [aspect_ops_target_type], ax
 and cx, 0x3
 mov word [aspect_ops_source_type], cx
 ret

aspect_ops_store_result:
 push si
 cmp word [aspect_ops_target_type], 0x0
 jnz ops_loc_d4cd
 call aspect_expr_integer_address
 mov_load si,ax
 call aspect_ops_word_result
 mov word [si], ax
 pop si
 ret
ops_loc_d4cd:
 cmp word [aspect_ops_target_type], 0x1
 jnz ops_loc_d4e3
 call aspect_expr_long_address
 mov_load si,ax
 call aspect_ops_dword_result
 mov word [si], ax
 mov word [si + 0x2], dx
 pop si
 ret
ops_loc_d4e3:
 mov ax, 0x8
 push ax
 call aspect_ops_eight_result
 push ax
 call aspect_expr_float_address
 push ax
 call erase_move_bytes
 add sp, 0x6
 pop si
 ret

aspect_ops_store_boolean:
 push bp
 mov_load bp,sp
 mov ax, word [bp + 0x4]
 mov [aspect_ops_word_value], ax
 mov word [aspect_ops_source_type], 0x0
 call aspect_ops_store_result
 mov_load sp,bp
 pop bp
 ret 0x2

aspect_ops_load_first:
 call aspect_ops_metadata
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d520
 call aspect_operand_read_integer
 mov [aspect_ops_word_value], ax
 ret
ops_loc_d520:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d532
 call aspect_expr_signed
 mov [aspect_ops_dword_value], ax
 mov word [aspect_ops_dword_value+2], dx
 ret
ops_loc_d532:
 call aspect_expr_stage
 ret

aspect_ops_word_result:
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d541
 mov ax, [aspect_ops_word_value]
 ret
ops_loc_d541:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d54c
 mov ax, [aspect_ops_dword_value]
 ret
ops_loc_d54c:
 mov ax, [aspect_ops_float_value]
 ret

aspect_ops_dword_result:
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d55c
 mov ax, [aspect_ops_word_value]
 cwd
 ret
ops_loc_d55c:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d56b
 mov ax, [aspect_ops_dword_value]
 mov dx, word [aspect_ops_dword_value+2]
 ret
ops_loc_d56b:
 mov ax, [aspect_ops_float_value]
 mov dx, word [aspect_ops_float_value+2]
 ret

aspect_ops_eight_result:
 cmp word [aspect_ops_source_type], 0x2
 jz ops_loc_d59e
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d589
 mov ax, [aspect_ops_word_value]
 mov [aspect_ops_float_value], ax
 jmp ops_loc_d597
ops_loc_d589:
 mov ax, [aspect_ops_dword_value]
 mov dx, word [aspect_ops_dword_value+2]
 mov [aspect_ops_float_value], ax
 mov word [aspect_ops_float_value+2], dx
ops_loc_d597:
 mov ax, 0x5b
 push ax
 call aspect_ops_float_transform
ops_loc_d59e:
 mov ax, aspect_ops_float_value
 ret

aspect_ops_logical_and:
 push di
 push si
 call aspect_ops_metadata
 call aspect_expr_boolean
 mov_load di,ax
 call aspect_expr_boolean
 mov_load si,ax
 or_load di,di
 jz ops_loc_d5be
 or_load si,si
 jz ops_loc_d5be
 mov dx, 0x1
 jmp ops_loc_d5c0
ops_loc_d5be:
 sub_load dx,dx
ops_loc_d5c0:
 push dx
 call aspect_ops_store_boolean
 pop si
 pop di
 ret

aspect_ops_logical_not:
 call aspect_ops_metadata
 call aspect_expr_boolean
 cmp ax, strict word 0x1
 sbb_load ax,ax
 neg ax
 push ax
 call aspect_ops_store_boolean
 ret

aspect_ops_logical_or:
 push di
 push si
 call aspect_ops_metadata
 call aspect_expr_boolean
 mov_load di,ax
 call aspect_expr_boolean
 mov_load si,ax
 or_load di,di
 jnz ops_loc_d5f4
 or_load si,si
 jnz ops_loc_d5f4
 sub_load dx,dx
 jmp ops_loc_d5f7
ops_loc_d5f4:
 mov dx, 0x1
ops_loc_d5f7:
 push dx
 call aspect_ops_store_boolean
 pop si
 pop di
 ret

aspect_ops_equal:
 call aspect_ops_load_first
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d618
 call aspect_operand_read_integer
 cmp ax, word [aspect_ops_word_value]
 jz ops_loc_d62e
ops_loc_d611:
 sub_load ax,ax
ops_loc_d613:
 push ax
 call aspect_ops_store_boolean
 ret
ops_loc_d618:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d633
 call aspect_expr_signed
 cmp ax, word [aspect_ops_dword_value]
 jnz ops_loc_d611
 cmp dx, word [aspect_ops_dword_value+2]
 jnz ops_loc_d611
ops_loc_d62e:
 mov ax, 0x1
 jmp ops_loc_d613
ops_loc_d633:
 mov ax, 0x32
 push ax
 call aspect_ops_float_compare
 ret

aspect_ops_less_equal:
 call aspect_ops_load_first
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d655
 call aspect_operand_read_integer
 cmp ax, word [aspect_ops_word_value]
 jle ops_loc_d66d
ops_loc_d64e:
 sub_load ax,ax
ops_loc_d650:
 push ax
 call aspect_ops_store_boolean
 ret
ops_loc_d655:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d672
 call aspect_expr_signed
 cmp dx, word [aspect_ops_dword_value+2]
 jg ops_loc_d64e
 jl ops_loc_d66d
 cmp ax, word [aspect_ops_dword_value]
 ja ops_loc_d64e
ops_loc_d66d:
 mov ax, 0x1
 jmp ops_loc_d650
ops_loc_d672:
 mov ax, 0x48
 push ax
 call aspect_ops_float_compare
 ret

aspect_ops_less:
 call aspect_ops_load_first
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d694
 call aspect_operand_read_integer
 cmp ax, word [aspect_ops_word_value]
 jl ops_loc_d6ac
ops_loc_d68d:
 sub_load ax,ax
ops_loc_d68f:
 push ax
 call aspect_ops_store_boolean
 ret
ops_loc_d694:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d6b1
 call aspect_expr_signed
 cmp dx, word [aspect_ops_dword_value+2]
 jg ops_loc_d68d
 jl ops_loc_d6ac
 cmp ax, word [aspect_ops_dword_value]
 jnc ops_loc_d68d
ops_loc_d6ac:
 mov ax, 0x1
 jmp ops_loc_d68f
ops_loc_d6b1:
 mov ax, 0x54
 push ax
 call aspect_ops_float_compare
 ret

aspect_ops_greater_equal:
 call aspect_ops_load_first
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d6d3
 call aspect_operand_read_integer
 cmp ax, word [aspect_ops_word_value]
 jge ops_loc_d6eb
ops_loc_d6cc:
 sub_load ax,ax
ops_loc_d6ce:
 push ax
 call aspect_ops_store_boolean
 ret
ops_loc_d6d3:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d6f0
 call aspect_expr_signed
 cmp dx, word [aspect_ops_dword_value+2]
 jl ops_loc_d6cc
 jg ops_loc_d6eb
 cmp ax, word [aspect_ops_dword_value]
 jc ops_loc_d6cc
ops_loc_d6eb:
 mov ax, 0x1
 jmp ops_loc_d6ce
ops_loc_d6f0:
 mov ax, 0x68
 push ax
 call aspect_ops_float_compare
 ret

aspect_ops_greater:
 call aspect_ops_load_first
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d712
 call aspect_operand_read_integer
 cmp ax, word [aspect_ops_word_value]
 jg ops_loc_d72a
ops_loc_d70b:
 sub_load ax,ax
ops_loc_d70d:
 push ax
 call aspect_ops_store_boolean
 ret
ops_loc_d712:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d72f
 call aspect_expr_signed
 cmp dx, word [aspect_ops_dword_value+2]
 jl ops_loc_d70b
 jg ops_loc_d72a
 cmp ax, word [aspect_ops_dword_value]
 jbe ops_loc_d70b
ops_loc_d72a:
 mov ax, 0x1
 jmp ops_loc_d70d
ops_loc_d72f:
 mov ax, 0x6d
 push ax
 call aspect_ops_float_compare
 ret

aspect_ops_not_equal:
 call aspect_ops_load_first
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d751
 call aspect_operand_read_integer
 cmp ax, word [aspect_ops_word_value]
 jnz ops_loc_d767
ops_loc_d74a:
 sub_load ax,ax
ops_loc_d74c:
 push ax
 call aspect_ops_store_boolean
 ret
ops_loc_d751:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d76c
 call aspect_expr_signed
 cmp ax, word [aspect_ops_dword_value]
 jnz ops_loc_d767
 cmp dx, word [aspect_ops_dword_value+2]
 jz ops_loc_d74a
ops_loc_d767:
 mov ax, 0x1
 jmp ops_loc_d74c
ops_loc_d76c:
 mov ax, 0x7f
 push ax
 call aspect_ops_float_compare
 ret

aspect_ops_decrement:
 call aspect_dispatch_read
 mov [aspect_operand_lookahead], ax
 push ax
 call aspect_operand_is_integer
 or_load ax,ax
 jz ops_loc_d78a
 call aspect_expr_integer_address
 mov_load bx,ax
 dec word [bx]
 ret
ops_loc_d78a:
 push word [aspect_operand_lookahead]
 call aspect_operand_is_long
 or_load ax,ax
 jz ops_loc_d7a2
 call aspect_expr_long_address
 mov_load bx,ax
 sub word [bx], 0x1
 sbb word [bx + 0x2], 0x0
 ret
ops_loc_d7a2:
 mov ax, 0x1e
 push ax
 call aspect_ops_float_destination
 ret

aspect_ops_increment:
 call aspect_dispatch_read
 mov [aspect_operand_lookahead], ax
 push ax
 call aspect_operand_is_integer
 or_load ax,ax
 jz ops_loc_d7c0
 call aspect_expr_integer_address
 mov_load bx,ax
 inc word [bx]
 ret
ops_loc_d7c0:
 push word [aspect_operand_lookahead]
 call aspect_operand_is_long
 or_load ax,ax
 jz ops_loc_d7d8
 call aspect_expr_long_address
 mov_load bx,ax
 add word [bx], 0x1
 adc word [bx + 0x2], 0x0
 ret
ops_loc_d7d8:
 mov ax, 0x5a
 push ax
 call aspect_ops_float_destination
 ret

aspect_ops_assign:
 sub_load ax,ax
 push ax
 call aspect_ops_assignment
 ret

aspect_ops_assign_chained:
 mov ax, 0x1
 push ax
 call aspect_ops_assignment
 ret

aspect_ops_assignment:
 push bp
 mov_load bp,sp
 sub sp, 0xc
 push si
 call aspect_ops_metadata
 cmp word [aspect_ops_target_type], 0x0
 jnz ops_loc_d808
 call aspect_expr_integer_address
 mov word [bp + -0x2], ax
 jmp ops_loc_d81d
ops_loc_d808:
 cmp word [aspect_ops_target_type], 0x1
 jnz ops_loc_d817
 call aspect_expr_long_address
 mov word [bp + -0xa], ax
 jmp ops_loc_d81d
ops_loc_d817:
 call aspect_expr_float_address
 mov word [bp + -0xc], ax
ops_loc_d81d:
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d82c
 call aspect_operand_read_integer
 mov word [bp + -0x4], ax
 jmp ops_loc_d85f
ops_loc_d82c:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d83e
 call aspect_operand_read_long
 mov word [bp + -0x8], ax
 mov word [bp + -0x6], dx
 jmp ops_loc_d85f
ops_loc_d83e:
 cmp word [aspect_ops_target_type], 0x2
 jz ops_loc_d84e
 mov ax, 0x5b
 push ax
 call aspect_ops_float_operand
 jmp ops_loc_d85f
ops_loc_d84e:
 mov ax, 0x8
 push ax
 call aspect_expr_read_float
 push ax
 push word [bp + -0xc]
 call erase_move_bytes
 add sp, 0x6
ops_loc_d85f:
 cmp word [aspect_ops_target_type], 0x0
 jnz ops_loc_d89e
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d872
 mov ax, word [bp + -0x4]
 jmp ops_loc_d881
ops_loc_d872:
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d87e
 mov ax, word [bp + -0x8]
 jmp ops_loc_d881
ops_loc_d87e:
 mov ax, [aspect_ops_float_value]
ops_loc_d881:
 mov bx, word [bp + -0x2]
 mov word [bx], ax
 cmp word [bp + 0x4], 0x0
 jnz ops_loc_d88f
 jmp ops_loc_d93c
ops_loc_d88f:
 call aspect_expr_integer_address
 mov_load si,ax
 mov bx, word [bp + -0x2]
 mov ax, word [bx]
 mov word [si], ax
 jmp ops_loc_d93c
ops_loc_d89e:
 mov bx, word [bp + -0x4]
 cmp word [aspect_ops_target_type], 0x1
 jnz ops_loc_d8ec
 cmp word [aspect_ops_source_type], 0x1
 jnz ops_loc_d8b7
 mov ax, word [bp + -0x8]
 mov dx, word [bp + -0x6]
 jmp ops_loc_d8ca
ops_loc_d8b7:
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d8c3
 mov_load ax,bx
 cwd
 jmp ops_loc_d8ca
ops_loc_d8c3:
 mov ax, [aspect_ops_float_value]
 mov dx, word [aspect_ops_float_value+2]
ops_loc_d8ca:
 mov si, word [bp + -0xa]
 mov word [si], ax
 mov word [si + 0x2], dx
 cmp word [bp + 0x4], 0x0
 jz ops_loc_d93c
 call aspect_expr_long_address
 mov_load si,ax
 mov bx, word [bp + -0xa]
 mov ax, word [bx]
 mov dx, word [bx + 0x2]
 mov word [si], ax
 mov word [si + 0x2], dx
 jmp ops_loc_d93c
ops_loc_d8ec:
 cmp word [aspect_ops_source_type], 0x2
 jz ops_loc_d925
 cmp word [aspect_ops_source_type], 0x0
 jnz ops_loc_d900
 mov word [aspect_ops_float_value], bx
 jmp ops_loc_d90d
ops_loc_d900:
 mov ax, word [bp + -0x8]
 mov dx, word [bp + -0x6]
 mov [aspect_ops_float_value], ax
 mov word [aspect_ops_float_value+2], dx
ops_loc_d90d:
 mov ax, 0x5b
 push ax
 call aspect_ops_float_transform
 mov ax, 0x8
 push ax
 mov ax, aspect_ops_float_value
 push ax
 push word [bp + -0xc]
 call erase_move_bytes
 add sp, 0x6
ops_loc_d925:
 cmp word [bp + 0x4], 0x0
 jz ops_loc_d93c
 mov ax, 0x8
 push ax
 push word [bp + -0xc]
 call aspect_expr_float_address
 push ax
 call erase_move_bytes
 add sp, 0x6
ops_loc_d93c:
 pop si
 mov_load sp,bp
 pop bp
 ret 0x2
