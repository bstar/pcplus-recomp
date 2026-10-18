; Source-only diagnostic: CRT/cursor/status boundaries are memory fixtures.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern print_screen_original
GLOBAL _print_screen_dos_test
_print_screen_dos_test:
 push bp
 push si
 push di
 push es
 mov ax,3
 push ax
 call print_screen_original
 add sp,2
 cmp word [fixture_wire_count],6
 jne .bad
 cmp word [fixture_close_calls],1
 jne .bad
 cmp word [fixture_flush_calls],1
 jne .bad
 xor ax,ax
 jmp .done
.bad: mov ax,1
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
GLOBAL print_set_cursor
print_set_cursor:
 mov [print_cursor_row],ax
 mov [print_cursor_column],dx
 push ax
 push dx
 mov bx,8
 mul bx
 pop dx
 mov bx,dx
 shl bx,1
 add ax,bx
 mov [print_video_offset],ax
 pop ax
 ret
GLOBAL print_copy_fallback,print_status_message,printer_status
print_copy_fallback: inc word [fixture_fallback_calls]
 ret
print_status_message: inc word [fixture_message_calls]
 ret
printer_status: inc word [fixture_status_calls]
 ret
GLOBAL printer_open,printer_close,printer_putc,printer_flush
printer_open:
 inc word [fixture_open_calls]
 mov ax,[fixture_open_result]
 ret
printer_close:
 push bp
 mov bp,sp
 mov ax,[bp+4]
 mov [fixture_closed_handle],ax
 pop bp
 inc word [fixture_close_calls]
 mov ax,[fixture_close_result]
 ret
printer_flush:
 inc word [fixture_flush_calls]
 mov ax,[fixture_flush_result]
 ret
printer_putc:
 push bp
 mov bp,sp
 push bx
 cmp word [fixture_close_calls],0
 je .not_closed
 inc word [fixture_putc_after_close]
.not_closed:
 inc word [fixture_putc_calls]
 mov ax,[bp+4]
 mov bx,[fixture_wire_count]
 cmp bx,4096
 jae .skip
 mov [fixture_wire+bx],al
 inc word [fixture_wire_count]
.skip:
 mov ax,[bp+6]
 mov [fixture_last_handle],ax
 mov ax,[fixture_putc_result]
 pop bx
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
GLOBAL fixture_close_calls
fixture_close_calls: dw 0
GLOBAL fixture_close_result
fixture_close_result: dw 0
GLOBAL fixture_fallback_calls
fixture_fallback_calls: dw 0
GLOBAL fixture_flush_calls
fixture_flush_calls: dw 0
GLOBAL fixture_flush_result
fixture_flush_result: dw 0
GLOBAL fixture_last_handle
fixture_last_handle: dw 0
GLOBAL fixture_message_calls
fixture_message_calls: dw 0
GLOBAL fixture_open_calls
fixture_open_calls: dw 0
GLOBAL fixture_open_result
fixture_open_result: dw 4369
GLOBAL fixture_putc_calls
fixture_putc_calls: dw 0
GLOBAL fixture_putc_result
fixture_putc_result: dw 0
GLOBAL fixture_status_calls
fixture_status_calls: dw 0
GLOBAL fixture_wire_count
fixture_wire_count: dw 0
GLOBAL print_copy_policy
print_copy_policy: dw 0
GLOBAL print_cursor_column
print_cursor_column: dw 2
GLOBAL print_cursor_row
print_cursor_row: dw 1
GLOBAL print_formfeed
print_formfeed: dw 0
GLOBAL print_last_column
print_last_column: dw 3
GLOBAL print_parameter_count
print_parameter_count: dw 0
GLOBAL print_parameters
print_parameters: times 16 dw 0
GLOBAL print_region_bottom
print_region_bottom: dw 2
GLOBAL print_region_mode
print_region_mode: dw 0
GLOBAL print_region_top
print_region_top: dw 1
GLOBAL print_row_limit
print_row_limit: dw 3
GLOBAL print_status_text
print_status_text: db 'Print',0
GLOBAL print_text_mode
print_text_mode: db 'wb',0
GLOBAL print_video_offset
print_video_offset: dw 0
GLOBAL printer_binary_mode
printer_binary_mode: db 'wb',0
GLOBAL printer_device
printer_device: db 'PRN',0
GLOBAL printer_enabled
printer_enabled: dw 0
GLOBAL printer_stream
printer_stream: dw 0
GLOBAL text_cga_status_port
text_cga_status_port: dw 0
GLOBAL text_video_segment
text_video_segment: dw 47104
GLOBAL fixture_wire
fixture_wire: times 4096 db 0
GLOBAL fixture_putc_after_close,fixture_closed_handle
fixture_putc_after_close: dw 0
fixture_closed_handle: dw 0
