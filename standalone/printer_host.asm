; Memory-CRT diagnostic only. Never opens a real DOS PRN or source file.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern printer_byte_original,printer_toggle_original,terminal_log_character

global _printer_dos_test
_printer_dos_test:
 push bp
 mov bp,sp
 push bx
 push si
 push di
 push es
 mov [fixture_expected_sp],sp
 mov [fixture_expected_bp],bp
 mov ax,ds
 mov [fixture_expected_ds],ax
 mov si,0x1357
 mov di,0x2468
 mov word [printer_enabled],1
 mov word [printer_stream],0x1111
 mov word [terminal_sink_398a_enabled],0
 mov word [fixture_wire_count],0
 mov ax,'A'
 push ax
 call printer_byte_original
 pop bx
 cmp word [fixture_putc_calls],1
 jne .fail1
 cmp word [fixture_flush_calls],1
 jne .fail1
 cmp byte [fixture_wire],'A'
 jne .fail1
 mov word [terminal_cr_adds_lf],0
 mov ax,13
 push ax
 call terminal_log_character
 pop bx
 cmp word [fixture_wire_count],2
 jne .fail2
 cmp byte [fixture_wire+1],13
 jne .fail2
 mov word [terminal_cr_adds_lf],1
 mov ax,13
 push ax
 call terminal_log_character
 pop bx
 cmp word [fixture_wire_count],4
 jne .fail2
 cmp word [fixture_wire+2],0x0a0d
 jne .fail2
 mov ax,255
 push ax
 call terminal_log_character
 pop bx
 mov ax,127
 push ax
 call terminal_log_character
 pop bx
 cmp word [fixture_wire_count],4
 jne .fail2
 ; Direct native byte wrapper does not apply loggerFF/DEL filtering.
 mov ax,255
 push ax
 call printer_byte_original
 pop bx
 mov ax,127
 push ax
 call printer_byte_original
 pop bx
 cmp word [fixture_wire_count],6
 jne .fail2
 cmp word [fixture_wire+4],0x7fff
 jne .fail2
 ; Original open failure leaves enabled1/FILE0. Fixture observes null use.
 mov word [printer_enabled],0
 mov word [fixture_open_result],0
 call printer_toggle_original
 cmp word [printer_enabled],1
 jne .fail3
 cmp word [printer_stream],0
 jne .fail3
 mov ax,'Z'
 push ax
 call printer_byte_original
 pop bx
 cmp word [fixture_last_handle],0
 jne .fail3
 mov word [fixture_close_result],0xffff
 call printer_toggle_original
 cmp word [printer_enabled],0
 jne .fail3
 cmp word [fixture_close_calls],1
 jne .fail3
 mov word [fixture_putc_result],0xffff
 mov word [fixture_flush_result],0x1234
 mov ax,'X'
 push ax
 call printer_byte_original
 pop bx
 cmp ax,0x1234
 jne .fail4
 cmp word [fixture_flush_calls],8
 jne .fail4
 cmp si,0x1357
 jne .fail5
 cmp di,0x2468
 jne .fail5
 cmp bp,[fixture_expected_bp]
 jne .fail5
 cmp sp,[fixture_expected_sp]
 jne .fail5
 mov ax,ds
 cmp ax,[fixture_expected_ds]
 jne .fail5
 mov ax,ss
 cmp ax,[fixture_expected_ds]
 jne .fail5
 cmp word [fixture_guard_after],0xa55a
 jne .fail5
 cmp word [fixture_guard_before],0x5aa5
 jne .fail5
 xor ax,ax
 jmp .return
.fail1:
 mov ax,1
 jmp .return
.fail2:
 mov ax,2
 jmp .return
.fail3:
 mov ax,3
 jmp .return
.fail4:
 mov ax,4
 jmp .return
.fail5:
 mov ax,5
.return:
 pop es
 pop di
 pop si
 pop bx
 pop bp
 ret

global terminal_sink_36fc,terminal_sink_8436,terminal_sink_427f,terminal_sink_bb23,screen_viewport_refresh
terminal_sink_36fc:
 jmp printer_byte_original
terminal_sink_8436:
 jmp printer_putc
terminal_sink_427f:
 push ax
 mov al,'E'
 call fixture_trace_event
 pop ax
 inc word [fixture_capture_error_calls]
 ret
terminal_sink_bb23:
 push ax
 mov al,'L'
 call fixture_trace_event
 pop ax
 inc word [fixture_capture_close_calls]
 mov word [terminal_sink_398a_enabled],0
 ret
screen_viewport_refresh:
 jmp printer_status

global printer_open,printer_close,printer_putc,printer_flush,printer_status
printer_open:
 push ax
 mov al,'O'
 call fixture_trace_event
 pop ax
 push bp
 mov bp,sp
 inc word [fixture_open_calls]
 mov ax,[bp+4]
 mov [fixture_last_filename],ax
 mov ax,[bp+6]
 mov [fixture_last_mode],ax
 mov ax,[fixture_open_result]
 pop bp
 ret
printer_close:
 push ax
 mov al,'C'
 call fixture_trace_event
 pop ax
 push bp
 mov bp,sp
 inc word [fixture_close_calls]
 mov ax,[bp+4]
 mov [fixture_last_handle],ax
 mov ax,[fixture_close_result]
 pop bp
 ret
printer_putc:
 push ax
 mov al,'P'
 call fixture_trace_event
 pop ax
 push bp
 mov bp,sp
 push bx
 inc word [fixture_putc_calls]
 mov ax,[bp+6]
 mov [fixture_last_handle],ax
 mov dx,[fixture_putc_result]
 cmp ax,[terminal_sink_handle]
 jne .selected
 mov dx,[fixture_capture_putc_result]
.selected:
 cmp dx,0xffff
 je .failed
 mov bx,[fixture_wire_count]
 cmp bx,256
 jae .overflow
 mov ax,[bp+4]
 mov [fixture_wire+bx],al
 inc word [fixture_wire_count]
 mov ax,dx
 jmp .return
.failed:
 mov ax,0xffff
.return:
 pop bx
 pop bp
 ret
.overflow:
 int3
 jmp .overflow
printer_flush:
 push ax
 mov al,'F'
 call fixture_trace_event
 pop ax
 push bp
 mov bp,sp
 inc word [fixture_flush_calls]
 mov ax,[bp+4]
 mov [fixture_last_handle],ax
 mov ax,[fixture_flush_result]
 pop bp
 ret
printer_status:
 push ax
 mov al,'S'
 call fixture_trace_event
 pop ax
 inc word [fixture_status_calls]
 ret

fixture_trace_event:
 push bx
 mov bx,[fixture_trace_count]
 cmp bx,256
 jae .overflow
 mov [fixture_trace+bx],al
 inc word [fixture_trace_count]
 pop bx
 ret
.overflow:
 int3
 jmp .overflow

SEGMENT _DATA public class=DATA use16
global printer_enabled,terminal_sink_3988_enabled
printer_enabled:
terminal_sink_3988_enabled dw 0
global printer_stream,printer_device,printer_binary_mode
printer_stream dw 0x1111
printer_device db 'PRN',0
printer_binary_mode db 'wb',0
global terminal_cr_adds_lf,terminal_sink_398a_enabled,terminal_sink_398c_disabled,terminal_sink_handle,terminal_sink_error_state
terminal_cr_adds_lf dw 0
terminal_sink_398a_enabled dw 0
terminal_sink_398c_disabled dw 0
terminal_sink_handle dw 0x2222
terminal_sink_error_state dw 0
global fixture_open_result,fixture_putc_result,fixture_flush_result,fixture_close_result
fixture_open_result dw 0x1111
fixture_putc_result dw 0
global fixture_capture_putc_result
fixture_capture_putc_result dw 0
fixture_flush_result dw 0
fixture_close_result dw 0
global fixture_open_calls,fixture_putc_calls,fixture_flush_calls,fixture_close_calls,fixture_status_calls
fixture_open_calls dw 0
fixture_putc_calls dw 0
fixture_flush_calls dw 0
fixture_close_calls dw 0
fixture_status_calls dw 0
global fixture_last_handle,fixture_last_filename,fixture_last_mode
fixture_last_handle dw 0
fixture_last_filename dw 0
fixture_last_mode dw 0
global fixture_wire_count,fixture_wire,fixture_capture_error_calls,fixture_capture_close_calls
fixture_wire_count dw 0
fixture_capture_error_calls dw 0
fixture_capture_close_calls dw 0
global fixture_guard_before,fixture_guard_after
fixture_guard_before dw 0x5aa5
fixture_wire times 256 db 0
fixture_guard_after dw 0xa55a
fixture_expected_sp dw 0
fixture_expected_bp dw 0
fixture_expected_ds dw 0

global fixture_trace_count,fixture_trace
fixture_trace_count dw 0
fixture_trace times 256 db 0
