; Exact original receiver instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_RECEIVE_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global receive_at_daea
global receive_at_daef
global receive_at_daf1
global receive_at_daf6
global receive_at_daf9
global receive_at_dafc
global receive_at_db00
global receive_at_db04
global receive_at_db07
global receive_at_db0b
global receive_at_db0c
global receive_at_db10
global receive_at_db14
global receive_at_db18
global receive_at_db1c
global receive_at_db1f
global receive_at_db25
global receive_at_db27
extern receive_ack
extern receive_total_low
extern receive_total_high
extern receive_flush_input
extern receive_session_low
extern receive_session_high
extern receive_block_size
extern receive_last_block
extern receive_buffer_used
extern receive_blocks_accepted
extern receive_streaming_mode
extern receive_buffer_full
extern receive_at_dc07
extern receive_progress
%else
ORG 0xdaea
%define receive_ack 0x40b1
%define receive_total_low 0x8ffa
%define receive_total_high 0x8ffc
%define receive_flush_input 0xabca
%define receive_session_low 0xcb2c
%define receive_session_high 0xcb2e
%define receive_block_size 0xcb5e
%define receive_last_block 0xcc9a
%define receive_buffer_used 0xcd34
%define receive_blocks_accepted 0xcd80
%define receive_streaming_mode 0xcdcc
%define receive_buffer_full 0xdb2a
%define receive_at_dc07 0xdc07
%define receive_progress 0xe322
%endif
%include "encodings.inc"
receive_at_daea: cmp word [receive_streaming_mode],0x0
receive_at_daef: jnz short receive_at_dafc
receive_at_daf1: mov word [bp-0x14],0x0
receive_at_daf6: call receive_flush_input
receive_at_daf9: call receive_ack
receive_at_dafc: inc word [receive_blocks_accepted]
receive_at_db00: inc word [receive_last_block]
receive_at_db04: mov ax,[receive_block_size]
receive_at_db07: add [receive_buffer_used],ax
receive_at_db0b: cwd
receive_at_db0c: add [receive_total_low],ax
receive_at_db10: adc [receive_total_high],dx
receive_at_db14: add [receive_session_low],ax
receive_at_db18: adc [receive_session_high],dx
receive_at_db1c: call receive_progress
receive_at_db1f: cmp word [receive_buffer_used],0x2800
receive_at_db25: jnc short receive_buffer_full
receive_at_db27: jmp near receive_at_dc07
%ifdef TRANSFER_RECEIVE_OMF
jmp receive_buffer_full
%endif
