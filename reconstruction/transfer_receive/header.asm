; Exact original receiver instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_RECEIVE_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global receive_at_dc6a
global receive_at_dc6e
global receive_at_dc70
global receive_at_dc74
global receive_at_dc76
global receive_at_dc7a
global receive_at_dc7c
global receive_at_dc82
global receive_at_dc86
global receive_at_dc88
global receive_at_dc8e
global receive_at_dc91
global receive_at_dc94
global receive_at_dc97
global receive_at_dc9a
global receive_at_dc9d
global receive_at_dca0
global receive_at_dca3
global receive_at_dca7
global receive_at_dcaa
global receive_at_dcac
global receive_at_dcb1
global receive_at_dcb3
global receive_at_dcb6
global receive_at_dcbb
global receive_at_dcbd
global receive_at_dcc0
global receive_at_dcc5
global receive_at_dcc7
global receive_at_dcca
global receive_at_dccf
global receive_at_dcd1
global receive_at_dcd6
global receive_at_dcd8
global receive_at_dcdd
global receive_at_dcdf
global receive_at_dce2
global receive_at_dce7
global receive_at_dcea
global receive_at_dcef
global receive_retry_limit
global receive_at_dcf5
global receive_at_dcf7
global receive_at_dcfa
extern receive_protocol
extern receive_ack
extern receive_header_byte
extern receive_block_size
extern receive_last_block
extern receive_wire_block
extern receive_wire_complement
extern receive_streaming_mode
extern receive_unsupported_control
extern receive_at_d8e8
extern receive_at_d8ed
extern receive_at_dbf8
extern receive_other_control
extern receive_eot
%else
ORG 0xdc6a
%define receive_protocol 0x3996
%define receive_ack 0x40b1
%define receive_header_byte 0x5ca0
%define receive_block_size 0xcb5e
%define receive_last_block 0xcc9a
%define receive_wire_block 0xcc9c
%define receive_wire_complement 0xcd32
%define receive_streaming_mode 0xcdcc
%define receive_unsupported_control 0xd734
%define receive_at_d8e8 0xd8e8
%define receive_at_d8ed 0xd8ed
%define receive_at_dbf8 0xdbf8
%define receive_other_control 0xdd4a
%endif
%include "encodings.inc"
receive_at_dc6a: cmp word [bp-0x10],0x1
receive_at_dc6e: jz short receive_at_dc7c
receive_at_dc70: cmp word [bp-0x10],0x16
receive_at_dc74: jz short receive_at_dc7c
receive_at_dc76: cmp word [bp-0x10],0x2
receive_at_dc7a: jnz short receive_at_dcea
receive_at_dc7c: mov word [receive_block_size],0x80
receive_at_dc82: cmp word [bp-0x10],0x2
receive_at_dc86: jnz short receive_at_dc8e
receive_at_dc88: mov word [receive_block_size],0x400
receive_at_dc8e: mov ax,0xffff
receive_at_dc91: mov [bp-0x2],ax
receive_at_dc94: mov [bp-0x10],ax
receive_at_dc97: call receive_header_byte
receive_at_dc9a: mov [receive_wire_block],ax
receive_at_dc9d: call receive_header_byte
receive_at_dca0: mov [receive_wire_complement],ax
receive_at_dca3: add ax,[receive_wire_block]
receive_at_dca7: cmp ax,0xff
receive_at_dcaa: jz short receive_at_dcb6
receive_at_dcac: cmp word [receive_streaming_mode],0x0
receive_at_dcb1: jnz short receive_at_dcb6
receive_at_dcb3: jmp near receive_at_dbf8
receive_at_dcb6: cmp word [receive_last_block],0x0
receive_at_dcbb: jz short receive_at_dcc0
receive_at_dcbd: jmp near receive_at_d8ed
receive_at_dcc0: cmp word [receive_wire_block],0x0
receive_at_dcc5: jz short receive_at_dcca
receive_at_dcc7: jmp near receive_at_d8e8
receive_at_dcca: cmp word [receive_protocol],0x3
receive_at_dccf: jz short receive_at_dce2
receive_at_dcd1: cmp word [receive_protocol],0x5
receive_at_dcd6: jz short receive_at_dce2
receive_at_dcd8: cmp word [receive_protocol],0xb
receive_at_dcdd: jz short receive_at_dce2
receive_at_dcdf: jmp near receive_at_d8e8
receive_at_dce2: mov word [bp-0xe],0x1
receive_at_dce7: jmp near receive_at_d8ed
receive_at_dcea: cmp word [receive_streaming_mode],0x0
receive_at_dcef: jz short receive_other_control
receive_retry_limit: cmp word [bp-0x10],0x4
receive_at_dcf5: jz short receive_at_dcfa
receive_at_dcf7: jmp near receive_unsupported_control
receive_at_dcfa: call receive_ack
%ifdef TRANSFER_RECEIVE_OMF
jmp receive_eot
%endif
