; Maintained optional Hayes initialization transactions. DS=SS, foreground only.
; All private state stays in the retained MODEM code segment to spare DGROUP.
BITS 16
CPU 8086
%include "modem_import.inc"
SEGMENT MODEM_CODE public align=16 class=FARCODE use16
GROUP MODEM_GROUP MODEM_CODE
extern terminal_modem_init_wait,terminal_modem_pause
extern connection_state,connection_elapsed,connection_deadline
extern terminal_connection_reset_clock_impl,terminal_connection_seconds_clock_impl
extern terminal_modem_send_line_start_impl,terminal_modem_send_poll_impl
extern terminal_modem_send_position_impl,terminal_modem_send_line_armed_impl
extern connection_uart_write_service
global terminal_modem_init_validate_impl,terminal_modem_init_begin_impl
global terminal_modem_init_poll_impl,terminal_modem_init_receive_impl

; Every nonempty command must have a physical CR. CRLF and pause/LF-only
; trailers are preserved. Embedded physical LF inside a command is rejected.
terminal_modem_init_validate_impl:
 xor bx,bx
 mov cx,129
.next:
 lodsb
 or al,al
 jz .end
 cmp al,[terminal_modem_pause]
 je .advance
 cmp al,13
 je .terminated
 cmp al,10
 jne .data
 or bx,bx
 jnz .bad
 jmp .advance
.data:
 mov bx,1
 jmp .advance
.terminated:
 xor bx,bx
.advance:
 loop .next
.bad:
 mov ax,1
 stc
 ret
.end:
 or bx,bx
 jnz .bad
 xor ax,ax
 clc
 ret

; SI near expanded initialization, AX nonzero if prior cancel needs separator.
terminal_modem_init_begin_impl:
 mov [cs:init_cursor],si
 mov byte [cs:modem_init_reply],0
 mov byte [cs:modem_init_line_length],0
 or ax,ax
 jz init_begin_line
 mov byte [cs:modem_init_phase],3
 call terminal_connection_reset_clock_impl
 ret

; Start one physical command, without altering its bytes or the sender cursor.
init_begin_line:
 mov si,[cs:init_cursor]
 cmp byte [si],0
 jne .begin
 mov byte [cs:modem_init_phase],0
 ret
.begin:
 call terminal_connection_reset_clock_impl
 mov byte [cs:modem_init_phase],1
 mov byte [cs:modem_init_reply],0
 mov byte [cs:modem_init_line_length],0
 mov byte [cs:init_space],0
 mov byte [cs:init_echo_length],0
 mov byte [cs:init_echo_space],0
 mov di,si
.echo:
 mov al,[di]
 inc di
 or al,al
 jz .echo_done
 cmp al,[terminal_modem_pause]
 je .echo
 cmp al,13
 je .echo_done
 cmp al,10
 je .echo
 cmp al,' '
 jne .echo_data
 cmp byte [cs:init_echo_length],0
 je .echo
 mov byte [cs:init_echo_space],1
 jmp .echo
.echo_data:
 cmp byte [cs:init_echo_space],0
 je .echo_character
 mov al,' '
 call init_echo_append
 mov al,[di-1]
 mov byte [cs:init_echo_space],0
.echo_character:
 call init_upper
 call init_echo_append
 jmp .echo
.echo_done:
 mov byte [cs:init_require_ack],0
 cmp byte [cs:init_echo_length],0
 je .start
 mov byte [cs:init_require_ack],1
.start:
 mov word [connection_state],1
 call terminal_modem_send_line_start_impl
 ret
init_echo_append:
 xor bx,bx
 mov bl,[cs:init_echo_length]
 cmp bx,5
 jae .long
 mov [cs:init_echo+bx],al
 inc byte [cs:init_echo_length]
 ret
.long:
 mov byte [cs:init_echo_length],6
 ret
init_upper:
 cmp al,'a'
 jb .done
 cmp al,'z'
 ja .done
 sub al,32
.done:
 ret

; AX0 busy, AX1 all commands acknowledged, AX2 explicit ERROR, AX3 timeout.
terminal_modem_init_poll_impl:
 cmp byte [cs:modem_init_phase],0
 je .ready
 cmp byte [cs:modem_init_phase],4
 je .guard
 cmp byte [cs:modem_init_phase],2
 je .reply
 call init_expired
 jc .timeout
 cmp byte [cs:modem_init_phase],3
 je .separator
 cmp byte [cs:modem_init_phase],1
 jne .error
 call terminal_modem_send_poll_impl
 or ax,ax
 jz .busy
 call terminal_modem_send_position_impl
 mov [cs:init_cursor],ax
 call terminal_modem_send_line_armed_impl
 or ax,ax
 jz .ready ; validated pause/LF-only trailer, no result to request
 cmp byte [cs:init_require_ack],0
 je .begin_guard
 mov byte [cs:modem_init_phase],2
 mov word [connection_state],10
 mov ax,[terminal_modem_init_wait]
 call terminal_connection_seconds_clock_impl
.reply:
 cmp byte [cs:modem_init_reply],2
 je .error
 cmp byte [cs:modem_init_reply],1
 je .next
 call init_expired
 jc .timeout
 jmp .busy
.next:
 call init_begin_line
 cmp byte [cs:modem_init_phase],0
 je .ready
 jmp .busy
.separator:
 mov al,13
 call connection_uart_write_service
 jc .busy
.begin_guard:
 ; A retry separator or empty command can reply ERROR/OK or remain quiet.
 ; Drain for the full configured interval before admitting the new command.
 ; Late traffic beyond that declared guard cannot be correlated generically.
 mov byte [cs:modem_init_phase],4
 mov word [connection_state],10
 mov ax,[terminal_modem_init_wait]
 call terminal_connection_seconds_clock_impl
 jmp .busy
.guard:
 call init_expired
 jc .next
.busy:
 xor ax,ax
 ret
.ready:
 mov byte [cs:modem_init_phase],0
 mov ax,1
 ret
.error:
 mov ax,2
 ret
.timeout:
 mov ax,3
 ret
init_expired:
 mov ax,[connection_elapsed+2]
 cmp ax,[connection_deadline+2]
 ja .yes
 jb .no
 mov ax,[connection_elapsed]
 cmp ax,[connection_deadline]
 jae .yes
.no:
 clc
 ret
.yes:
 stc
 ret

; Only framed terminal results after a physically sent CR can be admitted.
; Empty lines, echo, long/unknown lines and guard-window traffic are ignored.
terminal_modem_init_receive_impl:
 cmp byte [cs:modem_init_reply],0
 jne .return
 cmp byte [cs:init_require_ack],0
 je .return
 cmp byte [cs:modem_init_phase],2
 je .feed
 cmp byte [cs:modem_init_phase],1
 jne .return
 push ax
 call terminal_modem_send_line_armed_impl
 or ax,ax
 pop ax
 jz .return
.feed:
 cmp al,13
 je .line
 cmp al,10
 je .line
 cmp al,' '
 jne .character
 cmp byte [cs:modem_init_line_length],0
 je .return
 mov byte [cs:init_space],1
 ret
.character:
 cmp byte [cs:init_space],0
 jne .unknown
 xor bx,bx
 mov bl,[cs:modem_init_line_length]
 cmp bx,5
 jae .unknown
 call init_upper
 mov [cs:init_line+bx],al
 inc byte [cs:modem_init_line_length]
 ret
.unknown:
 mov byte [cs:modem_init_line_length],6
 ret
.line:
 xor cx,cx
 mov cl,[cs:modem_init_line_length]
 mov byte [cs:modem_init_line_length],0
 mov byte [cs:init_space],0
 jcxz .return
 cmp cx,5
 ja .return
 ; Do not mistake an exact echoed short command for a terminal result.
 cmp cl,[cs:init_echo_length]
 jne .classify
 xor bx,bx
.echo:
 mov al,[cs:init_line+bx]
 cmp al,[cs:init_echo+bx]
 jne .classify
 inc bx
 cmp bx,cx
 jb .echo
 ret
.classify:
 cmp cx,1
 je .numeric
 cmp cx,2
 je .ok
 cmp cx,5
 jne .return
 cmp word [cs:init_line],'ER'
 jne .return
 cmp word [cs:init_line+2],'RO'
 jne .return
 cmp byte [cs:init_line+4],'R'
 jne .return
 mov byte [cs:modem_init_reply],2
 ret
.ok:
 cmp word [cs:init_line],'OK'
 jne .return
.success:
 mov byte [cs:modem_init_reply],1
 ret
.numeric:
 cmp byte [cs:init_line],'0'
 je .success
 cmp byte [cs:init_line],'4'
 jne .return
 mov byte [cs:modem_init_reply],2
.return:
 ret

global modem_init_phase,modem_init_reply,modem_init_line_length
modem_init_phase: db 0
modem_init_reply: db 0
modem_init_line_length: db 0
init_cursor: dw 0
init_require_ack: db 0
init_echo_length: db 0
init_echo_space: db 0
init_space: db 0
init_echo: times 5 db 0
init_line: times 5 db 0
