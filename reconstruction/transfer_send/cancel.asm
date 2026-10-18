; Exact original sender instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SEND_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global send_control_status
global send_at_f051
global send_at_f053
global send_at_f057
global send_at_f059
global send_at_f05c
global send_at_f05f
global send_at_f061
global send_at_f064
global send_at_f065
global send_at_f068
global send_at_f069
global send_at_f06c
global send_at_f06e
global send_at_f06f
extern send_header_byte
extern send_unwind
extern send_checkpoint_buffer
%else
ORG 0xf050
%define send_header_byte 0x5ca0
%define send_unwind 0x9065
%define send_checkpoint_buffer 0xcd94
%endif
%include "encodings.inc"
send_control_status: push bp
send_at_f051: mov_load bp,sp
send_at_f053: cmp word [bp+0x4],0x18
send_at_f057: jnz short send_at_f06c
send_at_f059: call send_header_byte
send_at_f05c: cmp ax,strict word 0x18
send_at_f05f: jnz short send_at_f06c
send_at_f061: mov ax,0x7
send_at_f064: push ax
send_at_f065: mov ax,send_checkpoint_buffer
send_at_f068: push ax
send_at_f069: call send_unwind
send_at_f06c: mov_load sp,bp
send_at_f06e: pop bp
send_at_f06f: ret
