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
