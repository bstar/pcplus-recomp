; FAR cdecl chat_sink(kind,value,user). Caller uses the parent DS=SS.
; No polling, keyboard read, private queue or direct UART write. Return0 has
; no product-data side effect. Native LOG/HISTORY retain their exact word ABI.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_enqueue_user_al,terminal_log_character,terminal_history_character
chat_sink_tx:
 call terminal_enqueue_user_al
 retf
chat_sink_log:
 push ax
 call terminal_log_character
 add sp,2
 retf
chat_sink_history:
 push ax
 call terminal_history_character ; Native RET2.
 retf

SEGMENT CHAT_ADAPTER_CODE public align=16 class=FARCODE use16
global _terminal_chat_sink
extern _redisplay_active,terminal_quit,terminal_aspect_active,terminal_tx_count
extern terminal_sink_3988_enabled,terminal_printer_count
_terminal_chat_sink:
 push bp
 mov bp,sp
 push si
 push di
 push es
 cmp word [_redisplay_active],2
%ifdef CHAT_REDISPLAY
 je .owned
 extern _chat_view_active
 cmp word [_redisplay_active],1
 jne .refuse
 cmp word [_chat_view_active],1
 jne .refuse
.owned:
%else
 jne .refuse
%endif
 cmp word [terminal_quit],0
 jne .refuse
 cmp word [terminal_aspect_active],0
 jne .refuse
 mov ax,[ss:bp+8]
 cmp word [ss:bp+6],1 ; CHAT_TX
 je .tx
 cmp word [ss:bp+6],2 ; CHAT_LOG
 je .log
 cmp word [ss:bp+6],3 ; CHAT_HISTORY
 jne .refuse
 call far chat_sink_history
 jmp .accepted
.tx:
 cmp ax,255
 ja .refuse
 cmp word [terminal_tx_count],1024
 jae .refuse
 call far chat_sink_tx
 jmp .accepted
.log:
 ; Native09B6 may append CR+LF to the128-byte printer queue. Reserve both
 ; slots before calling it, so backpressure cannot half-apply this effect.
 cmp word [terminal_sink_3988_enabled],0
 je .log_ready
 cmp word [terminal_printer_count],126
 ja .refuse
.log_ready:
 call far chat_sink_log
.accepted:
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
