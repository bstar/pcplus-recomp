; Resume a software-paused peer before giving the UART back to DOS.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_software_flow,uart_xoff_sent,uart_flow_pending,uart_poll_flow
extern terminal_clock_ticks,terminal_exit_code
global terminal_release_flow
terminal_release_flow:
 push bp
 push si
 push di
 push es
 cmp word [uart_software_flow],0
 je .done
 cmp byte [uart_xoff_sent],0
 jne .resume
 cmp byte [uart_flow_pending],0x11
 jne .done
.resume:
 mov byte [uart_xoff_sent],0
 mov byte [uart_flow_pending],0x11
 call terminal_clock_ticks
 mov si,ax
 mov bp,dx
.poll:
 call uart_poll_flow
 cmp byte [uart_flow_pending],0
 je .done
 call terminal_clock_ticks
 sub ax,si
 sbb dx,bp
 jnc .elapsed
 add ax,0x00b0
 adc dx,0x0018
.elapsed:
 or dx,dx
 jnz .failed
 cmp ax,36
 jb .poll
.failed:
 mov word [terminal_cleanup_flow_failed],1
 cmp word [terminal_exit_code],0
 jne .done
 mov word [terminal_exit_code],11
.done:
 pop es
 pop di
 pop si
 pop bp
 ret
SEGMENT _DATA public class=DATA use16
global terminal_cleanup_flow_failed
terminal_cleanup_flow_failed: dw 0
