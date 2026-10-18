; Maintained foreground text-capture UI and checked-file bridge.
; Native09b6 still filters processed input; no UART/raw/binary-transfer logging.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _capture_session_begin,_capture_session_stop,_capture_session_pause
extern _capture_session_flush,_capture_session_put,_capture_session_poll
extern _capture_session_notice,_capture_file_result
extern terminal_sink_398a_enabled,terminal_cr_adds_lf
extern terminal_clock_ticks,terminal_poll_serial,terminal_read_key,keyboard_poll
extern terminal_connection_notice,terminal_connection_notice_restore
extern terminal_quit,terminal_exit_code,uart_rx_dropped,connection_state
extern terminal_macro_active,terminal_program_pending,terminal_ansi_wait_active
global terminal_capture_toggle,terminal_capture_pause,terminal_capture_crlf
global terminal_capture_poll,terminal_capture_flush,terminal_capture_before_program
global terminal_sink_8436,terminal_sink_427f,terminal_sink_bb23
global terminal_capture_native_refresh
%macro save 0
 push bp
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push es
%endmacro
%macro restore 0
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 pop bp
 ret
%endmacro
terminal_capture_toggle:
 save
 cmp word [terminal_sink_398a_enabled],0
 je .open
 call _capture_session_stop
 jmp .done
.open:
 cmp word [terminal_macro_active],0
 jne .denied
 cmp word [terminal_program_pending],0
 jne .denied
 cmp word [terminal_ansi_wait_active],0
 jne .denied
 cmp word [connection_state],0
 je .prompt
 cmp word [connection_state],6
 jne .denied
.prompt:
 call terminal_connection_notice_restore
 call capture_prompt
 or ax,ax
 jz .done
 call terminal_clock_ticks
 push dx
 push ax
 mov ax,capture_filename
 push ax
 call _capture_session_begin
 add sp,6
 or ax,ax
 jz .done
 cmp word [_capture_session_notice],4
 je .done
.denied:
 mov word [_capture_session_notice],5
.done:
 restore
terminal_capture_pause:
 save
 call _capture_session_pause
 restore
terminal_capture_crlf:
 save
 xor word [terminal_cr_adds_lf],1
 mov si,capture_crlf_off
 cmp word [terminal_cr_adds_lf],0
 je .draw
 mov si,capture_crlf_on
.draw:
 call terminal_connection_notice
 restore
terminal_capture_flush:
 save
 call _capture_session_flush
 restore
terminal_capture_poll:
 save
 call terminal_clock_ticks
 push dx
 push ax
 call _capture_session_poll
 add sp,4
 mov bx,[_capture_session_notice]
 mov word [_capture_session_notice],0
 or bx,bx
 jz .done
 cmp bx,5
 ja .done
 dec bx
 shl bx,1
 mov si,[capture_notices+bx]
 call terminal_connection_notice
.done:
 restore
; Close before DOS EXEC: no child may inherit this owner's file handle. A close
; whose outcome is uncertain cancels launch; the terminal can still disconnect.
; AX=0 resolved, AX=1 uncertain. Does not erase the sticky session failure.
terminal_capture_before_program:
 push bp
 push si
 push di
 push es
 cmp word [terminal_sink_398a_enabled],0
 je .check
 call _capture_session_stop
.check:
 xor ax,ax
 cmp word [_capture_file_result+12],0
 je .done
 inc ax
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
; Native putc argument shape is character, near FILE*. The maintained owner
; ignores that legacy token and returns unsigned byte/FFFF as the caller needs.
terminal_sink_8436:
 jmp _capture_session_put
; Native's non-CR failure UI is deferred to the next foreground poll. Its paired
; refresh is identified explicitly so unrelated viewport services still trap.
terminal_sink_427f:
 mov byte [capture_native_refresh],1
 ret
terminal_sink_bb23:
 jmp _capture_session_stop
terminal_capture_native_refresh:
 cmp byte [capture_native_refresh],0
 je .other
 mov byte [capture_native_refresh],0
 clc
 ret
.other:
 stc
 ret

; Own bottom two rows while editing; keep UART TX, flow and carrier serviced.
; Input parsing waits until restoration. RX overflow aborts through live cleanup.
capture_prompt:
 mov ah,0x0f
 int 0x10
 cmp al,3
 jne .bad_view
 cmp ah,80
 jne .bad_view
 or bh,bh
 jnz .bad_view
 mov ah,3
 xor bh,bh
 int 0x10
 mov [capture_cursor],dx
 mov [capture_shape],cx
 push ds
 mov ax,0xb800
 mov ds,ax
 mov si,3680
 pop es
 mov di,capture_saved
 mov cx,160
 cld
 rep movsw
 push es
 pop ds
 mov ax,0xb800
 mov es,ax
 mov di,3680
 mov ax,0x1f20
 mov cx,160
 rep stosw
 mov di,3680
 mov si,capture_title
.title:
 lodsb
 or al,al
 jz .ready
 mov ah,0x1f
 stosw
 jmp .title
.ready:
 mov word [capture_length],0
 mov byte [capture_filename],0
 mov cx,0x0607
 mov ah,1
 int 0x10
.input:
 mov dx,[capture_length]
 mov dh,24
 xor bh,bh
 mov ah,2
 int 0x10
 call terminal_poll_serial
 cmp word [uart_rx_dropped],0
 jne .overflow
 cmp word [terminal_quit],0
 jne .cancel
 call keyboard_poll
 or ax,ax
 jz .input
 call terminal_read_key
 cmp ax,0x2d00
 je .quit
 cmp al,27
 je .cancel
 cmp al,13
 je .accept
 cmp al,8
 je .backspace
 cmp al,32
 jb .input
 cmp al,126
 ja .input
 mov bx,[capture_length]
 cmp bx,63
 jae .input
 mov [capture_filename+bx],al
 mov di,bx
 shl di,1
 add di,3840
 mov ah,0x1f
 mov [es:di],ax
 inc bx
 mov [capture_length],bx
 mov byte [capture_filename+bx],0
 jmp .input
.backspace:
 mov bx,[capture_length]
 or bx,bx
 jz .input
 dec bx
 mov [capture_length],bx
 mov byte [capture_filename+bx],0
 mov di,bx
 shl di,1
 add di,3840
 mov word [es:di],0x1f20
 jmp .input
.accept:
 mov ax,1
 jmp .restore
.overflow:
 mov word [terminal_exit_code],6
.quit:
 mov word [terminal_quit],1
.cancel:
 xor ax,ax
.restore:
 push ax
 mov ax,0xb800
 mov es,ax
 mov di,3680
 mov si,capture_saved
 mov cx,160
 cld
 rep movsw
 mov cx,[capture_shape]
 mov ah,1
 int 0x10
 mov dx,[capture_cursor]
 xor bh,bh
 mov ah,2
 int 0x10
 pop ax
 ret
.bad_view:
 mov word [_capture_session_notice],5
 xor ax,ax
 ret
SEGMENT _DATA public class=DATA use16
capture_native_refresh: db 0
capture_length: dw 0
capture_cursor: dw 0
capture_shape: dw 0
capture_filename: times 64 db 0
capture_saved: times 320 db 0
capture_title: db ' Capture file [PCPLUS.LOG]:   [Enter] Append   [Esc] Cancel',0
capture_notices: dw capture_open,capture_hold,capture_closed,capture_error,capture_denied
capture_open: db 'Capture open',0
capture_hold: db 'Capture hold',0
capture_closed: db 'Capture closed',0
capture_error: db 'Capture error',0
capture_denied: db 'Capture denied',0
capture_crlf_on: db 'CR+LF on',0
capture_crlf_off: db 'CR+LF off',0
