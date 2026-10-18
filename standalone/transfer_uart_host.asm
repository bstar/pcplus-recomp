; Controlled UART diagnostic. UI callbacks are declared fixtures, not vendor UI.
BITS 16
CPU 8086
GROUP DGROUP _DATA
SEGMENT _TEXT public class=CODE use16
extern uart_save_hardware_state,uart_restore_hardware_state,uart_disable,uart_enable,uart_install_interrupt,uart_restore_interrupt
extern uart_set_baud_divisor,uart_set_line_control,uart_clear_receive_buffer,uart_available,uart_receive_byte,transfer_uart_send_bounded
extern uart_rx_count,uart_rx_read,uart_rx_write,uart_rx_buffer
GLOBAL _transfer_uart_dos_test
_transfer_uart_dos_test:
 push bp
 push si
 push di
 call uart_save_hardware_state
 call uart_disable
 mov ax,0x0c
 push ax
 call uart_install_interrupt
 pop bx
 mov ax,0
 push ax
 mov ax,38400
 push ax
 call uart_set_baud_divisor
 add sp,4
 mov ax,1
 push ax
 mov ax,8
 push ax
 mov ax,0
 push ax
 call uart_set_line_control
 add sp,6
 call uart_clear_receive_buffer
 call uart_enable
 mov ax,3
 push ax
 call uart_available
 cmp ax,0x5a
 jne .failed
 mov di,transfer_uart_payload
 xor ax,ax
 mov cx,1024
 push ds
 pop es
.fill:
 stosb
 inc al
 loop .fill
 mov ax,transfer_uart_payload
 push ax
 mov ax,1024
 push ax
 call transfer_uart_send_bounded
 add sp,4
 or ax,ax
 jnz .failed
 mov ax,3
 push ax
 call uart_available
 cmp ax,0xa5
 jne .failed
 ; The immediategetter must not confuse ring-empty with wireNUL.
 call uart_receive_byte
 cmp ax,0xffff
 jne .failed
 call uart_clear_receive_buffer
 cmp word [uart_rx_count],0
 jne .failed
 mov ax,[uart_rx_read]
 cmp ax,[uart_rx_write]
 jne .failed
 xor ax,ax
 jmp .cleanup
.failed: mov ax,1
.cleanup:
 push ax
 call uart_disable
 mov ax,0x0c
 push ax
 call uart_restore_interrupt
 pop bx
 call uart_restore_hardware_state
 pop ax
 pop di
 pop si
 pop bp
 ret
GLOBAL pcplus_flow_bell,pcplus_flow_message,pcplus_escape_pressed,pcplus_screen_restore,pcplus_screen_save
pcplus_flow_bell:
 inc word [transfer_fixture_flow_calls]
 ret
pcplus_flow_message: ret
pcplus_screen_restore:
pcplus_screen_save: ret 6
pcplus_escape_pressed:
 mov ax,[transfer_fixture_escape]
 ret
SEGMENT _DATA public class=DATA use16
global transfer_dos_clock_sample,transfer_uart_payload,transfer_fixture_escape,transfer_fixture_flow_calls
transfer_dos_clock_sample: times 4 dw 0
transfer_fixture_escape: dw 0
transfer_fixture_flow_calls: dw 0
transfer_uart_payload: times 1024 db 0
