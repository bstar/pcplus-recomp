; Test-only typed operand/error/writeback boundaries. No filesystem substitute.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_script_file_clear,aspect_script_file_close,aspect_script_file_flush
extern aspect_script_file_getc,aspect_script_file_gets,aspect_script_file_open
extern aspect_script_file_putc,aspect_script_file_puts,aspect_script_file_read
extern aspect_script_file_seek,aspect_script_file_tell,aspect_script_file_write,aspect_script_file_eof
extern _test_slot,_test_origin,_test_count,_test_byte,_test_position,_test_long_value
extern _test_integer,_test_buffer,_test_strings,_test_string_at,_test_flushes,_test_warnings
extern _test_ascii_lower,_runtime_error
global _script_file_call
_script_file_call:
 push bp
 mov bp,sp
 push si
 push di
 mov bx,[bp+4]
 shl bx,1
 call word [cs:operations+bx]
 pop di
 pop si
 pop bp
 ret
operations:
 dw aspect_script_file_clear,aspect_script_file_close,aspect_script_file_flush
 dw aspect_script_file_getc,aspect_script_file_gets,aspect_script_file_open
 dw aspect_script_file_putc,aspect_script_file_puts,aspect_script_file_read
 dw aspect_script_file_seek,aspect_script_file_tell,aspect_script_file_write,aspect_script_file_eof
global aspect_string_bounded_integer,aspect_string_read,aspect_string_read_destination
global aspect_string_flush,aspect_string_byte_operand,aspect_string_length_operand
global aspect_string_store_integer,aspect_operand_read_long,aspect_expr_long_address
global aspect_string_lower,aspect_string_error
aspect_string_bounded_integer:
 push bp
 mov bp,sp
 mov ax,[_test_slot]
 cmp word [bp+4],2
 jne .done
 mov ax,[_test_origin]
.done:
 pop bp
 ret 4
aspect_string_read:
 mov bx,[_test_string_at]
 shl bx,1
 mov ax,[_test_strings+bx]
 inc word [_test_string_at]
 ret
aspect_string_read_destination: mov ax,[_test_buffer]
 ret
aspect_string_flush: inc word [_test_flushes]
 ret
aspect_string_byte_operand: mov ax,[_test_byte]
 ret
aspect_string_length_operand: mov ax,[_test_count]
 ret
aspect_string_store_integer:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [_test_integer],ax
 pop bp
 ret 2
aspect_operand_read_long:
 mov ax,[_test_position]
 mov dx,[_test_position+2]
 ret
aspect_expr_long_address: mov ax,_test_long_value
 ret
aspect_string_lower: jmp _test_ascii_lower
aspect_string_error:
 inc word [_test_warnings]
 mov word [_runtime_error],7
 ret 2
SEGMENT _DATA public class=DATA use16
global aspect_string_compare_result,_test_comparison,aspect_string_check_range
aspect_string_compare_result:
_test_comparison: dw 0
aspect_string_check_range: dw 1
