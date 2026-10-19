; Exact PCPlus2.01 overlay17 numeric conversion commands and numeric scanner.
; Anchored17 listings; original SHA256
; 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; Units EA4B..EAE0 and EAF4..EB37. Scanner takes (flag,string) RET4;
; flag permits .digit when nonzero, digit and -digit always accepted. It uses
; strcspn against '-.0123456789' then the digit bit4 of the ctype table.
; Commands are nearRET; DS=SS,DF=0, BP/SI/DI preserved. CRT calls cdecl;
; integer store RET2. No bounds, overflow, invalid selector, or radix guards.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_CONVERSIONS_FLAT
%if ASPECT_CONVERSIONS_UNIT=1
ORG 0xea4b
%elif ASPECT_CONVERSIONS_UNIT=2
ORG 0xeaf4
%else
%error Select ASPECT_CONVERSIONS_UNIT1..2
%endif
%define aspect_string_read 0xdf04
%define aspect_string_read_destination 0xdf0b
%define aspect_string_flush 0xe0a4
%define aspect_operand_read_integer 0xdc48
%define aspect_operand_read_long 0xdcc1
%define aspect_string_store_integer 0xde3a
%define aspect_expr_long_address 0xde92
%define aspect_conversion_atoi 0x984e
%define aspect_conversion_atol 0x9b32
%define aspect_conversion_strcspn 0x9b36
%define aspect_conversion_itoa 0x8e6c
%define aspect_conversion_ltoa 0x9ae8
%define aspect_convert_candidate_chars 0x776c
%define aspect_convert_ctype 0x7caf
%else
%define ASPECT_CONVERSIONS_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_convert_atoi
global aspect_convert_atol
global aspect_convert_scan_numeric
global aspect_convert_itoa
global aspect_convert_ltoa
extern aspect_string_read
extern aspect_string_read_destination
extern aspect_string_flush
extern aspect_operand_read_integer
extern aspect_operand_read_long
extern aspect_string_store_integer
extern aspect_expr_long_address
extern aspect_conversion_atoi
extern aspect_conversion_atol
extern aspect_conversion_strcspn
extern aspect_conversion_itoa
extern aspect_conversion_ltoa
extern aspect_convert_candidate_chars
extern aspect_convert_ctype
%endif
%if ASPECT_CONVERSIONS_UNIT=0 || ASPECT_CONVERSIONS_UNIT=1
; REA ev_ad5780901f002295322b66c988bd131a1510b0614236450284cdb90dc92e7058
aspect_convert_atoi:
convert_loc_ea4b:
 call aspect_string_read
convert_loc_ea4e:
 push ax
convert_loc_ea4f:
 sub_load ax, ax
convert_loc_ea51:
 push ax
convert_loc_ea52:
 call aspect_convert_scan_numeric
convert_loc_ea55:
 push ax
convert_loc_ea56:
 call aspect_conversion_atoi
convert_loc_ea59:
 pop bx
convert_loc_ea5a:
 push ax
convert_loc_ea5b:
 call aspect_string_store_integer
convert_loc_ea5e:
 ret
; REA ev_fcf5da5ba6426d3fe2d964dcbffb972f0882b580bf22b4ef4912ec7f1b7768ab
aspect_convert_atol:
convert_loc_ea5f:
 push di
convert_loc_ea60:
 push si
convert_loc_ea61:
 call aspect_string_read
convert_loc_ea64:
 mov_load di, ax
convert_loc_ea66:
 call aspect_expr_long_address
convert_loc_ea69:
 mov_load si, ax
convert_loc_ea6b:
 push di
convert_loc_ea6c:
 sub_load ax, ax
convert_loc_ea6e:
 push ax
convert_loc_ea6f:
 call aspect_convert_scan_numeric
convert_loc_ea72:
 push ax
convert_loc_ea73:
 call aspect_conversion_atol
convert_loc_ea76:
 pop bx
convert_loc_ea77:
 mov word [si], ax
convert_loc_ea79:
 mov word [si + 0x2], dx
convert_loc_ea7c:
 pop si
convert_loc_ea7d:
 pop di
convert_loc_ea7e:
 ret
; REA ev_4640c640e5f00a7ab2f90e94140fe39a9591bbd3ee3efa37aac8731a25a0fa15
aspect_convert_scan_numeric:
convert_loc_ea7f:
 push bp
convert_loc_ea80:
 mov_load bp, sp
convert_loc_ea82:
 push di
convert_loc_ea83:
 push si
convert_loc_ea84:
 mov si, word [bp + 0x6]
convert_loc_ea87:
 jmp convert_loc_ead2
convert_loc_ea89:
 mov ax, aspect_convert_candidate_chars
convert_loc_ea8c:
 push ax
convert_loc_ea8d:
 push si
convert_loc_ea8e:
 call aspect_conversion_strcspn
convert_loc_ea91:
 pop bx
convert_loc_ea92:
 pop bx
convert_loc_ea93:
 mov_load di, ax
convert_loc_ea95:
 add_load si, di
convert_loc_ea97:
 mov bl, byte [si]
convert_loc_ea99:
 sub_load bh, bh
convert_loc_ea9b:
 test byte [bx + aspect_convert_ctype], 0x4
convert_loc_eaa0:
 jnz convert_loc_ead7
convert_loc_eaa2:
 cmp bl, 0x2d
convert_loc_eaa5:
 jnz convert_loc_eab1
convert_loc_eaa7:
 mov bl, byte [si + 0x1]
convert_loc_eaaa:
 test byte [bx + aspect_convert_ctype], 0x4
convert_loc_eaaf:
 jnz convert_loc_ead7
convert_loc_eab1:
 cmp byte [si], 0x2e
convert_loc_eab4:
 jnz convert_loc_eac8
convert_loc_eab6:
 cmp word [bp + 0x4], 0x0
convert_loc_eaba:
 jz convert_loc_eac8
convert_loc_eabc:
 mov bl, byte [si + 0x1]
convert_loc_eabf:
 sub_load bh, bh
convert_loc_eac1:
 test byte [bx + aspect_convert_ctype], 0x4
convert_loc_eac6:
 jnz convert_loc_ead7
convert_loc_eac8:
 or_load di, di
convert_loc_eaca:
 jnz convert_loc_ead2
convert_loc_eacc:
 cmp byte [si], 0x0
convert_loc_eacf:
 jz convert_loc_ead2
convert_loc_ead1:
 inc si
convert_loc_ead2:
 cmp byte [si], 0x0
convert_loc_ead5:
 jnz convert_loc_ea89
convert_loc_ead7:
 mov_load ax, si
convert_loc_ead9:
 pop si
convert_loc_eada:
 pop di
convert_loc_eadb:
 mov_load sp, bp
convert_loc_eadd:
 pop bp
convert_loc_eade:
 ret 0x4
%endif
%if ASPECT_CONVERSIONS_UNIT=0 || ASPECT_CONVERSIONS_UNIT=2
; REA ev_06a1de6cc8e7b6043743c6076b85a7c4aedd410689906f89c21dcd6398aa7326
aspect_convert_itoa:
convert_loc_eaf4:
 push si
convert_loc_eaf5:
 call aspect_operand_read_integer
convert_loc_eaf8:
 mov_load si, ax
convert_loc_eafa:
 mov ax, 0xa
convert_loc_eafd:
 push ax
convert_loc_eafe:
 call aspect_string_read_destination
convert_loc_eb01:
 push ax
convert_loc_eb02:
 push si
convert_loc_eb03:
 call aspect_conversion_itoa
convert_loc_eb06:
 add sp, 0x6
convert_loc_eb09:
 call aspect_string_flush
convert_loc_eb0c:
 pop si
convert_loc_eb0d:
 ret
; REA ev_7aeb132918bb0ec59f72f7dc5541de4d02aa1c1fe2ce672a25bdce970ec92c09
aspect_convert_ltoa:
convert_loc_eb0e:
 push bp
convert_loc_eb0f:
 mov_load bp, sp
convert_loc_eb11:
 sub sp, 0x4
convert_loc_eb14:
 call aspect_operand_read_long
convert_loc_eb17:
 mov word [bp + -0x4], ax
convert_loc_eb1a:
 mov word [bp + -0x2], dx
convert_loc_eb1d:
 mov ax, 0xa
convert_loc_eb20:
 push ax
convert_loc_eb21:
 call aspect_string_read_destination
convert_loc_eb24:
 push ax
convert_loc_eb25:
 push word [bp + -0x2]
convert_loc_eb28:
 push word [bp + -0x4]
convert_loc_eb2b:
 call aspect_conversion_ltoa
convert_loc_eb2e:
 add sp, 0x8
convert_loc_eb31:
 call aspect_string_flush
convert_loc_eb34:
 mov_load sp, bp
convert_loc_eb36:
 pop bp
convert_loc_eb37:
 ret
%endif
