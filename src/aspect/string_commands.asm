; Exact PCPlus2.01 overlay17 string commands EEFF..EF1C and EF42..F0B4.
; Retained anchored17 function listings; original SHA256:
; 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904.
; DS=SS,DF=0, nearRET, BP/SI/DI preserved; others/flags volatile.
; String/operand services RET, store_integer consumes one word(RET2), error
; consumes one word if returning; resident text helpers use caller cleanup.
; Native signed length comparisons and16-bit sums are preserved. Error3 may
; abort before mutation or return into80-byte truncation. Fill/subcopy always
; terminate byte80; set_char does not alter a separate terminator. Helpers and
; raw unchecked indices/counts remain explicit dependencies, not safety claims.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_STRING_COMMANDS_FLAT
%if ASPECT_STRING_COMMANDS_UNIT=1
ORG 0xeeff
%elif ASPECT_STRING_COMMANDS_UNIT=2
ORG 0xef42
%else
%error Select ASPECT_STRING_COMMANDS_UNIT1..2
%endif
%define aspect_string_read 0xdf04
%define aspect_string_read_destination 0xdf0b
%define aspect_string_copy_count 0xeef0
%define aspect_expr_compare 0x9ac0
%define aspect_string_strlen 0x8d18
%define aspect_string_option_flag 0xe0e4
%define aspect_string_length_operand 0xde11
%define aspect_string_error 0x4efb
%define aspect_string_concat 0x9852
%define aspect_string_flush 0xe0a4
%define aspect_string_strncmp 0x9c06
%define aspect_string_strcmp 0x9476
%define aspect_string_store_integer 0xde3a
%define aspect_string_lower 0x9be8
%define aspect_string_index_operand 0xde1c
%define aspect_string_byte_operand 0xdde3
%define aspect_string_fill 0x9736
%define erase_move_bytes 0x85b4
%define aspect_string_upper 0x9128
%define aspect_string_compare_result 0xd124
%else
%define ASPECT_STRING_COMMANDS_UNIT 0
SEGMENT _TEXT public class=CODE use16
global aspect_strcmd_compare_bytes
global aspect_strcmd_concat
global aspect_strcmd_compare
global aspect_strcmd_length
global aspect_strcmd_lower
global aspect_strcmd_get_char
global aspect_strcmd_set_char
global aspect_strcmd_fill
global aspect_strcmd_subcopy
global aspect_strcmd_upper
global aspect_strcmd_substr
extern aspect_string_read
extern aspect_string_read_destination
extern aspect_string_copy_count
extern aspect_expr_compare
extern aspect_string_strlen
extern aspect_string_option_flag
extern aspect_string_length_operand
extern aspect_string_error
extern aspect_string_concat
extern aspect_string_flush
extern aspect_string_strncmp
extern aspect_string_strcmp
extern aspect_string_store_integer
extern aspect_string_lower
extern aspect_string_index_operand
extern aspect_string_byte_operand
extern aspect_string_fill
extern erase_move_bytes
extern aspect_string_upper
extern aspect_string_compare_result
%endif
%if ASPECT_STRING_COMMANDS_UNIT=0 || ASPECT_STRING_COMMANDS_UNIT=1
aspect_strcmd_compare_bytes:
 push di
strcmd_loc_ef00:
 push si
strcmd_loc_ef01:
 call aspect_string_read
strcmd_loc_ef04:
 mov_load di,ax
strcmd_loc_ef06:
 call aspect_string_read
strcmd_loc_ef09:
 mov_load si,ax
strcmd_loc_ef0b:
 call aspect_string_copy_count
strcmd_loc_ef0e:
 push ax
strcmd_loc_ef0f:
 push si
strcmd_loc_ef10:
 push di
strcmd_loc_ef11:
 call aspect_expr_compare
strcmd_loc_ef14:
 add sp, 0x6
strcmd_loc_ef17:
 mov [aspect_string_compare_result], ax
strcmd_loc_ef1a:
 pop si
strcmd_loc_ef1b:
 pop di
strcmd_loc_ef1c:
 ret
%endif
%if ASPECT_STRING_COMMANDS_UNIT=0 || ASPECT_STRING_COMMANDS_UNIT=2
aspect_strcmd_concat:
 push bp
strcmd_loc_ef43:
 mov_load bp,sp
strcmd_loc_ef45:
 sub sp, 0x4
strcmd_loc_ef48:
 push di
strcmd_loc_ef49:
 push si
strcmd_loc_ef4a:
 call aspect_string_read_destination
strcmd_loc_ef4d:
 mov_load si,ax
strcmd_loc_ef4f:
 call aspect_string_read
strcmd_loc_ef52:
 mov_load di,ax
strcmd_loc_ef54:
 push si
strcmd_loc_ef55:
 call aspect_string_strlen
strcmd_loc_ef58:
 pop bx
strcmd_loc_ef59:
 mov word [bp - 0x2], ax
strcmd_loc_ef5c:
 call aspect_string_option_flag
strcmd_loc_ef5f:
 or_load ax,ax
strcmd_loc_ef61:
 jz strcmd_loc_ef68
strcmd_loc_ef63:
 call aspect_string_length_operand
strcmd_loc_ef66:
 jmp strcmd_loc_ef6d
strcmd_loc_ef68:
 push di
strcmd_loc_ef69:
 call aspect_string_strlen
strcmd_loc_ef6c:
 pop bx
strcmd_loc_ef6d:
 mov word [bp - 0x4], ax
strcmd_loc_ef70:
 add ax, word [bp - 0x2]
strcmd_loc_ef73:
 cmp ax, strict word 0x50
strcmd_loc_ef76:
 jle strcmd_loc_ef88
strcmd_loc_ef78:
 mov ax, 0x50
strcmd_loc_ef7b:
 sub ax, word [bp - 0x2]
strcmd_loc_ef7e:
 mov word [bp - 0x4], ax
strcmd_loc_ef81:
 mov ax, 0x3
strcmd_loc_ef84:
 push ax
strcmd_loc_ef85:
 call aspect_string_error
strcmd_loc_ef88:
 push word [bp - 0x4]
strcmd_loc_ef8b:
 push di
strcmd_loc_ef8c:
 push si
strcmd_loc_ef8d:
 call aspect_string_concat
strcmd_loc_ef90:
 add sp, 0x6
strcmd_loc_ef93:
 call aspect_string_flush
strcmd_loc_ef96:
 pop si
strcmd_loc_ef97:
 pop di
strcmd_loc_ef98:
 mov_load sp,bp
strcmd_loc_ef9a:
 pop bp
strcmd_loc_ef9b:
 ret
aspect_strcmd_compare:
 push di
strcmd_loc_ef9d:
 push si
strcmd_loc_ef9e:
 call aspect_string_read
strcmd_loc_efa1:
 mov_load di,ax
strcmd_loc_efa3:
 call aspect_string_read
strcmd_loc_efa6:
 mov_load si,ax
strcmd_loc_efa8:
 call aspect_string_option_flag
strcmd_loc_efab:
 or_load ax,ax
strcmd_loc_efad:
 jz strcmd_loc_efbd
strcmd_loc_efaf:
 call aspect_string_length_operand
strcmd_loc_efb2:
 push ax
strcmd_loc_efb3:
 push si
strcmd_loc_efb4:
 push di
strcmd_loc_efb5:
 call aspect_string_strncmp
strcmd_loc_efb8:
 add sp, 0x6
strcmd_loc_efbb:
 jmp strcmd_loc_efc4
strcmd_loc_efbd:
 push si
strcmd_loc_efbe:
 push di
strcmd_loc_efbf:
 call aspect_string_strcmp
strcmd_loc_efc2:
 pop bx
strcmd_loc_efc3:
 pop bx
strcmd_loc_efc4:
 mov [aspect_string_compare_result], ax
strcmd_loc_efc7:
 pop si
strcmd_loc_efc8:
 pop di
strcmd_loc_efc9:
 ret
aspect_strcmd_length:
 call aspect_string_read
strcmd_loc_efcd:
 push ax
strcmd_loc_efce:
 call aspect_string_strlen
strcmd_loc_efd1:
 pop bx
strcmd_loc_efd2:
 push ax
strcmd_loc_efd3:
 call aspect_string_store_integer
strcmd_loc_efd6:
 ret
aspect_strcmd_lower:
 call aspect_string_read_destination
strcmd_loc_efda:
 push ax
strcmd_loc_efdb:
 call aspect_string_lower
strcmd_loc_efde:
 pop bx
strcmd_loc_efdf:
 call aspect_string_flush
strcmd_loc_efe2:
 ret
aspect_strcmd_get_char:
 push si
strcmd_loc_efe4:
 call aspect_string_read
strcmd_loc_efe7:
 mov_load si,ax
strcmd_loc_efe9:
 call aspect_string_index_operand
strcmd_loc_efec:
 mov_load bx,ax
strcmd_loc_efee:
 mov al, byte [bx + si]
strcmd_loc_eff0:
 sub_load ah,ah
strcmd_loc_eff2:
 push ax
strcmd_loc_eff3:
 call aspect_string_store_integer
strcmd_loc_eff6:
 pop si
strcmd_loc_eff7:
 ret
aspect_strcmd_set_char:
 push si
strcmd_loc_eff9:
 call aspect_string_read_destination
strcmd_loc_effc:
 mov_load si,ax
strcmd_loc_effe:
 call aspect_string_index_operand
strcmd_loc_f001:
 add_load si,ax
strcmd_loc_f003:
 call aspect_string_byte_operand
strcmd_loc_f006:
 mov byte [si], al
strcmd_loc_f008:
 call aspect_string_flush
strcmd_loc_f00b:
 pop si
strcmd_loc_f00c:
 ret
aspect_strcmd_fill:
 push di
strcmd_loc_f00e:
 push si
strcmd_loc_f00f:
 call aspect_string_read_destination
strcmd_loc_f012:
 mov_load si,ax
strcmd_loc_f014:
 call aspect_string_byte_operand
strcmd_loc_f017:
 mov_load di,ax
strcmd_loc_f019:
 call aspect_string_copy_count
strcmd_loc_f01c:
 push ax
strcmd_loc_f01d:
 push di
strcmd_loc_f01e:
 push si
strcmd_loc_f01f:
 call aspect_string_fill
strcmd_loc_f022:
 add sp, 0x6
strcmd_loc_f025:
 mov byte [si + 0x50], 0x0
strcmd_loc_f029:
 call aspect_string_flush
strcmd_loc_f02c:
 pop si
strcmd_loc_f02d:
 pop di
strcmd_loc_f02e:
 ret
aspect_strcmd_subcopy:
 push bp
strcmd_loc_f030:
 mov_load bp,sp
strcmd_loc_f032:
 sub sp, 0x4
strcmd_loc_f035:
 push di
strcmd_loc_f036:
 push si
strcmd_loc_f037:
 call aspect_string_read_destination
strcmd_loc_f03a:
 mov_load di,ax
strcmd_loc_f03c:
 call aspect_string_read
strcmd_loc_f03f:
 mov word [bp - 0x4], ax
strcmd_loc_f042:
 call aspect_string_index_operand
strcmd_loc_f045:
 mov_load si,ax
strcmd_loc_f047:
 call aspect_string_length_operand
strcmd_loc_f04a:
 mov word [bp - 0x2], ax
strcmd_loc_f04d:
 add_load ax,si
strcmd_loc_f04f:
 cmp ax, strict word 0x50
strcmd_loc_f052:
 jle strcmd_loc_f063
strcmd_loc_f054:
 mov ax, 0x50
strcmd_loc_f057:
 sub_load ax,si
strcmd_loc_f059:
 mov word [bp - 0x2], ax
strcmd_loc_f05c:
 mov ax, 0x3
strcmd_loc_f05f:
 push ax
strcmd_loc_f060:
 call aspect_string_error
strcmd_loc_f063:
 push word [bp - 0x2]
strcmd_loc_f066:
 push word [bp - 0x4]
strcmd_loc_f069:
 add_load si,di
strcmd_loc_f06b:
 push si
strcmd_loc_f06c:
 call erase_move_bytes
strcmd_loc_f06f:
 add sp, 0x6
strcmd_loc_f072:
 mov byte [di + 0x50], 0x0
strcmd_loc_f076:
 call aspect_string_flush
strcmd_loc_f079:
 pop si
strcmd_loc_f07a:
 pop di
strcmd_loc_f07b:
 mov_load sp,bp
strcmd_loc_f07d:
 pop bp
strcmd_loc_f07e:
 ret
aspect_strcmd_upper:
 call aspect_string_read_destination
strcmd_loc_f082:
 push ax
strcmd_loc_f083:
 call aspect_string_upper
strcmd_loc_f086:
 pop bx
strcmd_loc_f087:
 call aspect_string_flush
strcmd_loc_f08a:
 ret
aspect_strcmd_substr:
 push di
 push si
 call aspect_string_read_destination
 mov_load di,ax
 call aspect_string_read
 mov_load si,ax
 call aspect_string_index_operand
 add_load si,ax
 call aspect_string_length_operand
 push ax
 push si
 push di
 mov_load si,ax
 call erase_move_bytes
 add sp,byte 6
 add_load di,si
 mov byte [di],0
 call aspect_string_flush
 pop si
 pop di
 ret
%endif
