; Relocatable adaptation of the already recovered46-byte BIOS header timeout.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef TRANSFER_UART_OMF
SEGMENT _TEXT public class=CODE use16
global transfer_uart_header_byte
extern uart_rx_count,uart_receive_byte
%else
ORG 0x5ca0
%define uart_rx_count 0x8e20
%define uart_receive_byte 0xaa65
%endif
transfer_uart_header_byte:
 cmp word [uart_rx_count],byte 0
 jnz short .read
 mov dx,36
 sti
 xor_load cx,cx
 mov es,cx
 mov bx,0x46c
.tick:
 mov ax,[es:bx]
.wait:
 cmp word [uart_rx_count],byte 0
 jnz short .read
 cmp ax,[es:bx]
 jz short .wait
 inc cx
 cmp_load cx,dx
 jb short .tick
 mov ax,0xffff
 ret
.read:
 call uart_receive_byte
 ret
