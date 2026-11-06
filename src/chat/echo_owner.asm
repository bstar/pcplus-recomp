; Experimental synchronous native echo scope. The original parser retains its
; stack while bounded foreground IO services the modem. No second renderer or
; Chat module call may run until this scope restores the outer cursor context.
; The frontend busy-key guard is part of this contract. Parent DS=SS, DF clear.
BITS 16
CPU 8086
SEGMENT CHAT_ECHO_CODE public align=16 class=FARCODE use16
extern chat_echo_cursor_swap,terminal_key_echo_far
extern line_poll_far,line_tick_far,line_raw_receive_far
extern _redisplay_active,terminal_aspect_active,terminal_parser_active
extern terminal_ansi_wait_active,terminal_ansi_wait_cancel,terminal_ansi_wait_timed_out
extern terminal_quit,connection_state,redisplay_snapshot,ui_window_rows
extern terminal_deferred_count,terminal_macro_active,terminal_program_pending
extern screen_viewport_enabled,screen_video_row_bytes,screen_attribute_row_bytes
extern screen_viewport_offset,screen_line_flags
global _terminal_chat_text_echo_sink,terminal_chat_echo_read_far
global terminal_chat_echo_unread_far,terminal_chat_echo_read_now_far
global terminal_chat_echo_error_far

; FAR cdecl sink(kind,value,user). Only ECHO4, byte0..255, and the exact
; caller-owned22-byte context at frozen+14500 are admitted. No refusal paints.
_terminal_chat_text_echo_sink:
 push bp
 mov bp,sp
 push si
 push di
 push es
 call admit
 jnc .accepted
 xor ax,ax
 jmp .done
.accepted:
 ; Scope state is retained in this bank, never a new near allocation. The
 ; callback has one foreground owner. Context storage exchanges twice, so it
 ; ends holding the updated local cursor and the parent is restored exactly.
 push word [terminal_ansi_wait_cancel]
 push word [terminal_ansi_wait_timed_out]
 mov ax,1
 mov [cs:active],ax
 mov [cs:have_last],ax
 mov word [cs:remaining],4096
 xor ax,ax
 mov [cs:fault],ax
 mov [cs:unread],ax
 mov [terminal_ansi_wait_cancel],ax
 mov [terminal_ansi_wait_timed_out],ax
 inc word [terminal_ansi_wait_active] ; Admission requires zero here.
 mov ax,[ss:bp+8]
 mov [cs:last],ax ; Native C1 unread precedes its first continuation read.
 inc word [terminal_parser_active]
 call far line_tick_far
 mov [cs:started],ax
 mov [cs:progress_tick],ax
 call far chat_echo_cursor_swap
 mov ax,[ss:bp+8]
 call far terminal_key_echo_far
 ; No module reentry/unload or second renderer is allowed before here.
 les di,[ss:bp+10]
 call far chat_echo_cursor_swap
 dec word [terminal_parser_active]
 mov word [terminal_ansi_wait_active],0
 pop word [terminal_ansi_wait_timed_out]
 pop word [terminal_ansi_wait_cancel]
 xor ax,ax
 mov [cs:active],ax
 mov [cs:unread],ax
 mov [cs:have_last],ax
 mov ax,1 ; Accepted exactly once, even if the parser partially painted/faulted.
.done:
 pop es
 pop di
 pop si
 pop bp
 retf

; Read-only admission islands keep every refusal close to its checks.
admit:
 cmp word [ss:bp+6],4
 jne .bad
 cmp word [ss:bp+8],255
 ja .bad
 cmp word [ss:bp+10],redisplay_snapshot+14500
 jne .bad
 mov ax,seg redisplay_snapshot
 cmp [ss:bp+12],ax
 jne .bad
 cmp word [cs:active],0
 jne .bad
 cmp word [_redisplay_active],2
 jne .bad
%ifdef TERMINAL_CHAT_FOREGROUND_TEXT
 ; Entry admitted an empty shared FIFO; the foreground now owns its retained
 ; typeahead until TEXT completes or the entire Chat session is retired.
 cmp word [terminal_deferred_count],32
 ja .bad
%endif
 mov ax,[terminal_aspect_active]
 or ax,[terminal_parser_active]
 or ax,[terminal_ansi_wait_active]
 or ax,[terminal_quit]
%ifndef TERMINAL_CHAT_FOREGROUND_TEXT
 or ax,[terminal_deferred_count]
%endif
 or ax,[terminal_macro_active]
 or ax,[terminal_program_pending]
 or ax,[screen_viewport_enabled]
 or ax,[screen_viewport_offset]
 jnz .bad
 jmp short .planes
.bad:
 stc
 ret
.planes:
 cmp word [screen_video_row_bytes],160
 jne .bad
 cmp word [screen_attribute_row_bytes],80
 jne .bad
 mov ax,0x40
 mov es,ax
 cmp byte [es:0x49],3
 jne .bad
 cmp word [es:0x4a],80
 jne .bad
 cmp byte [es:0x62],0
 jne .bad
 xor ax,ax
 mov al,[es:0x84]
 or ax,ax
 jnz .rows
 mov ax,24
.rows:
 inc ax
 cmp ax,[ui_window_rows]
 jne .bad
 mov cx,ax
 mov si,screen_line_flags
.plain:
 cmp byte [si],0
 jne .bad
 inc si
 loop .plain
 cmp word [connection_state],0
 je .context
 cmp word [connection_state],6
 jne .bad
.context:
 les di,[ss:bp+10]
 mov ax,[es:di]
 cmp ax,[ui_window_rows]
 jae .cursor_bad
 cmp [es:di+6],ax
 jne .cursor_bad
 mov dx,[es:di+2]
 cmp dx,79
 ja .cursor_bad
 cmp [es:di+4],dx
 jne .cursor_bad
 cmp [es:di+8],dx
 jne .cursor_bad
 mov cx,80
 mul cx
 add ax,[es:di+2]
 cmp [es:di+12],ax
 jne .cursor_bad
 shl ax,1
 cmp [es:di+10],ax
 jne .cursor_bad
 cmp word [es:di+14],1
 ja .cursor_bad
 jne .no_wrap
 mov ax,[es:di]
 cmp [es:di+16],ax
 jne .cursor_bad
 mov ax,[es:di+2]
 cmp [es:di+18],ax
 jne .cursor_bad
.no_wrap:
 cmp word [es:di+20],1
 ja .cursor_bad
 clc
 ret
.cursor_bad:
 stc
 ret

; CF0: unowned, preserve AX. CF1: owned AX=actual byte orFFFF. The whole echo
; has36 BIOS ticks, not36 per byte.4096 attempts without clock progress also
; end a stopped-clock wait, without shortening the advancing-clock deadline.
; The finite count also terminates a stopped-clock/no-input fixture.
terminal_chat_echo_read_far:
 cmp word [cs:active],0
 je unowned
 push bp
 push si
 push di
 push es
 mov di,1
.wait:
 call checked_read
 cmp ax,0xffff
 jne .done
 cmp word [cs:fault],0
 je .wait
.done:
 pop es
 pop di
 pop si
 pop bp
 stc
 retf

; A nested original discard/wait controller owns its own outer loop. Give it
; a nonblocking read; a fault sets its existing cancel latch before return.
terminal_chat_echo_read_now_far:
 cmp word [cs:active],0
 je unowned
 push bp
 push si
 push di
 push es
 xor di,di
 call checked_read
 pop es
 pop di
 pop si
 pop bp
 stc
 retf
unowned:
 clc
 retf

checked_read:
 cmp word [cs:fault],0
 jne .failed_empty
 mov word [terminal_ansi_wait_active],1
 or di,di
 jz .polled ; The nested controller already serviced IO before this read.
 call far line_poll_far
.polled:
 cmp word [terminal_quit],0
 jne .cancel
 cmp word [terminal_ansi_wait_cancel],0
 jne .cancel
 cmp word [connection_state],0
 je .clock
 cmp word [connection_state],6
 jne .carrier
.clock:
 call far line_tick_far
 sub ax,[cs:started]
 cmp ax,36
 jae .timeout
 add ax,[cs:started]
 cmp ax,[cs:progress_tick]
 je .read_budget
 mov [cs:progress_tick],ax
 mov word [cs:remaining],4096
.read_budget:
 cmp word [cs:remaining],0
 je .budget
 dec word [cs:remaining]
 cmp word [cs:unread],0
 je .receive
 mov word [cs:unread],0
 mov word [cs:have_last],1
 mov ax,[cs:last]
 ret
.receive:
 call far line_raw_receive_far
 cmp ax,0xffff
 je .empty
 mov [cs:last],ax
 mov word [cs:have_last],1
 ret
.budget:
 mov ax,4
 jmp .fail
.timeout:
 mov ax,1
 jmp .fail
.cancel:
 mov ax,2
 jmp .fail
.carrier:
 mov ax,3
.fail:
 mov [cs:fault],ax
.failed_empty:
 mov word [terminal_ansi_wait_cancel],1
.empty:
 mov ax,0xffff
 ret

; One-byte undo belongs to this parser scope, never the ordinary UART ring.
terminal_chat_echo_unread_far:
 cmp word [cs:active],0
 je unowned
 cmp word [cs:have_last],0
 je .bad
 cmp word [cs:unread],0
 jne .bad
 mov word [cs:unread],1
 mov word [cs:have_last],0
 stc
 retf
.bad:
 mov word [cs:fault],5
 mov word [terminal_ansi_wait_cancel],1
 stc
 retf
terminal_chat_echo_error_far:
 mov ax,[cs:fault]
 retf
active: dw 0
started: dw 0
progress_tick: dw 0
remaining: dw 0
fault: dw 0
unread: dw 0
last: dw 0
have_last: dw 0
