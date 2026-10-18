; Maintained nonblocking sender. Inputs are owned, fully expanded C buffers.
; SI=start; start preserves registers. poll returns AX0busy/1done, CF0.
; At most one actual uart_try_write per poll. No queued/unsent byte is consumed.
; Explicit maintained pacing: one BIOS tick per ordinary byte, ten per pause.
; Original calibrated units are retained in the configuration, not reinterpreted.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_try_write,connection_elapsed,terminal_modem_pause
global terminal_modem_send_start,terminal_modem_send_poll
terminal_modem_send_start:
 mov [sender_cursor],si
 mov word [sender_delay],0
 ret
terminal_modem_send_poll:
 push bx
 push cx
 push dx
 push si
 mov ax,[connection_elapsed]
 mov cx,ax
 sub ax,[sender_tick]
 cmp ax,[sender_delay]
 jb .busy
 mov si,[sender_cursor]
 xor ax,ax
 mov al,[si]
 or al,al
 jz .done
 cmp al,[terminal_modem_pause]
 je .pause
 cmp al,0xff
 je .nul
 call uart_try_write
 jc .busy
 mov word [sender_delay],1
 jmp .accepted
.nul:
 xor al,al
 call uart_try_write
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
SEGMENT _DATA public class=DATA use16
sender_cursor: dw 0
sender_tick: dw 0
sender_delay: dw 0
