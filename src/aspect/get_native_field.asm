; Maintained adapter to GET's recovered14-byte callee-clean field ABI.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _runtime_get_native_field
extern aspect_get_numeric_filter,aspect_get_string_filter,runtime_get_abort_gate
global aspect_get_field,_runtime_get_numeric_filter,_runtime_get_string_filter
global _runtime_get_field_abort
_runtime_get_numeric_filter: mov ax,aspect_get_numeric_filter
 ret
_runtime_get_string_filter: mov ax,aspect_get_string_filter
 ret
_runtime_get_field_abort: jmp runtime_get_abort_gate
aspect_get_field:
 push bp
 mov bp,sp
 push word [bp+16]
 push word [bp+14]
 push word [bp+12]
 push word [bp+10]
 push word [bp+8]
 push word [bp+6]
 push word [bp+4]
 call _runtime_get_native_field
 add sp,14
 pop bp
 ret 14
