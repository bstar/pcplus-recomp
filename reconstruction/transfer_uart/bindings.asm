; Source-owned zero-policy tail aliases onto the existing recovered UART core.
BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern uart_available,uart_transmit_buffer,uart_clear_receive_buffer,uart_receive_byte,uart_transmit_byte,transfer_uart_header_byte
%macro alias 2
 global %1
 %1: jmp %2
%endmacro
alias send_timed_byte,uart_available
alias receive_timed_byte,uart_available
alias send_transmit_buffer,uart_transmit_buffer
alias send_transmit_byte,uart_transmit_byte
alias receive_transmit_byte,uart_transmit_byte
alias send_flush_input,uart_clear_receive_buffer
alias receive_flush_input,uart_clear_receive_buffer
alias send_receive_byte,uart_receive_byte
alias send_header_byte,transfer_uart_header_byte
alias receive_header_byte,transfer_uart_header_byte
