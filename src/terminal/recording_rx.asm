; Record ordinary raw receive bytes before translation, and parser continuation
; bytes. A parser lookahead unreceive is observed once, never duplicated.
BITS 16
CPU 8086
SEGMENT CONFIG_CODE public align=16 class=FARCODE use16
GROUP CONFIG_GROUP CONFIG_CODE
extern _recording_terminal_cookie,_recording_terminal_owner
extern _recording_terminal_receive,_recording_terminal_replay,_recording_terminal_unread_pointer
extern uart_rx_read
global terminal_record_receive_far,terminal_record_unread_far,terminal_recording_owned_far
global _recording_ui_ready
extern _terminal_autostart_busy
extern terminal_tx_count,terminal_macro_active,terminal_parser_active,terminal_quit
extern terminal_transfer_pending,terminal_transfer_active,terminal_program_pending,terminal_program_active
extern terminal_monitor_active,terminal_controller_active,terminal_ansi_wait_active,uart_break_hold,connection_state
; No byte owner, partial parser, pending output or held invitation may straddle
; a UI recording boundary. Existing menu service lets these drain/expire.
_recording_ui_ready:
 mov ax,[terminal_tx_count]
 or ax,[terminal_macro_active]
 or ax,[terminal_parser_active]
 or ax,[terminal_quit]
 or ax,[terminal_transfer_pending]
 or ax,[terminal_transfer_active]
 or ax,[terminal_program_pending]
 or ax,[terminal_program_active]
 or ax,[terminal_monitor_active]
 or ax,[terminal_controller_active]
 or ax,[terminal_ansi_wait_active]
 or ax,[uart_break_hold]
 jnz .no
 cmp word [connection_state],0
 je .invitation
 cmp word [connection_state],6
 jne .no
.invitation:
 call far _terminal_autostart_busy
 or ax,ax
 jnz .no
 mov ax,1
 retf
.no:
 xor ax,ax
 retf
%macro save 0
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
%endmacro
%macro restore 0
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 retf
%endmacro
; AX=actual ordinary byte. Preserve all registers and flags, including before
; entering native parsing. The script prompt matches the raw UART byte stream.
terminal_record_receive_far:
 save
 cmp ax,255
 ja .done
 cmp word [_recording_terminal_cookie],0x5244
 jne .done
 cmp word [_recording_terminal_owner+136],1
 jne .done
 cmp word [_recording_terminal_replay],0
 je .record
 mov word [_recording_terminal_replay],0
 mov bx,[uart_rx_read]
 cmp bx,[_recording_terminal_unread_pointer]
 je .done
.record:
 push ax
 call far _recording_terminal_receive
 add sp,2
.done:
 restore
; Called before the actual native unreceive. Save the post-consumption cursor
; expected when that same byte is read again, including a ring wrap.
terminal_record_unread_far:
 save
 cmp word [_recording_terminal_cookie],0x5244
 jne .done
 cmp word [_recording_terminal_owner+136],1
 jne .done
 mov ax,[uart_rx_read]
 mov [_recording_terminal_unread_pointer],ax
 mov word [_recording_terminal_replay],1
.done:
 restore
; AX=1 while the recorder owns active/recovery files, otherwise0. Other
; registers preserved. Automatic transfer admission must not steal its bytes.
terminal_recording_owned_far:
 xor ax,ax
 cmp word [_recording_terminal_cookie],0x5244
 jne .done
 cmp word [_recording_terminal_owner+156],0
 je .done
 inc ax
.done:
 retf
