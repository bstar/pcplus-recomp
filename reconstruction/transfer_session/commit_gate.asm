; Exact native transfer session instructions; analyst regeneration is explicit.
BITS 16
CPU 8086
%ifdef TRANSFER_SESSION_OMF
SEGMENT _TEXT public class=CODE use16
%define short
global session_commit_enter
global session_at_dd02
global session_at_dd04
global session_at_dd06
global session_at_dd07
global session_at_dd0a
global session_at_dd0d
global session_at_dd10
global session_at_dd14
global session_at_dd16
global session_at_dd19
global session_at_dd1c
global session_at_dd1d
global session_at_dd1e
global session_at_dd1f
global session_at_dd23
global session_at_dd27
global session_at_dd2a
global session_at_dd2c
global session_at_dd2e
global session_at_dd30
global session_at_dd32
global session_at_dd35
global session_at_dd39
global session_at_dd3c
global session_at_dd3d
global session_at_dd41
global session_at_dd45
global session_at_dd46
global session_at_dd49
extern session_buffer_used
extern session_commit_buffer
extern session_commit_partial
extern session_commit_unknown_size
extern session_expected_high
extern session_expected_low
extern session_file_handle
extern session_long_remainder
extern session_serial_gate
extern session_serial_gate_set
%else
ORG 0xdcfd
%define session_buffer_used 0xcd34
%define session_commit_buffer 0xddf6
%define session_commit_partial 0xde02
%define session_commit_unknown_size 0xde20
%define session_expected_high 0x9008
%define session_expected_low 0x9006
%define session_file_handle 0xcbaa
%define session_long_remainder 0x9c7c
%define session_serial_gate 0x1d1e
%define session_serial_gate_set 0xabfa
%endif
%include "encodings.inc"
session_commit_enter: cmp word [session_serial_gate],0x0
session_at_dd02: jz short session_at_dd0d
session_at_dd04: sub_load ax,ax
session_at_dd06: push ax
session_at_dd07: call session_serial_gate_set
session_at_dd0a: add sp,0x2
session_at_dd0d: mov ax,[session_expected_high]
session_at_dd10: or ax,[session_expected_low]
session_at_dd14: jnz short session_at_dd19
session_at_dd16: jmp near session_commit_unknown_size
session_at_dd19: mov ax,[0xcb5e]
session_at_dd1c: cwd
session_at_dd1d: push dx
session_at_dd1e: push ax
session_at_dd1f: push word [session_expected_high]
session_at_dd23: push word [session_expected_low]
session_at_dd27: call session_long_remainder
session_at_dd2a: mov_load cx,ax
session_at_dd2c: mov_load bx,dx
session_at_dd2e: or_load dx,ax
session_at_dd30: jnz short session_at_dd35
session_at_dd32: jmp near session_commit_buffer
session_at_dd35: push word [session_file_handle]
session_at_dd39: mov ax,0x1
session_at_dd3c: push ax
session_at_dd3d: sub cx,[0xcb5e]
session_at_dd41: add cx,[session_buffer_used]
session_at_dd45: push cx
session_at_dd46: jmp near session_commit_partial
session_at_dd49: nop
