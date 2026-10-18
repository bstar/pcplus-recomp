; Maintained live transport over the actual recovered UART and keyboard modules.
; Near calls, DS=SS. Public callbacks preserve BP/SI/DI (and ES).
; Single foreground producer/consumer TX ring; UART ISR owns RX only.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_receive_byte,uart_unreceive_byte,uart_try_write,uart_poll_flow
extern keyboard_poll,keyboard_read_extended
extern terminal_keymap,terminal_quit,terminal_exit_code
global terminal_poll_io,terminal_enqueue_al,terminal_tick_low
global ansi_next_byte,ansi_unread_byte,csi_transmit_byte,csi_transmit_string

; Read only the low BIOS tick word. Unsigned subtraction handles 16-bit wrap.
; BIOS midnight reset can end the wait early; it cannot extend this deadline.
terminal_tick_low:
 push es
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x6c]
 pop es
 ret

; Consume one actual RX byte, including NUL, or return ffff after36 BIOS ticks.
; Continue servicing flow, bounded TX and keyboard/Alt-X while waiting.
ansi_next_byte:
 push bp
 push si
 push di
 push es
 call terminal_tick_low
 mov si,ax
.wait:
 cmp word [terminal_quit],0
 jne .timeout
 call terminal_poll_io
 cmp word [terminal_quit],0
 jne .timeout
 call uart_receive_byte
 cmp ax,0xffff
 jne .done
 call terminal_tick_low
 sub ax,si
 cmp ax,36
 jb .wait
.timeout:
 mov ax,0xffff
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

; Original parser calls this only immediately after consuming a byte.
ansi_unread_byte:
 jmp uart_unreceive_byte

; AL -> bounded TX queue. No busy wait, no local echo. AX is preserved.
; Overflow terminates the session with explicit error3 instead of losing bytes.
terminal_enqueue_al:
 push bx
 cmp word [terminal_quit],0
 jne .done
 cmp word [terminal_tx_count],1024
 jae .overflow
 mov bx,[terminal_tx_tail]
 mov [terminal_tx_buffer+bx],al
 inc bx
 and bx,1023
 mov [terminal_tx_tail],bx
 inc word [terminal_tx_count]
.done:
 pop bx
 ret
.overflow:
 mov word [terminal_exit_code],3
 mov word [terminal_quit],1
 jmp .done

; Original report/output ABI: word argument, callee cleanup RET2.
csi_transmit_byte:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov ax,[bp+4]
 call terminal_enqueue_al
 pop es
 pop di
 pop si
 pop bp
 ret 2

csi_transmit_string:
 push bp
 mov bp,sp
 push si
 push di
 push es
 mov si,[bp+4]
.next:
 cmp word [terminal_quit],0
 jne .done
 lodsb
 or al,al
 jz .done
 call terminal_enqueue_al
 jmp .next
.done:
 pop es
 pop di
 pop si
 pop bp
 ret 2

terminal_poll_io:
 push bp
 push si
 push di
 push es
 cmp word [terminal_quit],0
 jne .done
 call uart_poll_flow
 cmp word [terminal_tx_count],0
 je .keyboard
 mov bx,[terminal_tx_head]
 mov al,[terminal_tx_buffer+bx]
 call uart_try_write
 jc .keyboard
 ; try_write preserves AX/DX; keep head lookup independent of future API changes.
 mov bx,[terminal_tx_head]
 inc bx
 and bx,1023
 mov [terminal_tx_head],bx
 dec word [terminal_tx_count]
.keyboard:
 call keyboard_poll
 or ax,ax
 jz .done
 ; A successful peek makes this actual blocking read immediately satisfiable;
 ; the private application queue is disabled and BIOS has one foreground reader.
 call keyboard_read_extended
 cmp ax,0x2d00
 je .quit
 or al,al
 jz .scan
 call terminal_enqueue_al
 jmp .done
.scan:
 mov si,terminal_keymap
 cmp ah,0x48
 je .arrow
 add si,12
 cmp ah,0x50
 je .arrow
 add si,12
 cmp ah,0x4d
 je .arrow
 add si,12
 cmp ah,0x4b
 jne .done ; Other scan-only keys await configurable translation support.
.arrow:
 ; Validate the complete12-byte slot before queueing it; never cross a slot.
 mov di,si
 mov cx,12
.find_end:
 cmp byte [di],0
 je .send_arrow
 inc di
 loop .find_end
 mov word [terminal_exit_code],4 ; Invalid nonterminated binding.
 mov word [terminal_quit],1
 jmp .done
.send_arrow:
 cmp si,di
 jae .done
 cmp word [terminal_quit],0
 jne .done
 lodsb
 call terminal_enqueue_al
 jmp .send_arrow
.quit:
 mov word [terminal_quit],1
.done:
 pop es
 pop di
 pop si
 pop bp
 ret

SEGMENT _DATA public align=16 class=DATA use16
GROUP DGROUP _DATA
global terminal_tx_head,terminal_tx_tail,terminal_tx_count,terminal_tx_buffer
terminal_tx_head: dw 0
terminal_tx_tail: dw 0
terminal_tx_count: dw 0
terminal_tx_buffer: times 1024 db 0
