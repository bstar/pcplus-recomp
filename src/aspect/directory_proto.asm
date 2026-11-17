; PCPlus2.01 overlay16 D9C8..D9D5, exact13-byte indexed getter.
; The runtime bridge admits stored IDs1..18 before this unchecked body.
BITS 16
CPU 8086
%include "encodings.inc"
%ifdef ASPECT_DIRECTORY_PROTO_FLAT
ORG 0xd9c8
%define aspect_directory_record 0xe650
%define aspect_directory_protocol_table 0x4dd8
%else
SEGMENT _TEXT public class=CODE use16
extern aspect_directory_record
global aspect_directory_builtin_proto
%endif
aspect_directory_builtin_proto:
 mov al,6
 imul byte [aspect_directory_record+72]
 mov_load bx,ax
 mov ax,[bx+aspect_directory_protocol_table]
 ret

%ifndef ASPECT_DIRECTORY_PROTO_FLAT
SEGMENT CONST public class=DATA use16
GROUP DGROUP CONST
global aspect_directory_protocol_table
aspect_directory_protocol_table:
 ; Index0 is reserved and never read. Only the first word in each six-byte
 ; record is consumed; unused original pointer/descriptor fields are absent.
 times 6 db 0
%macro PROTOCOL 1
 dw %1,0,0
%endmacro
 PROTOCOL 5
 PROTOCOL 11
 PROTOCOL 7
 PROTOCOL 17
 PROTOCOL 8
 PROTOCOL 4
 PROTOCOL 13
 PROTOCOL 3
 PROTOCOL 16
 PROTOCOL 12
 PROTOCOL 9
 PROTOCOL 14
 PROTOCOL 6
 PROTOCOL 0
 PROTOCOL 1
 PROTOCOL 2
 PROTOCOL 10
 PROTOCOL 15
%endif
