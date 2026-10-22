; Whole-packet foreground TX ownership. The ISR never consumes this ring.
; Queue only on empty TX; later parser replies may follow the owned prefix.
; Successful uart_try_write in transport.asm consumes exactly one owned byte.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
global _clipboard_transport,terminal_clipboard_abort
extern terminal_tx_count,terminal_tx_head,terminal_tx_tail,terminal_tx_buffer
extern terminal_enqueue_user_al,terminal_quit,terminal_parser_active
extern terminal_transfer_pending,terminal_transfer_active
extern terminal_program_pending,terminal_program_active,terminal_macro_active
extern connection_state
_clipboard_transport:
 push bp
 mov bp,sp
 push si
 push di
 mov ax,[bp+4]
 cmp ax,1
 je .probe
 cmp ax,2
 je .cancel
 or ax,ax
 jnz .refuse
 mov ax,[terminal_quit]
 or ax,[terminal_parser_active]
 or ax,[terminal_transfer_pending]
 or ax,[terminal_transfer_active]
 or ax,[terminal_program_pending]
 or ax,[terminal_program_active]
 or ax,[terminal_macro_active]
 or ax,[terminal_tx_count]
 or ax,[terminal_clipboard_remaining]
 jnz .refuse
 cmp word [connection_state],0
 je .pointer
 cmp word [connection_state],6
 jne .refuse
.pointer:
 mov si,[bp+6]
 or si,si
 jz .refuse
 mov cx,[bp+8]
 jcxz .refuse
 cmp cx,196
 ja .refuse
 mov ax,si
 add ax,cx
 jc .refuse
 mov [terminal_clipboard_remaining],cx
 mov word [clipboard_failed],0
.copy:
 lodsb
 call terminal_enqueue_user_al
 loop .copy
 xor ax,ax
 jmp .done
.probe:
 cmp word [clipboard_failed],0
 jne .refuse
 mov ax,[terminal_clipboard_remaining]
 cmp ax,[terminal_tx_count]
 ja .lost
 jmp .done
.cancel:
 mov ax,[terminal_clipboard_remaining]
 cmp ax,[terminal_tx_count]
 ja .lost
 sub [terminal_tx_count],ax
 add ax,[terminal_tx_head]
 and ax,1023
 mov [terminal_tx_head],ax
 mov word [terminal_clipboard_remaining],0
 xor ax,ax
 jmp .done
.lost:
 call terminal_clipboard_abort
.refuse:
 mov ax,0xffff
.done:
 pop di
 pop si
 pop bp
 ret
; Called before connection owners discard the queue. Completion must never be
; inferred from a cleared ring: mark interrupted pastes failed for the UI.
terminal_clipboard_abort:
 cmp word [terminal_clipboard_remaining],0
 je .done
 mov word [clipboard_failed],1
 mov word [terminal_clipboard_remaining],0
.done:
 ret
SEGMENT _DATA public class=DATA use16
global terminal_clipboard_remaining
terminal_clipboard_remaining: dw 0
clipboard_failed: dw 0
