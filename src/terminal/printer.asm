; Maintained processed printer copy. Native09B6 owns filtering/newline policy.
; Foreground queue only: no DOS calls from the logger or UART ISR.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _printer_device_begin,_printer_device_ready,_printer_device_write
extern _printer_device_close,_printer_device_result
extern terminal_sink_3988_enabled,csi_printer_ready
extern terminal_clock_ticks,uart_poll_flow
extern terminal_monitor_active,terminal_parser_active,terminal_ansi_wait_active
extern terminal_macro_active,terminal_program_pending,connection_state
extern terminal_transfer_active,terminal_transfer_pending
extern terminal_connection_notice
global terminal_printer_toggle,terminal_printer_poll,terminal_sink_36fc
global terminal_printer_receive_hold,terminal_printer_barrier
global terminal_printer_before_program,terminal_printer_shutdown
global terminal_printer_put_raw,terminal_printer_failure
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
terminal_printer_toggle:
 save
 cmp word [terminal_sink_3988_enabled],0
 je .open
 ; Stop new admission immediately; poll drains before closing the owner.
 mov word [terminal_sink_3988_enabled],0
 mov word [terminal_printer_closing],1
 mov si,printer_draining
 jmp .notice
.open:
 cmp word [terminal_printer_closing],0
 jne .denied
 cmp word [_printer_device_result+12],0
 jne .denied
 cmp word [terminal_monitor_active],0
 jne .denied
 cmp word [terminal_parser_active],0
 jne .denied
 cmp word [terminal_ansi_wait_active],0
 jne .denied
 cmp word [terminal_macro_active],0
 jne .denied
 cmp word [terminal_program_pending],0
 jne .denied
 cmp word [terminal_transfer_active],0
 jne .denied
 cmp word [terminal_transfer_pending],0
 jne .denied
 cmp word [connection_state],0
 je .begin
 cmp word [connection_state],6
 jne .denied
.begin:
 call _printer_device_begin
 or ax,ax
 jz .ready
 cmp ax,5 ; Open denied without acquired handle is a nonsticky UI denial.
 je .denied
 call printer_failure
 jmp .done
.ready:
 call _printer_device_ready
 cmp ax,1
 ja .failed
 mov word [csi_printer_ready],0
 or ax,ax
 jnz .enabled
 inc word [csi_printer_ready]
.enabled:
 mov word [terminal_sink_3988_enabled],1
 mov si,printer_on
 jmp .notice
.failed:
 call printer_failure
 jmp .done
.denied:
 mov si,printer_denied
.notice:
 call terminal_connection_notice
.done:
 restore

; near cdecl(c). Native ignores return value. Maximum two queued bytes per
; received character (CR plus optional LF); main stops RX dequeue at127.
terminal_sink_36fc:
 cmp word [terminal_sink_3988_enabled],0
 jne terminal_printer_put_raw
 ret
; Internal byte admission for a separately owned screen-print operation. This
; bypasses processed-character filtering and does not turn stream copying on.
terminal_printer_put_raw:
 push bp
 mov bp,sp
 push bx
 cmp word [terminal_printer_count],128
 jae .overflow
 mov bx,[terminal_printer_tail]
 mov ax,[bp+4]
 mov [terminal_printer_buffer+bx],al
 inc bx
 and bx,127
 mov [terminal_printer_tail],bx
 inc word [terminal_printer_count]
 cmp word [terminal_printer_count],1
 jne .done
 push dx
 call printer_progress
 pop dx
 jmp .done
.overflow:
 cmp word [terminal_printer_sticky],0
 jne .stop
 mov word [terminal_printer_sticky],13
.stop:
 mov word [printer_fault_pending],13
 mov word [terminal_sink_3988_enabled],0
 mov word [terminal_printer_closing],1
 ; Preserve all128 pending bytes; deferred poll reports the sticky failure.
.done:
 pop bx
 pop bp
 ret

terminal_printer_receive_hold:
 xor ax,ax
 cmp word [terminal_sink_3988_enabled],0
 je .done
 cmp word [terminal_printer_count],126
 jbe .done
 inc ax
.done: ret

terminal_printer_barrier:
 xor ax,ax
 cmp word [terminal_printer_count],0
 je .done
 mov ax,2
.done: ret

; PROGRAM retries at its foreground safe point until close resolves. No child
; inherits PRN; uncertain close cancels launch. Sticky resolved errors remain.
terminal_printer_before_program:
 cmp word [_printer_device_result+12],0
 jne .uncertain
 cmp word [_printer_device_result+10],0
 je .done
 mov word [terminal_sink_3988_enabled],0
 mov word [terminal_printer_closing],1
 mov ax,2
 ret
.uncertain:
 mov ax,1
 ret
.done:
 xor ax,ax
 ret

terminal_printer_poll:
 save
 cmp word [printer_fault_pending],0
 je .queue
 cmp word [_printer_device_result+10],0
 jne .sticky_failure
 jmp .done
.sticky_failure:
 mov ax,[printer_fault_pending]
 jmp .failed
.queue:
 mov cx,16
.next:
 cmp word [terminal_printer_count],0
 je .empty
 mov bx,[terminal_printer_head]
 xor ax,ax
 mov al,[terminal_printer_buffer+bx]
 push cx
 push ax
 call _printer_device_write
 add sp,2
 pop cx
 cmp ax,1
 je .busy
 or ax,ax
 jnz .failed
 mov word [csi_printer_ready],1
 mov bx,[terminal_printer_head]
 inc bx
 and bx,127
 mov [terminal_printer_head],bx
 dec word [terminal_printer_count]
 call printer_progress
 loop .next
 jmp .done
.busy:
 mov word [csi_printer_ready],0
 mov si,printer_progress_tick
 call printer_elapsed
 or dx,dx
 jnz .timeout
 cmp ax,18
 jb .done
.timeout:
 mov ax,14
.failed:
 call printer_failure
 jmp .done
.empty:
 cmp word [terminal_printer_closing],0
 je .done
 call _printer_device_close
 mov word [terminal_printer_closing],0
 mov word [csi_printer_ready],0
 or ax,ax
 jnz .failed
 mov si,printer_off
 call terminal_connection_notice
.done:
 restore

printer_progress:
 call terminal_clock_ticks
 mov [printer_progress_tick],ax
 mov [printer_progress_tick+2],dx
 ret
printer_elapsed:
 call terminal_clock_ticks
 sub ax,[si]
 sbb dx,[si+2]
 jnc .done
 add ax,0x00b0
 adc dx,0x0018
.done: ret

; AX is the first app/backend error. Drop remaining bytes explicitly on fault;
; don't retry a possibly partially accepted write or uncertain close.
terminal_printer_failure:
printer_failure:
 inc word [terminal_printer_fault_epoch]
 cmp word [terminal_printer_sticky],0
 jne .close
 mov [terminal_printer_sticky],ax
.close:
 mov word [printer_fault_pending],0
 mov word [terminal_sink_3988_enabled],0
 mov word [terminal_printer_count],0
 mov word [terminal_printer_head],0
 mov word [terminal_printer_tail],0
 mov word [terminal_printer_closing],0
 mov word [csi_printer_ready],0
 call _printer_device_close
 mov si,printer_error
 call terminal_connection_notice
 ret

; Called before UART teardown. Drain with flow/IRQ service, with an independent
; total36-daytick bound as well as poll's18-tick no-progress bound. DOS device
; calls can themselves block; an application timer cannot interrupt a driver.
terminal_printer_shutdown:
 push bp
 push bx
 push cx
 push dx
 push si
 push di
 push es
 cmp word [_printer_device_result+10],0
 je .result
 mov word [terminal_sink_3988_enabled],0
 mov word [terminal_printer_closing],1
 call terminal_clock_ticks
 mov [printer_shutdown_tick],ax
 mov [printer_shutdown_tick+2],dx
.drain:
 call uart_poll_flow
 call terminal_printer_poll
 cmp word [_printer_device_result+10],0
 je .result
 mov si,printer_shutdown_tick
 call printer_elapsed
 or dx,dx
 jnz .timeout
 cmp ax,36
 jb .drain
.timeout:
 mov ax,14
 call printer_failure
.result:
 mov ax,[terminal_printer_sticky]
 pop es
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop bp
 ret

SEGMENT _DATA public class=DATA use16
global terminal_printer_count,terminal_printer_head,terminal_printer_tail
global terminal_printer_buffer,terminal_printer_closing,terminal_printer_sticky
global terminal_printer_fault_epoch
terminal_printer_fault_epoch: dw 0
terminal_printer_count: dw 0
terminal_printer_head: dw 0
terminal_printer_tail: dw 0
terminal_printer_closing: dw 0
terminal_printer_sticky: dw 0
printer_fault_pending: dw 0
printer_progress_tick: dd 0
printer_shutdown_tick: dd 0
terminal_printer_buffer: times 128 db 0
printer_on: db 'Printer on',0
printer_off: db 'Printer off',0
printer_draining: db 'Printer drain',0
printer_denied: db 'Printer denied',0
printer_error: db 'Printer error',0
