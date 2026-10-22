; Maintained nonblocking sender. Inputs are owned, fully expanded C buffers.
; SI=start; start preserves registers. poll returns AX0busy/1done, CF0.
; At most one actual uart_try_write per poll. No queued/unsent byte is consumed.
; Explicit maintained pacing: one BIOS tick per ordinary byte, ten per pause.
; Original calibrated units are retained in the configuration, not reinterpreted.
BITS 16
CPU 8086
SEGMENT MODEM_CODE public align=16 class=FARCODE use16
GROUP MODEM_GROUP MODEM_CODE
extern connection_uart_write_service,connection_elapsed,terminal_modem_pause
global terminal_modem_send_start_impl,terminal_modem_send_poll_impl
global terminal_modem_send_resync_start_impl
terminal_modem_send_resync_start_impl:
 call terminal_modem_send_start_impl
 mov byte [sender_resync],1
 ret
terminal_modem_send_start_impl:
 mov byte [sender_resync],0
 mov [sender_cursor],si
 mov word [sender_delay],0
 ret
terminal_modem_send_poll_impl:
 push bx
 push cx
 push dx
 push si
 mov ax,[connection_elapsed]
 mov cx,ax
 sub ax,[sender_tick]
 cmp ax,[sender_delay]
 jb .busy
 cmp byte [sender_resync],0
 jne .resync
 mov si,[sender_cursor]
 xor ax,ax
 mov al,[si]
 or al,al
 jz .done
 cmp al,[terminal_modem_pause]
 je .pause
 cmp al,0xff
 je .nul
 call connection_uart_write_service
 jc .busy
 mov word [sender_delay],1
 jmp .accepted
.resync:
 mov al,13
 call connection_uart_write_service
 jc .busy
 mov byte [sender_resync],0
 mov [sender_tick],cx
 mov word [sender_delay],1
 jmp .busy
.nul:
 xor al,al
 call connection_uart_write_service
 jc .busy
 mov word [sender_delay],0
 jmp .accepted
.pause:
 mov word [sender_delay],10
.accepted:
 mov [sender_tick],cx
 inc word [sender_cursor]
.busy:
 xor ax,ax
 jmp .return
.done:
 mov ax,1
.return:
 pop si
 pop dx
 pop cx
 pop bx
 clc
 ret
global terminal_modem_code_end
terminal_modem_code_end:
SEGMENT _DATA public class=DATA use16
sender_resync: db 0
sender_cursor: dw 0
sender_tick: dw 0
sender_delay: dw 0
