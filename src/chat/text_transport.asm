; Optional native-boundary TEXT sink. Unlike the ordinary Chat sink, acceptance
; means uart_try_write actually emitted the byte. One foreground caller, DS=SS.
BITS 16
CPU 8086
SEGMENT CHAT_ADAPTER_CODE public align=16 class=FARCODE use16
; Reuse the existing exact register-service thunk; no new resident CS bytes.
extern connection_uart_write_resident
global _terminal_chat_text_tx_sink
extern _redisplay_active,terminal_quit,terminal_aspect_active,connection_state
extern terminal_tx_count,terminal_macro_active,terminal_macro_tx_allowed
extern terminal_macro_tx_epoch,terminal_record_user_delivered_far
_terminal_chat_text_tx_sink:
 push bp
 mov bp,sp
 push si
 push di
 push es
 cmp word [ss:bp+6],1 ; CHAT_TX only: echo/delay require other services.
 jne .refuse
 mov ax,[ss:bp+8]
 cmp ax,255
 ja .refuse
 cmp word [_redisplay_active],2
 jne .refuse
 cmp word [terminal_quit],0
 jne .refuse
 cmp word [terminal_aspect_active],0
 jne .refuse
 cmp word [terminal_macro_active],0
 jne .refuse
 cmp word [terminal_tx_count],0
 jne .refuse
 cmp word [terminal_macro_tx_allowed],1
 jne .refuse
 cmp word [connection_state],0
 je .write
 cmp word [connection_state],6
 jne .refuse
.write:
 call far connection_uart_write_resident
 jc .refuse
 mov word [terminal_macro_tx_allowed],0
 inc word [terminal_macro_tx_epoch]
 call far terminal_record_user_delivered_far
 mov ax,1
 jmp .done
.refuse:
 xor ax,ax
.done:
 pop es
 pop di
 pop si
 pop bp
 retf
