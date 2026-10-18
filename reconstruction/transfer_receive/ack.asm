; Exact original receiver instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_RECEIVE_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global receive_ack
global receive_at_40b4
global receive_at_40b5
global receive_at_40b8
global receive_nak
global receive_at_40bc
global receive_at_40bd
global receive_at_40c0
extern receive_transmit_byte
%else
ORG 0x40b1
%define receive_transmit_byte 0xab0b
%endif
%include "encodings.inc"
receive_ack: mov ax,0x6
receive_at_40b4: push ax
receive_at_40b5: call receive_transmit_byte
receive_at_40b8: ret
receive_nak: mov ax,0x15
receive_at_40bc: push ax
receive_at_40bd: call receive_transmit_byte
receive_at_40c0: ret
