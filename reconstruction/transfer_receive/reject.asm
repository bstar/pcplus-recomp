; Exact original receiver instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_RECEIVE_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global receive_at_dbbc
global receive_at_dbc1
global receive_at_dbc3
global receive_at_dbc8
global receive_at_dbca
global receive_at_dbcc
global receive_at_dbcf
global receive_at_dbd2
global receive_at_dbd5
global receive_at_dbd8
global receive_at_dbdd
global receive_at_dbdf
global receive_at_dbe2
global receive_at_dbe4
global receive_at_dbe8
global receive_at_dbea
global receive_at_dbed
global receive_at_dbf0
global receive_at_dbf2
global receive_at_dbf5
global receive_at_dbf7
global receive_at_dbf8
global receive_at_dbfb
global receive_at_dbfc
global receive_at_dbff
global receive_at_dc02
global receive_at_dc07
global receive_at_dc0b
global receive_at_dc0d
global receive_at_dc11
global receive_at_dc14
global receive_at_dc17
global receive_at_dc1a
global receive_at_dc1f
global receive_at_dc23
global receive_at_dc25
extern receive_ack
extern receive_nak
extern receive_last_block
extern receive_wire_block
extern receive_error_count
extern receive_streaming_mode
extern receive_at_d976
extern receive_complete
extern receive_retry_limit
extern receive_status
extern receive_drain
%else
ORG 0xdbbc
%define receive_ack 0x40b1
%define receive_nak 0x40b9
%define receive_last_block 0xcc9a
%define receive_wire_block 0xcc9c
%define receive_error_count 0xcd8a
%define receive_streaming_mode 0xcdcc
%define receive_at_d976 0xd976
%define receive_complete 0xdc28
%define receive_retry_limit 0xdcf1
%define receive_status 0xe498
%define receive_drain 0xf03e
%endif
%include "encodings.inc"
receive_at_dbbc: cmp word [receive_streaming_mode],0x0
receive_at_dbc1: jnz short receive_at_dc07
receive_at_dbc3: mov word [bp-0x4],0x1
receive_at_dbc8: or_load di,di
receive_at_dbca: jz short receive_at_dbd2
receive_at_dbcc: mov ax,0x6
receive_at_dbcf: jmp near receive_at_d976
receive_at_dbd2: mov ax,0x5
receive_at_dbd5: jmp near receive_at_d976
receive_at_dbd8: cmp word [receive_streaming_mode],0x0
receive_at_dbdd: jnz short receive_at_dc07
receive_at_dbdf: mov al,[receive_last_block]
receive_at_dbe2: sub_load ah,ah
receive_at_dbe4: cmp ax,[receive_wire_block]
receive_at_dbe8: jnz short receive_at_dbf2
receive_at_dbea: call receive_drain
receive_at_dbed: call receive_ack
receive_at_dbf0: jmp short receive_at_dc07
receive_at_dbf2: mov ax,0x8
receive_at_dbf5: jmp short receive_at_dbfb
receive_at_dbf7: nop
receive_at_dbf8: mov ax,0x7
receive_at_dbfb: push ax
receive_at_dbfc: call receive_status
receive_at_dbff: add sp,0x2
receive_at_dc02: mov word [bp-0x4],0x1
receive_at_dc07: cmp word [bp-0x4],0x0
receive_at_dc0b: jz short receive_at_dc1f
receive_at_dc0d: inc word [receive_error_count]
receive_at_dc11: inc word [bp-0x14]
receive_at_dc14: call receive_drain
receive_at_dc17: call receive_nak
receive_at_dc1a: mov word [bp-0x4],0x0
receive_at_dc1f: cmp word [bp-0x14],0xf
receive_at_dc23: jnz short receive_complete
receive_at_dc25: jmp near receive_retry_limit
%ifdef TRANSFER_RECEIVE_OMF
jmp receive_complete
%endif
