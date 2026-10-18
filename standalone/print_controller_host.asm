; Explicit memory UART/keyboard/CRT/UI fixtures; no real device or file IO.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern print_controller_original
GLOBAL _print_controller_dos_test
_print_controller_dos_test:
 push bp
 push si
 push di
 push es
 call print_controller_original
 cmp word [fixture_wire_count],1
 jne .bad
 cmp byte [fixture_wire],'A'
 jne .bad
 cmp word [fixture_close_calls],1
 jne .bad
 cmp word [fixture_restore_calls],1
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
GLOBAL controller_save,controller_restore
controller_save: inc word [fixture_save_calls]
 ret 6
controller_restore: inc word [fixture_restore_calls]
 ret 6
GLOBAL controller_hide_cursor,controller_status,controller_cursor_shape,controller_break
controller_hide_cursor: inc word [fixture_hide_calls]
 ret
controller_status: inc word [fixture_status_calls]
 ret
controller_cursor_shape: inc word [fixture_shape_calls]
 ret
controller_break: inc word [fixture_break_calls]
 ret
GLOBAL controller_key_available,controller_read_key,controller_send_key
controller_key_available:
 xor ax,ax
 cmp word [fixture_keys_after_rx],0
 je .keys
 cmp word [controller_rx_count],0
 jne .done
.keys:
 mov bx,[fixture_key_index]
 cmp bx,[fixture_key_count]
 jae .done
 inc ax
.done: ret
controller_read_key:
 mov bx,[fixture_key_index]
 shl bx,1
 mov ax,[fixture_keys+bx]
 inc word [fixture_key_index]
 ret
controller_send_key:
 push bp
 mov bp,sp
 push bx
 mov bx,[fixture_sent_count]
 shl bx,1
 mov ax,[bp+4]
 mov [fixture_sent+bx],ax
 inc word [fixture_sent_count]
 pop bx
 pop bp
 ret 2
GLOBAL controller_dequeue,controller_next_byte
controller_next_byte: inc word [fixture_next_calls]
controller_dequeue:
 mov ax,0xffff
 cmp word [controller_rx_count],0
 je .done
 mov bx,[fixture_rx_index]
 xor ax,ax
 mov al,[fixture_rx+bx]
 inc word [fixture_rx_index]
 dec word [controller_rx_count]
.done: ret
GLOBAL printer_open,printer_close,printer_putc,printer_flush
printer_open: inc word [fixture_open_calls]
 mov ax,[fixture_open_result]
 ret
printer_close: inc word [fixture_close_calls]
 mov ax,[fixture_close_result]
 ret
printer_flush: inc word [fixture_flush_calls]
 mov ax,[fixture_flush_result]
 ret
printer_putc:
 push bp
 mov bp,sp
 push bx
 inc word [fixture_putc_calls]
 mov bx,[fixture_wire_count]
 cmp bx,4096
 jae .done
 mov ax,[bp+4]
 mov [fixture_wire+bx],al
 inc word [fixture_wire_count]
.done:
 mov ax,[bp+6]
 mov [fixture_last_handle],ax
 mov ax,[fixture_putc_result]
 pop bx
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
GLOBAL controller_columns
controller_columns: dw 80
GLOBAL controller_cursor_flags
controller_cursor_flags: dw 0
GLOBAL controller_dec_family
controller_dec_family: dw 1
GLOBAL controller_open_mode
controller_open_mode: db 'wb',0
GLOBAL controller_other_family
controller_other_family: dw 0
GLOBAL controller_rows
controller_rows: dw 25
GLOBAL controller_rx_count
controller_rx_count: dw 5
GLOBAL controller_status_text
controller_status_text: db 'DEDICATED PRINT',0
GLOBAL controller_terminal_id
controller_terminal_id: dw 6
GLOBAL fixture_break_calls
fixture_break_calls: dw 0
GLOBAL fixture_close_calls
fixture_close_calls: dw 0
GLOBAL fixture_close_result
fixture_close_result: dw 0
GLOBAL fixture_flush_calls
fixture_flush_calls: dw 0
GLOBAL fixture_flush_result
fixture_flush_result: dw 0
GLOBAL fixture_hide_calls
fixture_hide_calls: dw 0
GLOBAL fixture_key_count
fixture_key_count: dw 0
GLOBAL fixture_key_index
fixture_key_index: dw 0
GLOBAL fixture_keys_after_rx
fixture_keys_after_rx: dw 1
GLOBAL fixture_last_handle
fixture_last_handle: dw 0
GLOBAL fixture_next_calls
fixture_next_calls: dw 0
GLOBAL fixture_open_calls
fixture_open_calls: dw 0
GLOBAL fixture_open_result
fixture_open_result: dw 4369
GLOBAL fixture_putc_calls
fixture_putc_calls: dw 0
GLOBAL fixture_putc_result
fixture_putc_result: dw 0
GLOBAL fixture_restore_calls
fixture_restore_calls: dw 0
GLOBAL fixture_rx_index
fixture_rx_index: dw 0
GLOBAL fixture_save_calls
fixture_save_calls: dw 0
GLOBAL fixture_sent_count
fixture_sent_count: dw 0
GLOBAL fixture_shape_calls
fixture_shape_calls: dw 0
GLOBAL fixture_status_calls
fixture_status_calls: dw 0
GLOBAL fixture_wire_count
fixture_wire_count: dw 0
GLOBAL printer_device
printer_device: db 'PRN',0
GLOBAL printer_stream
printer_stream: dw 0
GLOBAL fixture_rx,fixture_keys,fixture_sent,fixture_wire
fixture_rx: db 'A',27,'[4i'
 times 1019 db 0
fixture_keys: times 64 dw 0
fixture_sent: times 64 dw 0
fixture_wire: times 4096 db 0
