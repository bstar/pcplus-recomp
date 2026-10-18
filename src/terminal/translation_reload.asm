; Maintained same-table reload over the drained PROGRAM foreground owner.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern terminal_translation_mode,terminal_translation_enabled,terminal_translation_table
extern terminal_program_start,terminal_program_kind,terminal_macro_active
extern terminal_parser_active,terminal_transfer_pending,terminal_transfer_active
extern terminal_monitor_active,terminal_controller_active,terminal_snapshot_active
extern terminal_ansi_wait_active,_redisplay_active,uart_rx_mask
extern _xlt_live_reload,terminal_connection_notice
extern terminal_read_foreground_key
global terminal_translation_reload_start,terminal_translation_reload_run
reload_safe:
 mov ax,[terminal_parser_active]
 or ax,[terminal_macro_active]
 or ax,[terminal_transfer_pending]
 or ax,[terminal_transfer_active]
 or ax,[terminal_monitor_active]
 or ax,[terminal_controller_active]
 or ax,[terminal_snapshot_active]
 or ax,[terminal_ansi_wait_active]
 or ax,[_redisplay_active]
 jnz .done
 cmp word [terminal_translation_mode],1
 jne .unsafe
 cmp word [terminal_translation_enabled],1
 jne .unsafe
 cmp word [uart_rx_mask],255
 je .done
.unsafe:
 mov ax,1
.done:
 ret
terminal_translation_reload_start:
 push si
 call reload_safe
 or ax,ax
 jnz .denied
 mov ax,reload_command
 call terminal_program_start
 or ax,ax
 jnz .denied
 mov word [terminal_program_kind],2
 mov word [terminal_translation_reload_status],1
 pop si
 ret
.denied:
 mov word [terminal_translation_reload_status],4
 mov si,reload_unavailable
 call terminal_connection_notice
 mov ax,1
 pop si
 ret

; Called after UART/IRQ handoff. No DOS child is launched and no PRM is read.
terminal_translation_reload_run:
 push bp
 push si
 push di
 push es
 call reload_safe
 or ax,ax
 jnz .unsafe
 xor ax,ax
 xor dx,dx
 call reload_event
 or ax,ax
 jnz .failed
 mov si,reload_question
 call reload_text
 call terminal_read_foreground_key
 cmp al,'Y'
 je .accept
 cmp al,'y'
 je .accept
 mov ax,2
 xor dx,dx
 call reload_event
 mov word [terminal_translation_reload_status],3
 xor ax,ax
 jmp .done
.accept:
 call reload_safe
 or ax,ax
 jnz .cancel_unsafe
 mov ax,1
 mov dx,terminal_translation_table
 call reload_event
 or ax,ax
 jnz .failed
 mov word [terminal_translation_reload_status],2
 xor ax,ax
 jmp .done
.cancel_unsafe:
 mov ax,2
 xor dx,dx
 call reload_event
.unsafe:
 mov word [terminal_translation_reload_io],7
 mov word [terminal_translation_reload_status],6
 jmp .error
.failed:
 mov word [terminal_translation_reload_status],5
.error:
 mov si,reload_failed
 call reload_text
 call terminal_read_foreground_key
 mov ax,1
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
reload_event:
 mov bx,terminal_translation_reload_io
 push bx
 push dx
 push ax
 call _xlt_live_reload
 add sp,6
 ret
reload_text:
 lodsb
 or al,al
 jz .done
 mov ah,0x0e
 xor bh,bh
 mov bl,7
 int 0x10
 jmp reload_text
.done:
 ret
SEGMENT _DATA public class=DATA use16
global terminal_translation_reload_status,terminal_translation_reload_io
terminal_translation_reload_status: dw 0 ;1queued,2applied,3declined,4unavailable,5IO,6unsafe.
terminal_translation_reload_io: times 4 dw 0
reload_command: db 'Reload input table',0
reload_unavailable: db 'Input table reload unavailable.',0
reload_question: db 13,10,'Reload input table? Queued input uses new table. Y applies; other keys keep table.',0
reload_failed: db 13,10,'Input table reload failed; old table retained. Press a key.',0
