; Exact PCPlus2.01 overlay17 EBB1..EE49 arithmetic instructions.
; Retained REA analysis/pcplus-overlay-anchored-17/functions/0x1e*.asm.
; Original SHA2566401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS,DF=0; near ABI. division consumes one operation word(RET2),
; other public handlers RET; BP/SI/DI preserved, other registers/flags volatile.
; Real numeric load/store/operand and long arithmetic interfaces are explicit.
; Float transform/operand/staging and comparison remain external services.
; No float approximation or checked arithmetic is introduced. Signed word
; MIN/-1 retains native INT0; zero-divisor error2 may return or nonlocally exit.
; Returned error2 reads/discards the next boolean operand and suppresses store.
; Word shifts retain original CL behavior (8086 differs from later CPUs).
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_ARITHMETIC_FLAT
ORG 0xebb1
%define aspect_ops_load_first 0xd50f
%define aspect_ops_metadata 0xd4a5
%define aspect_operand_read_integer 0xdc48
%define aspect_expr_signed 0xdbc6
%define aspect_ops_float_operand 0xd446
%define aspect_ops_store_result 0xd4b9
%define aspect_ops_float_transform 0xd408
%define aspect_long_multiply 0x9b90
%define aspect_long_shift_left 0x9bb0
%define aspect_long_shift_right 0x9bcc
%define aspect_long_divide 0x9af2
%define aspect_long_modulo 0x9b12
%define aspect_expr_stage 0xdbdd
%define aspect_operand_is_integer 0xdb10
%define aspect_operand_is_long 0xdb2b
%define aspect_expr_compare 0x9ac0
%define aspect_arith_error 0x4efb
%define aspect_expr_boolean 0xdb7d
%define aspect_ops_source_type 0xe3c0
%define aspect_ops_word_value 0xd474
%define aspect_ops_dword_value 0xd476
%define aspect_expr_float_zero 0xe128
%define aspect_expr_stage_types 0xe146
%define aspect_ops_float_value 0xe150
%else
SEGMENT _TEXT public class=CODE use16
global aspect_arith_add
global aspect_arith_bit_and
global aspect_arith_bit_not
global aspect_arith_divide
global aspect_arith_modulo
global aspect_arith_multiply
global aspect_arith_negate
global aspect_arith_bit_or
global aspect_arith_shift_left
global aspect_arith_shift_right
global aspect_arith_subtract
global aspect_arith_bit_xor
global aspect_arith_division
global aspect_arith_zero_divisor
extern aspect_ops_load_first
extern aspect_ops_metadata
extern aspect_operand_read_integer
extern aspect_expr_signed
extern aspect_ops_float_operand
extern aspect_ops_store_result
extern aspect_ops_float_transform
extern aspect_long_multiply
extern aspect_long_shift_left
extern aspect_long_shift_right
extern aspect_long_divide
extern aspect_long_modulo
extern aspect_expr_stage
extern aspect_operand_is_integer
extern aspect_operand_is_long
extern aspect_expr_compare
extern aspect_arith_error
extern aspect_expr_boolean
extern aspect_ops_source_type
extern aspect_ops_word_value
extern aspect_ops_dword_value
extern aspect_expr_float_zero
extern aspect_expr_stage_types,aspect_ops_float_value
%endif
aspect_arith_add:
 call aspect_ops_load_first
arith_loc_ebb4:
 cmp word [aspect_ops_source_type], 0x0
arith_loc_ebb9:
 jnz arith_loc_ebc4
arith_loc_ebbb:
 call aspect_operand_read_integer
arith_loc_ebbe:
 add word [aspect_ops_word_value], ax
arith_loc_ebc2:
 jmp arith_loc_ebde
arith_loc_ebc4:
 cmp word [aspect_ops_source_type], 0x1
arith_loc_ebc9:
 jnz arith_loc_ebd8
arith_loc_ebcb:
 call aspect_expr_signed
arith_loc_ebce:
 add word [aspect_ops_dword_value], ax
arith_loc_ebd2:
 adc word [aspect_ops_dword_value+2], dx
arith_loc_ebd6:
 jmp arith_loc_ebde
arith_loc_ebd8:
 sub_load ax,ax
arith_loc_ebda:
 push ax
arith_loc_ebdb:
 call aspect_ops_float_operand
arith_loc_ebde:
 call aspect_ops_store_result
arith_loc_ebe1:
 ret
aspect_arith_bit_and:
 call aspect_ops_load_first
arith_loc_ebe5:
 cmp word [aspect_ops_source_type], 0x0
arith_loc_ebea:
 jnz arith_loc_ebf5
arith_loc_ebec:
 call aspect_operand_read_integer
arith_loc_ebef:
 and word [aspect_ops_word_value], ax
arith_loc_ebf3:
 jmp arith_loc_ec00
arith_loc_ebf5:
 call aspect_expr_signed
arith_loc_ebf8:
 and word [aspect_ops_dword_value], ax
arith_loc_ebfc:
 and word [aspect_ops_dword_value+2], dx
arith_loc_ec00:
 call aspect_ops_store_result
arith_loc_ec03:
 ret
aspect_arith_bit_not:
 call aspect_ops_metadata
arith_loc_ec07:
 cmp word [aspect_ops_source_type], 0x0
arith_loc_ec0c:
 jnz arith_loc_ec18
arith_loc_ec0e:
 call aspect_operand_read_integer
arith_loc_ec11:
 not ax
arith_loc_ec13:
 mov [aspect_ops_word_value], ax
arith_loc_ec16:
 jmp arith_loc_ec26
arith_loc_ec18:
 call aspect_expr_signed
arith_loc_ec1b:
 not ax
arith_loc_ec1d:
 not dx
arith_loc_ec1f:
 mov [aspect_ops_dword_value], ax
arith_loc_ec22:
 mov word [aspect_ops_dword_value+2], dx
arith_loc_ec26:
 call aspect_ops_store_result
arith_loc_ec29:
 ret
aspect_arith_divide:
 mov ax, 0x26
arith_loc_ec2d:
 push ax
arith_loc_ec2e:
 call aspect_arith_division
arith_loc_ec31:
 ret
aspect_arith_modulo:
 mov ax, 0x7b
arith_loc_ec35:
 push ax
arith_loc_ec36:
 call aspect_arith_division
arith_loc_ec39:
 ret
aspect_arith_multiply:
 call aspect_ops_load_first
arith_loc_ec3d:
 cmp word [aspect_ops_source_type], 0x0
arith_loc_ec42:
 jnz arith_loc_ec50
arith_loc_ec44:
 call aspect_operand_read_integer
arith_loc_ec47:
 imul word [aspect_ops_word_value]
arith_loc_ec4b:
 mov [aspect_ops_word_value], ax
arith_loc_ec4e:
 jmp arith_loc_ec6c
arith_loc_ec50:
 cmp word [aspect_ops_source_type], 0x1
arith_loc_ec55:
 jnz arith_loc_ec65
arith_loc_ec57:
 call aspect_expr_signed
arith_loc_ec5a:
 push dx
arith_loc_ec5b:
 push ax
arith_loc_ec5c:
 mov ax, aspect_ops_dword_value
arith_loc_ec5f:
 push ax
arith_loc_ec60:
 call aspect_long_multiply
arith_loc_ec63:
 jmp arith_loc_ec6c
arith_loc_ec65:
 mov ax, 0x7d
arith_loc_ec68:
 push ax
arith_loc_ec69:
 call aspect_ops_float_operand
arith_loc_ec6c:
 call aspect_ops_store_result
arith_loc_ec6f:
 ret
aspect_arith_negate:
 call aspect_ops_load_first
arith_loc_ec73:
 cmp word [aspect_ops_source_type], 0x0
arith_loc_ec78:
 jnz arith_loc_ec80
arith_loc_ec7a:
 neg word [aspect_ops_word_value]
arith_loc_ec7e:
 jmp arith_loc_ec9d
arith_loc_ec80:
 cmp word [aspect_ops_source_type], 0x1
arith_loc_ec85:
 jnz arith_loc_ec96
arith_loc_ec87:
 neg word [aspect_ops_dword_value]
arith_loc_ec8b:
 adc word [aspect_ops_dword_value+2], 0x0
arith_loc_ec90:
 neg word [aspect_ops_dword_value+2]
arith_loc_ec94:
 jmp arith_loc_ec9d
arith_loc_ec96:
 mov ax, 0x7e
arith_loc_ec99:
 push ax
arith_loc_ec9a:
 call aspect_ops_float_transform
arith_loc_ec9d:
 call aspect_ops_store_result
arith_loc_eca0:
 ret
aspect_arith_bit_or:
 call aspect_ops_load_first
arith_loc_eca4:
 cmp word [aspect_ops_source_type], 0x0
arith_loc_eca9:
 jnz arith_loc_ecb4
arith_loc_ecab:
 call aspect_operand_read_integer
arith_loc_ecae:
 or word [aspect_ops_word_value], ax
arith_loc_ecb2:
 jmp arith_loc_ecbf
arith_loc_ecb4:
 call aspect_expr_signed
arith_loc_ecb7:
 or word [aspect_ops_dword_value], ax
arith_loc_ecbb:
 or word [aspect_ops_dword_value+2], dx
arith_loc_ecbf:
 call aspect_ops_store_result
arith_loc_ecc2:
 ret
aspect_arith_shift_left:
 call aspect_ops_load_first
arith_loc_ecc6:
 cmp word [aspect_ops_source_type], 0x0
arith_loc_eccb:
 jnz arith_loc_ecd8
arith_loc_eccd:
 call aspect_operand_read_integer
arith_loc_ecd0:
 mov_load cx,ax
arith_loc_ecd2:
 shl word [aspect_ops_word_value], cl
arith_loc_ecd6:
 jmp arith_loc_ece3
arith_loc_ecd8:
 call aspect_expr_signed
arith_loc_ecdb:
 push ax
arith_loc_ecdc:
 mov ax, aspect_ops_dword_value
arith_loc_ecdf:
 push ax
arith_loc_ece0:
 call aspect_long_shift_left
arith_loc_ece3:
 call aspect_ops_store_result
arith_loc_ece6:
 ret
aspect_arith_shift_right:
 call aspect_ops_load_first
arith_loc_ecea:
 cmp word [aspect_ops_source_type], 0x0
arith_loc_ecef:
 jnz arith_loc_ecfc
arith_loc_ecf1:
 call aspect_operand_read_integer
arith_loc_ecf4:
 mov_load cx,ax
arith_loc_ecf6:
 sar word [aspect_ops_word_value], cl
arith_loc_ecfa:
 jmp arith_loc_ed07
arith_loc_ecfc:
 call aspect_expr_signed
arith_loc_ecff:
 push ax
arith_loc_ed00:
 mov ax, aspect_ops_dword_value
arith_loc_ed03:
 push ax
arith_loc_ed04:
 call aspect_long_shift_right
arith_loc_ed07:
 call aspect_ops_store_result
arith_loc_ed0a:
 ret
aspect_arith_subtract:
 call aspect_ops_load_first
arith_loc_ed0e:
 cmp word [aspect_ops_source_type], 0x0
arith_loc_ed13:
 jnz arith_loc_ed1e
arith_loc_ed15:
 call aspect_operand_read_integer
arith_loc_ed18:
 sub word [aspect_ops_word_value], ax
arith_loc_ed1c:
 jmp arith_loc_ed39
arith_loc_ed1e:
 cmp word [aspect_ops_source_type], 0x1
arith_loc_ed23:
 jnz arith_loc_ed32
arith_loc_ed25:
 call aspect_expr_signed
arith_loc_ed28:
 sub word [aspect_ops_dword_value], ax
arith_loc_ed2c:
 sbb word [aspect_ops_dword_value+2], dx
arith_loc_ed30:
 jmp arith_loc_ed39
arith_loc_ed32:
 mov ax, 0xb5
arith_loc_ed35:
 push ax
arith_loc_ed36:
 call aspect_ops_float_operand
arith_loc_ed39:
 call aspect_ops_store_result
arith_loc_ed3c:
 ret
aspect_arith_bit_xor:
 call aspect_ops_load_first
arith_loc_ed40:
 cmp word [aspect_ops_source_type], 0x0
arith_loc_ed45:
 jnz arith_loc_ed50
arith_loc_ed47:
 call aspect_operand_read_integer
arith_loc_ed4a:
 xor word [aspect_ops_word_value], ax
arith_loc_ed4e:
 jmp arith_loc_ed5b
arith_loc_ed50:
 call aspect_expr_signed
arith_loc_ed53:
 xor word [aspect_ops_dword_value], ax
arith_loc_ed57:
 xor word [aspect_ops_dword_value+2], dx
arith_loc_ed5b:
 call aspect_ops_store_result
arith_loc_ed5e:
 ret
aspect_arith_division:
 push bp
arith_loc_ed60:
 mov_load bp,sp
arith_loc_ed62:
 sub sp, 0x4
arith_loc_ed65:
 push di
arith_loc_ed66:
 push si
arith_loc_ed67:
 sub_load si,si
arith_loc_ed69:
 call aspect_ops_load_first
arith_loc_ed6c:
 cmp word [aspect_ops_source_type], si
arith_loc_ed70:
 jnz arith_loc_eda2
arith_loc_ed72:
 call aspect_operand_read_integer
arith_loc_ed75:
 mov_load di,ax
arith_loc_ed77:
 or_load di,di
arith_loc_ed79:
 jz arith_loc_ed9a
arith_loc_ed7b:
 cmp word [bp + 0x4], 0x26
arith_loc_ed7f:
 jnz arith_loc_ed8d
arith_loc_ed81:
 mov ax, [aspect_ops_word_value]
arith_loc_ed84:
 cwd
arith_loc_ed85:
 idiv di
arith_loc_ed87:
 mov [aspect_ops_word_value], ax
arith_loc_ed8a:
 jmp arith_loc_ee2d
arith_loc_ed8d:
 mov ax, [aspect_ops_word_value]
arith_loc_ed90:
 cwd
arith_loc_ed91:
 idiv di
arith_loc_ed93:
 mov word [aspect_ops_word_value], dx
arith_loc_ed97:
 jmp arith_loc_ee2d
arith_loc_ed9a:
 call aspect_arith_zero_divisor
arith_loc_ed9d:
 mov_load si,ax
arith_loc_ed9f:
 jmp arith_loc_ee2d
arith_loc_eda2:
 cmp word [aspect_ops_source_type], 0x1
arith_loc_eda7:
 jnz arith_loc_edd3
arith_loc_eda9:
 call aspect_expr_signed
arith_loc_edac:
 mov word [bp - 0x2], dx
arith_loc_edaf:
 or_load dx,ax
arith_loc_edb1:
 jz arith_loc_ed9a
arith_loc_edb3:
 cmp word [bp + 0x4], 0x26
arith_loc_edb7:
 jnz arith_loc_edc6
arith_loc_edb9:
 push word [bp - 0x2]
arith_loc_edbc:
 push ax
arith_loc_edbd:
 mov ax, aspect_ops_dword_value
arith_loc_edc0:
 push ax
arith_loc_edc1:
 call aspect_long_divide
arith_loc_edc4:
 jmp arith_loc_ee2d
arith_loc_edc6:
 push word [bp - 0x2]
arith_loc_edc9:
 push ax
arith_loc_edca:
 mov ax, aspect_ops_dword_value
arith_loc_edcd:
 push ax
arith_loc_edce:
 call aspect_long_modulo
arith_loc_edd1:
 jmp arith_loc_ee2d
arith_loc_edd3:
 call aspect_expr_stage
arith_loc_edd6:
 mov al, [aspect_expr_stage_types+1]
arith_loc_edd9:
 sub_load ah,ah
arith_loc_eddb:
 push ax
arith_loc_eddc:
 call aspect_operand_is_integer
arith_loc_eddf:
 or_load ax,ax
arith_loc_ede1:
 jz arith_loc_edea
arith_loc_ede3:
 cmp word [aspect_ops_float_value+8], 0x1
arith_loc_ede8:
 jmp arith_loc_ee1a
arith_loc_edea:
 mov al, [aspect_expr_stage_types+1]
arith_loc_eded:
 sub_load ah,ah
arith_loc_edef:
 push ax
arith_loc_edf0:
 call aspect_operand_is_long
arith_loc_edf3:
 or_load ax,ax
arith_loc_edf5:
 jz arith_loc_ee05
arith_loc_edf7:
 mov ax, [aspect_ops_float_value+10]
arith_loc_edfa:
 or ax, word [aspect_ops_float_value+8]
arith_loc_edfe:
 jnz arith_loc_ee1e
arith_loc_ee00:
 mov si, 0x1
arith_loc_ee03:
 jmp arith_loc_ee1e
arith_loc_ee05:
 mov ax, 0x8
arith_loc_ee08:
 push ax
arith_loc_ee09:
 mov ax, aspect_expr_float_zero
arith_loc_ee0c:
 push ax
arith_loc_ee0d:
 mov ax, aspect_ops_float_value+8
arith_loc_ee10:
 push ax
arith_loc_ee11:
 call aspect_expr_compare
arith_loc_ee14:
 add sp, 0x6
arith_loc_ee17:
 cmp ax, strict word 0x1
arith_loc_ee1a:
 sbb_load si,si
arith_loc_ee1c:
 neg si
arith_loc_ee1e:
 or_load si,si
arith_loc_ee20:
 jnz arith_loc_ee2a
arith_loc_ee22:
 push word [bp + 0x4]
arith_loc_ee25:
 call aspect_ops_float_transform
arith_loc_ee28:
 jmp arith_loc_ee2d
arith_loc_ee2a:
 call aspect_arith_zero_divisor
arith_loc_ee2d:
 or_load si,si
arith_loc_ee2f:
 jnz arith_loc_ee34
arith_loc_ee31:
 call aspect_ops_store_result
arith_loc_ee34:
 pop si
arith_loc_ee35:
 pop di
arith_loc_ee36:
 mov_load sp,bp
arith_loc_ee38:
 pop bp
arith_loc_ee39:
 ret 0x2
aspect_arith_zero_divisor:
 mov ax, 0x2
arith_loc_ee3f:
 push ax
arith_loc_ee40:
 call aspect_arith_error
arith_loc_ee43:
 call aspect_expr_boolean
arith_loc_ee46:
 mov ax, 0x1
arith_loc_ee49:
 ret
