; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_retry_enter
global session_at_dc23
global session_at_dc25
global session_at_dc28
global session_at_dc2b
global session_at_dc2d
global session_at_dc2f
global session_at_dc32
global session_at_dc33
global session_at_dc36
global session_at_dc37
global session_at_dc3a
global session_at_dc3d
global session_at_dc40
global session_at_dc42
global session_at_dc44
global session_at_dc47
global session_at_dc48
global session_at_dc4b
global session_at_dc4c
global session_at_dc4f
global session_at_dc52
global session_at_dc57
global session_at_dc59
global session_at_dc5c
global session_at_dc5d
global session_at_dc60
global session_at_dc63
global session_at_dc64
global session_at_dc67
extern session_carrier_present
extern session_context
extern session_control_status
extern session_header_checkpoint
extern session_local_cancel
extern session_longjmp
extern session_retry_limit
extern session_streaming_mode
extern session_timed_byte
%else
ORG 0xdc1f
%define session_carrier_present 0x4861
%define session_context 0xcd94
%define session_control_status 0xf050
%define session_header_checkpoint 0xdc6a
%define session_local_cancel 0x3f4b
%define session_longjmp 0x9065
%define session_retry_limit 0xdcf1
%define session_streaming_mode 0xcdcc
%define session_timed_byte 0xaad9
%endif
%include "encodings.inc"
session_retry_enter: cmp word [bp-0x14],0xf
session_at_dc23: jnz short session_at_dc28
session_at_dc25: jmp near session_retry_limit
session_at_dc28: call session_local_cancel
session_at_dc2b: or_load ax,ax
session_at_dc2d: jz short session_at_dc3d
session_at_dc2f: mov ax,0x7
session_at_dc32: push ax
session_at_dc33: mov ax,session_context
session_at_dc36: push ax
session_at_dc37: call session_longjmp
session_at_dc3a: add sp,0x4
session_at_dc3d: call session_carrier_present
session_at_dc40: or_load ax,ax
session_at_dc42: jnz short session_at_dc52
session_at_dc44: mov ax,0xf
session_at_dc47: push ax
session_at_dc48: mov ax,session_context
session_at_dc4b: push ax
session_at_dc4c: call session_longjmp
session_at_dc4f: add sp,0x4
session_at_dc52: cmp word [session_streaming_mode],0x0
session_at_dc57: jz short session_header_checkpoint
session_at_dc59: mov ax,0xa
session_at_dc5c: push ax
session_at_dc5d: call session_timed_byte
session_at_dc60: mov [bp-0x10],ax
session_at_dc63: push ax
session_at_dc64: call session_control_status
session_at_dc67: add sp,0x2
%ifdef TRANSFER_SESSION_OMF
jmp session_header_checkpoint
%endif
