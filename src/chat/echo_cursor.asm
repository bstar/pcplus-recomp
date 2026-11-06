; Native renderer cursor/deferred-state exchange for the future Chat echo owner.
; DS=SS, DF clear. ES:DI -> eleven caller-owned words, disjoint from native
; state and stack, no segment wrap. Both contexts must be coherent plain
; 80-column contexts with viewport disabled and admitted geometry. This is a
; primitive, not an input provider: caller owns the entire parser operation,
; may not yield to a second renderer inside the exchange, and must exchange
; back even after parser timeout/cancellation. Attributes/modes/history/logs
; deliberately remain shared. No UART, keyboard, allocation or private state.
BITS 16
CPU 8086
SEGMENT CHAT_ECHO_CODE public align=16 class=FARCODE use16
extern terminal_key_position_far
extern screen_cursor_row,screen_cursor_column,screen_visible_column
extern screen_previous_row,screen_previous_column,screen_video_offset
extern screen_attribute_offset,csi_wrap_pending,render_deferred_row
extern render_deferred_column,scroll_suppress_next_linefeed
global chat_echo_cursor_swap
chat_echo_cursor_swap:
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 mov si,fields
 mov cx,11
.next:
 mov bx,[cs:si]
 mov ax,[es:di]
 xchg ax,[bx]
 mov [es:di],ax
 add si,2
 add di,2
 loop .next
 ; Coherent derived offsets make this an idempotent cache update plus BIOS
 ; position output. Preserve the deferred-wrap/suppressed-LF words unchanged.
 mov ax,[screen_cursor_row]
 mov dx,[screen_cursor_column]
 call far terminal_key_position_far
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 retf
fields:
 dw screen_cursor_row,screen_cursor_column,screen_visible_column
 dw screen_previous_row,screen_previous_column,screen_video_offset
 dw screen_attribute_offset,csi_wrap_pending,render_deferred_row
 dw render_deferred_column,scroll_suppress_next_linefeed
