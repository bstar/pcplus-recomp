; Native ASPECT file commands, not yet linked to the maintained application.
; Six slots and native FILE/error semantics require the matching owner backend.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_SCRIPT_FILE_FLAT
%if ASPECT_SCRIPT_FILE_UNIT=1
ORG 0xeb0a
%elif ASPECT_SCRIPT_FILE_UNIT=2
ORG 0xeb14
%elif ASPECT_SCRIPT_FILE_UNIT=3
ORG 0xeb2c
%elif ASPECT_SCRIPT_FILE_UNIT=4
ORG 0xeb3d
%elif ASPECT_SCRIPT_FILE_UNIT=5
ORG 0xeb52
%elif ASPECT_SCRIPT_FILE_UNIT=6
ORG 0xebce
%elif ASPECT_SCRIPT_FILE_UNIT=7
ORG 0xec25
%elif ASPECT_SCRIPT_FILE_UNIT=8
ORG 0xec3b
%elif ASPECT_SCRIPT_FILE_UNIT=9
ORG 0xec51
%elif ASPECT_SCRIPT_FILE_UNIT=10
ORG 0xec99
%elif ASPECT_SCRIPT_FILE_UNIT=11
ORG 0xec80
%elif ASPECT_SCRIPT_FILE_UNIT=12
ORG 0xecce
%elif ASPECT_SCRIPT_FILE_UNIT=13
ORG 0xeafa
%endif
%define aspect_script_file_lookup 0xd956
%define aspect_script_file_number 0xd97a
%define aspect_script_file_status 0xd943
%define aspect_script_file_slots 0xe39e
%define aspect_script_file_last 0xe3aa
%define aspect_script_file_keep_crlf 0xe388
%define aspect_script_file_mode_flags 0x7b2b
%define aspect_script_file_mode_scratch 0x4b06
%define aspect_string_compare_result 0xd124
%define script_file_crt_close 0x8318
%define script_file_crt_flush 0x8c54
%define script_file_crt_getc 0x998a
%define script_file_crt_gets 0x99a8
%define script_file_crt_putc 0x8436
%define script_file_crt_puts 0x8e88
%define script_file_crt_open 0x841a
%define script_file_crt_read 0x845a
%define script_file_crt_seek 0x853a
%define script_file_crt_tell 0x8ed8
%define script_file_crt_write 0x86ac
%define aspect_string_read 0xdf04
%define aspect_string_read_destination 0xdf0b
%define aspect_string_flush 0xe0a4
%define aspect_string_byte_operand 0xdde3
%define aspect_string_length_operand 0xde11
%define aspect_string_store_integer 0xde3a
%define aspect_operand_read_long 0xdcc1
%define aspect_expr_long_address 0xde92
%define aspect_string_bounded_integer 0xdd68
%define script_file_strcpy 0x8268
%define script_file_strlwr 0x9be8
%define script_file_strlen 0x8d18
%else
%define ASPECT_SCRIPT_FILE_UNIT 0
%define aspect_script_file_slots _runtime_script_file_slots
%define aspect_script_file_last _runtime_script_file_last
%define aspect_script_file_keep_crlf _runtime_script_file_keep_crlf
%define aspect_script_file_mode_flags _runtime_script_file_mode_flags
%define aspect_script_file_mode_scratch _runtime_script_file_mode_pointer
SEGMENT _TEXT public class=CODE use16
global aspect_script_file_clear,aspect_script_file_close,aspect_script_file_flush
global aspect_script_file_getc,aspect_script_file_gets,aspect_script_file_open
global aspect_script_file_putc,aspect_script_file_puts,aspect_script_file_read
global aspect_script_file_seek,aspect_script_file_tell,aspect_script_file_write
global aspect_script_file_eof
extern aspect_script_file_lookup,aspect_script_file_number,aspect_script_file_status
extern aspect_script_file_slots,aspect_script_file_last,aspect_script_file_keep_crlf
extern aspect_script_file_mode_flags,aspect_script_file_mode_scratch,aspect_string_compare_result
extern script_file_crt_close,script_file_crt_flush,script_file_crt_getc,script_file_crt_gets
extern script_file_crt_putc,script_file_crt_puts,script_file_crt_open,script_file_crt_read
extern script_file_crt_seek,script_file_crt_tell,script_file_crt_write
extern aspect_string_read,aspect_string_read_destination,aspect_string_flush
extern aspect_string_byte_operand,aspect_string_length_operand,aspect_string_store_integer
extern aspect_operand_read_long,aspect_expr_long_address,aspect_string_bounded_integer
extern script_file_strcpy,script_file_strlwr,script_file_strlen
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=13
aspect_script_file_eof:
 call aspect_script_file_lookup
 mov_load bx,ax
 mov al,[bx+6]
 and ax,strict word 0x10
 push ax
 call aspect_string_store_integer
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=1
aspect_script_file_clear:
 call aspect_script_file_lookup
 mov_load bx,ax
 and byte [bx+6],0xcf
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=2
aspect_script_file_close:
 call aspect_script_file_lookup
 push ax
 call script_file_crt_close
 pop bx
 mov [aspect_string_compare_result],ax
 mov bx,[aspect_script_file_last]
 shl bx,1
 mov word [bx+aspect_script_file_slots],0
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=3
aspect_script_file_flush:
 push si
 call aspect_script_file_lookup
 push ax
 mov_load si,ax
 call script_file_crt_flush
 pop bx
 push si
 call aspect_script_file_status
 pop si
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=4
aspect_script_file_getc:
 push si
 call aspect_script_file_lookup
 push ax
 mov_load si,ax
 call script_file_crt_getc
 pop bx
 push ax
 call aspect_string_store_integer
 push si
 call aspect_script_file_status
 pop si
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=5
aspect_script_file_gets:
 push bp
 mov_load bp,sp
 sub sp,4
 push di
 push si
 call aspect_script_file_lookup
 mov_load di,ax
 push di
 mov ax,0x51
 push ax
 call aspect_string_read_destination
 mov_load si,ax
 push si
 call script_file_crt_gets
 add sp,6
 or_load ax,ax
 jz .terminate
 cmp word [aspect_script_file_keep_crlf],0
 jnz .status
 cmp byte [si],0
 je .status
 push si
 call script_file_strlen
 pop bx
 mov [bp-2],ax
 dec ax
 add_load si,ax
 mov bl,[di+7]
 sub_load bh,bh
 mov al,[bx+aspect_script_file_mode_flags]
 and ax,0x80
 cmp byte [si],0x0a
 jne .control_z
 or_load ax,ax
 jnz .terminate
 cmp word [bp-2],2
 jl .terminate
 cmp byte [si-1],0x0d
 jne .terminate
 dec si
 jmp short .terminate
.control_z:
 or_load ax,ax
 jnz .status
 cmp byte [si],0x1a
 jne .status
 test byte [di+6],0x10
 jz .status
.terminate:
 mov byte [si],0
.status:
 push di
 call aspect_script_file_status
 call aspect_string_flush
 pop si
 pop di
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=6
aspect_script_file_open:
 push di
 push si
 call aspect_script_file_number
 mov_load si,ax
 mov_load bx,si
 shl bx,1
 cmp word [bx+aspect_script_file_slots],0
 je .path
 mov_load bx,si
 shl bx,1
 push word [bx+aspect_script_file_slots]
 call script_file_crt_close
 pop bx
.path:
 call aspect_string_read
 mov_load di,ax
 call aspect_string_read
 push ax
 push word [aspect_script_file_mode_scratch]
 call script_file_strcpy
 pop bx
 pop bx
 push word [aspect_script_file_mode_scratch]
 call script_file_strlwr
 pop bx
 push word [aspect_script_file_mode_scratch]
 push di
 call script_file_crt_open
 pop bx
 pop bx
 mov_load bx,si
 shl bx,1
 mov [bx+aspect_script_file_slots],ax
 cmp ax,strict word 1
 sbb_load ax,ax
 neg ax
 mov [aspect_string_compare_result],ax
 pop si
 pop di
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=7
aspect_script_file_putc:
 push si
 call aspect_script_file_lookup
 mov_load si,ax
 push si
 call aspect_string_byte_operand
 push ax
 call script_file_crt_putc
 pop bx
 pop bx
 push si
 call aspect_script_file_status
 pop si
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=8
aspect_script_file_puts:
 push si
 call aspect_script_file_lookup
 mov_load si,ax
 push si
 call aspect_string_read
 push ax
 call script_file_crt_puts
 pop bx
 pop bx
 push si
 call aspect_script_file_status
 pop si
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=9
aspect_script_file_read:
 push di
 push si
 call aspect_script_file_lookup
 mov_load si,ax
 call aspect_string_read_destination
 mov_load di,ax
 push si
 call aspect_string_length_operand
 push ax
 mov ax,1
 push ax
 push di
 call script_file_crt_read
 add sp,8
 mov_load bx,ax
 mov byte [bx+di],0
 push bx
 call aspect_string_store_integer
 push si
 call aspect_script_file_status
 call aspect_string_flush
 pop si
 pop di
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=10
aspect_script_file_seek:
 push bp
 mov_load bp,sp
 sub sp,4
 push si
 call aspect_script_file_lookup
 mov_load si,ax
 call aspect_operand_read_long
 mov [bp-4],ax
 mov [bp-2],dx
 sub_load ax,ax
 push ax
 mov ax,2
 push ax
 call aspect_string_bounded_integer
 push ax
 push word [bp-2]
 push word [bp-4]
 push si
 call script_file_crt_seek
 add sp,8
 mov [aspect_string_compare_result],ax
 pop si
 mov_load sp,bp
 pop bp
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=11
aspect_script_file_tell:
 push di
 push si
 call aspect_script_file_lookup
 mov_load di,ax
 call aspect_expr_long_address
 mov_load si,ax
 push di
 call script_file_crt_tell
 pop bx
 mov [si],ax
 mov [si+2],dx
 pop si
 pop di
 ret
%endif
%if ASPECT_SCRIPT_FILE_UNIT=0 || ASPECT_SCRIPT_FILE_UNIT=12
aspect_script_file_write:
 push di
 push si
 call aspect_script_file_lookup
 mov_load si,ax
 call aspect_string_read
 mov_load di,ax
 push si
 call aspect_string_length_operand
 push ax
 mov ax,1
 push ax
 push di
 call script_file_crt_write
 add sp,8
 push si
 call aspect_script_file_status
 pop si
 pop di
 ret
%endif
