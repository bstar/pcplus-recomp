; Near cdecl bridge to serviced physical UART. No native BP frame inspection,
; synthetic transport, DOS IO from callbacks or pending native unwind context.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_transfer_timed_byte,terminal_transfer_service,terminal_transfer_fault
extern terminal_transfer_accepted_progress,terminal_transfer_ui_progress
extern transfer_emit,transfer_protocol_started
extern uart_rx_buffer,uart_rx_read,uart_rx_count
GLOBAL _ymodem_io_read,_ymodem_io_put,_ymodem_io_poll,_ymodem_io_progress
GLOBAL _ymodem_io_unread
_ymodem_io_read:
 push bp
 mov bp,sp
 push word [bp+4]
 call terminal_transfer_timed_byte ; native callee RET2
 pop bp
 ret
_ymodem_io_put:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov ax,[bp+4]
 call transfer_emit
 jc .failed
 mov word [transfer_protocol_started],1
 xor ax,ax
 jmp .done
.failed:
 mov ax,1
.done:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
_ymodem_io_poll:
 push bp
 push bx
 push si
 push di
 push es
 call terminal_transfer_service
 mov ax,[terminal_transfer_fault]
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
_ymodem_io_progress:
 push bp
 push bx
 push si
 push di
 push es
 call terminal_transfer_accepted_progress
 call terminal_transfer_ui_progress
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret
; Restore ONLY the most recently read prefix. Exclusive foreground owner,
; at most1029 bytes; capacity check proves ISR has not overwritten those slots.
; Atomic pointer/count update is constant-time and preserves entry IF.
_ymodem_io_unread:
 push bp
 mov bp,sp
 push bx
 push cx
 pushf
 cli
 mov cx,[bp+4]
 cmp cx,1029
 ja .failed
 mov ax,[uart_rx_count]
 add ax,cx
 jc .failed
 cmp ax,4096
 ja .failed
 mov bx,[uart_rx_read]
 sub bx,uart_rx_buffer
 sub bx,cx
 and bx,4095
 add bx,uart_rx_buffer
 mov [uart_rx_read],bx
 mov [uart_rx_count],ax
 xor ax,ax
 jmp .done
.failed:
 cmp word [terminal_transfer_fault],0
 jne .latched
 mov word [terminal_transfer_fault],5
.latched:
 mov ax,1
.done:
 popf
 pop cx
 pop bx
 pop bp
 ret
