; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_initialize
global session_at_d658
global session_at_d65b
global session_at_d65e
global session_at_d661
global session_at_d664
global session_at_d667
global session_at_d66a
global session_at_d66d
global session_at_d673
global session_at_d678
global session_at_d67a
global session_at_d67f
global session_at_d681
global session_at_d684
global session_at_d686
global session_at_d68c
global session_at_d690
global session_at_d692
global session_at_d694
global session_at_d698
global session_at_d69c
global session_at_d69f
global session_at_d6a3
extern session_baud_index
extern session_baud_table
extern session_baud_table_high
extern session_blocks_accepted
extern session_buffer_pointer
extern session_error_count
extern session_file_handle
extern session_payload
extern session_protocol
extern session_rate_high
extern session_rate_low
extern session_state_cb3a
extern session_state_cb54
extern session_state_cb56
extern session_state_cd7a
extern session_streaming_mode
%else
ORG 0xd656
%define session_baud_index 0x1b86
%define session_baud_table 0x3270
%define session_baud_table_high 0x3272
%define session_blocks_accepted 0xcd80
%define session_buffer_pointer 0x39c0
%define session_error_count 0xcd8a
%define session_file_handle 0xcbaa
%define session_payload 0x9062
%define session_protocol 0x3996
%define session_rate_high 0x905c
%define session_rate_low 0x905a
%define session_state_cb3a 0xcb3a
%define session_state_cb54 0xcb54
%define session_state_cb56 0xcb56
%define session_state_cd7a 0xcd7a
%define session_streaming_mode 0xcdcc
%endif
%include "encodings.inc"
session_initialize: sub_load ax,ax
session_at_d658: mov [session_state_cb56],ax
session_at_d65b: mov [session_state_cb54],ax
session_at_d65e: mov [session_state_cb3a],ax
session_at_d661: mov [session_error_count],ax
session_at_d664: mov [session_blocks_accepted],ax
session_at_d667: mov [session_state_cd7a],ax
session_at_d66a: mov [session_file_handle],ax
session_at_d66d: mov word [session_buffer_pointer],session_payload
session_at_d673: cmp word [session_protocol],0xa
session_at_d678: jz short session_at_d686
session_at_d67a: cmp word [session_protocol],0xb
session_at_d67f: jz short session_at_d686
session_at_d681: mov [session_streaming_mode],ax
session_at_d684: jmp short session_at_d68c
session_at_d686: mov word [session_streaming_mode],0x1
session_at_d68c: mov bx,[session_baud_index]
session_at_d690: shl bx,1
session_at_d692: shl bx,1
session_at_d694: mov ax,[bx+session_baud_table]
session_at_d698: mov dx,[bx+session_baud_table_high]
session_at_d69c: mov [session_rate_low],ax
session_at_d69f: mov [session_rate_high],dx
session_at_d6a3: ret
