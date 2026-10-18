; Exact original receiver instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_RECEIVE_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global receive_drain
global receive_at_f041
global receive_at_f042
global receive_at_f045
global receive_at_f048
global receive_at_f04d
global receive_at_f04f
extern receive_delay
extern receive_queued_count
extern receive_flush_input
%else
ORG 0xf03e
%define receive_delay 0x6b72
%define receive_queued_count 0x8e20
%define receive_flush_input 0xabca
%endif
%include "encodings.inc"
receive_drain: mov ax,0x32
receive_at_f041: push ax
receive_at_f042: call receive_delay
receive_at_f045: call receive_flush_input
receive_at_f048: cmp word [receive_queued_count],0x0
receive_at_f04d: jnz short receive_drain
receive_at_f04f: ret
