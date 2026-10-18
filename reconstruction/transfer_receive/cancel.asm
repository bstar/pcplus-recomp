; Exact original receiver instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_RECEIVE_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global receive_control_status
global receive_at_f051
global receive_at_f053
global receive_at_f057
global receive_at_f059
global receive_at_f05c
global receive_at_f05f
global receive_at_f061
global receive_at_f064
global receive_at_f065
global receive_at_f068
global receive_at_f069
global receive_at_f06c
global receive_at_f06e
global receive_at_f06f
extern receive_header_byte
extern receive_post_event
extern receive_event_queue
%else
ORG 0xf050
%define receive_header_byte 0x5ca0
%define receive_post_event 0x9065
%define receive_event_queue 0xcd94
%endif
%include "encodings.inc"
receive_control_status: push bp
receive_at_f051: mov_load bp,sp
receive_at_f053: cmp word [bp+0x4],0x18
receive_at_f057: jnz short receive_at_f06c
receive_at_f059: call receive_header_byte
receive_at_f05c: cmp ax,strict word 0x18
receive_at_f05f: jnz short receive_at_f06c
receive_at_f061: mov ax,0x7
receive_at_f064: push ax
receive_at_f065: mov ax,receive_event_queue
receive_at_f068: push ax
receive_at_f069: call receive_post_event
receive_at_f06c: mov_load sp,bp
receive_at_f06e: pop bp
receive_at_f06f: ret
