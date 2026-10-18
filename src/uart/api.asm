; Maintained host API layered over the recovered driver. All calls are bounded.
; DS=SS, near calls. try_write takes AL, preserves AX/DX, CF=1 when busy.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_tx_paused, uart_hardware_flow, uart_port_msr, uart_port_lsr
extern uart_port_thr, uart_flow_pending
global uart_try_write, uart_poll_flow
uart_try_write:
 push ax
 push dx
 cmp word [uart_tx_paused],0
 jne .busy
 cmp word [uart_hardware_flow],1
 jne .ready
 mov dx,[uart_port_msr]
 in al,dx
 test al,0x10
 jz .busy
.ready:
 mov dx,[uart_port_lsr]
 in al,dx
 test al,0x20
 jz .busy
 pop dx
 pop ax
 push dx
 mov dx,[uart_port_thr]
 out dx,al
 pop dx
 clc
 ret
.busy:
 pop dx
 pop ax
 stc
 ret

; Queueing XON/XOFF avoids spinning on THRE inside the receive interrupt.
; Poll once from the foreground loop. Never applies CTS/XOFF to control bytes.
uart_poll_flow:
 pushf
 cli
 push ax
 push dx
 cmp byte [uart_flow_pending],0
 je .done
 mov dx,[uart_port_lsr]
 in al,dx
 test al,0x20
 jz .done
 mov al,[uart_flow_pending]
 mov dx,[uart_port_thr]
 out dx,al
 mov byte [uart_flow_pending],0
.done:
 pop dx
 pop ax
 popf
 ret
