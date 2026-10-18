; Maintained extent guard; does not turn original blocking UART into async IO.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_transmit_buffer
global transfer_uart_send_bounded
; Near C (count1..1024,DS:pointer), caller4. AX0 sent,1 invalid before ports.
; Preserve BP/SI/DI. Endpoint=10000h accepted; pointer must be nonzero.
transfer_uart_send_bounded:
 push bp
 mov bp,sp
 mov cx,[bp+4]
 jcxz .invalid
 cmp cx,1024
 ja .invalid
 mov ax,[bp+6]
 or ax,ax
 jz .invalid
 add ax,cx
 jnc .send
 or ax,ax
 jnz .invalid
.send:
 push word [bp+6]
 push cx
 call uart_transmit_buffer
 xor ax,ax
 pop bp
 ret
.invalid:
 mov ax,1
 pop bp
 ret
